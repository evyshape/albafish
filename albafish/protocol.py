import struct
import time
from typing import Optional, Callable, Dict
from dataclasses import dataclass, field


PHOTON_HEADER_LENGTH = 12
COMMAND_HEADER_LENGTH = 12
FRAGMENT_HEADER_LENGTH = 20
MAX_PENDING_SEGMENTS = 64

CMD_DISCONNECT = 4
CMD_SEND_RELIABLE = 6
CMD_SEND_UNRELIABLE = 7
CMD_SEND_FRAGMENT = 8

MSG_REQUEST = 2
MSG_RESPONSE = 3
MSG_EVENT = 4
MSG_RESPONSE_ALT = 7
MSG_ENCRYPTED = 131


@dataclass
class SegmentedPackage:
    total_length: int
    bytes_written: int
    payload: bytearray
    created_at: float
    seen_offsets: set = field(default_factory=set)


@dataclass
class EventData:
    code: int
    parameters: Dict[int, any]


@dataclass
class OperationRequest:
    operation_code: int
    parameters: Dict[int, any]


@dataclass
class OperationResponse:
    operation_code: int
    return_code: int
    debug_message: str
    parameters: Dict[int, any]


class PhotonParser:
    
    def __init__(
        self,
        on_event: Optional[Callable[[EventData], None]] = None,
        on_request: Optional[Callable[[OperationRequest], None]] = None,
        on_response: Optional[Callable[[OperationResponse], None]] = None,
        on_encrypted: Optional[Callable[[], None]] = None,
        on_parse_error: Optional[Callable[[str, int], None]] = None,
    ):
        self.pending_segments: Dict[int, SegmentedPackage] = {}
        self.on_event = on_event
        self.on_request = on_request
        self.on_response = on_response
        self.on_encrypted = on_encrypted
        self.on_parse_error = on_parse_error
    
    def receive_packet(self, payload: bytes) -> bool:
        if len(payload) < PHOTON_HEADER_LENGTH:
            if self.on_parse_error:
                self.on_parse_error("payload shorter than photon header", len(payload))
            return False
        
        offset = 2
        flags = payload[offset]
        offset += 1
        command_count = payload[offset]
        offset += 1
        offset += 8
        
        if flags == 1:
            if self.on_encrypted:
                self.on_encrypted()
            return False
        
        for _ in range(command_count):
            offset, ok = self._handle_command(payload, offset)
            if not ok:
                if self.on_parse_error:
                    self.on_parse_error("handleCommand failed", len(payload))
                return False
        
        return True
    
    def _handle_command(self, src: bytes, offset: int) -> tuple[int, bool]:
        if not self._available(src, offset, COMMAND_HEADER_LENGTH):
            return offset, False
        
        cmd_type = src[offset]
        offset += 4
   
        cmd_len = struct.unpack(">I", src[offset:offset+4])[0]
        offset += 4
        offset += 4
        
        cmd_len -= COMMAND_HEADER_LENGTH
        if cmd_len < 0 or not self._available(src, offset, cmd_len):
            return offset, False
        
        if cmd_type == CMD_DISCONNECT:
            return offset + cmd_len, True
        
        elif cmd_type == CMD_SEND_UNRELIABLE:
            if cmd_len < 4:
                return offset + cmd_len, False
            offset += 4
            cmd_len -= 4
            return self._handle_send_reliable(src, offset, cmd_len), True
        
        elif cmd_type == CMD_SEND_RELIABLE:
            return self._handle_send_reliable(src, offset, cmd_len), True
        
        elif cmd_type == CMD_SEND_FRAGMENT:
            return self._handle_send_fragment(src, offset, cmd_len), True
        
        else:
            return offset + cmd_len, True
    
    def _handle_send_reliable(self, src: bytes, offset: int, cmd_len: int) -> int:
        if cmd_len < 2 or not self._available(src, offset, cmd_len):
            return offset + cmd_len
        
        offset += 1
        msg_type = src[offset]
        offset += 1
        cmd_len -= 2
        
        if not self._available(src, offset, cmd_len):
            return offset + cmd_len
        
        if msg_type == MSG_ENCRYPTED:
            if self.on_encrypted:
                self.on_encrypted()
            return offset + cmd_len
        
        data = src[offset:offset+cmd_len]
        offset += cmd_len
        
        if msg_type == MSG_REQUEST:
            req = deserialize_request(data)
            if req and self.on_request:
                self.on_request(req)
        
        elif msg_type in (MSG_RESPONSE, MSG_RESPONSE_ALT):
            resp = deserialize_response(data)
            if resp and self.on_response:
                self.on_response(resp)
        
        elif msg_type == MSG_EVENT:
            event = deserialize_event(data)
            if event and self.on_event:
                self.on_event(event)
        
        return offset
    
    def _handle_send_fragment(self, src: bytes, offset: int, cmd_len: int) -> int:
        if cmd_len < FRAGMENT_HEADER_LENGTH or not self._available(src, offset, FRAGMENT_HEADER_LENGTH):
            return offset + cmd_len
        
        start_seq = struct.unpack(">I", src[offset:offset+4])[0]
        offset += 4
        cmd_len -= 4
        
        offset += 4
        cmd_len -= 4
        
        offset += 4
        cmd_len -= 4
        
        total_len = struct.unpack(">I", src[offset:offset+4])[0]
        offset += 4
        cmd_len -= 4
        
        frag_offset = struct.unpack(">I", src[offset:offset+4])[0]
        offset += 4
        cmd_len -= 4
        
        frag_len = cmd_len
        if frag_len < 0 or not self._available(src, offset, frag_len) or total_len < 0 or total_len > 65536 * 16:
            return offset + frag_len
        
        seg = self.pending_segments.get(start_seq)
        if not seg:
            self._evict_if_full()
            seg = SegmentedPackage(
                total_length=total_len,
                bytes_written=0,
                payload=bytearray(total_len),
                created_at=time.time(),
                seen_offsets=set()
            )
            self.pending_segments[start_seq] = seg
        
        end = frag_offset + frag_len
        if frag_offset not in seg.seen_offsets and frag_offset >= 0 and end <= len(seg.payload):
            seg.payload[frag_offset:end] = src[offset:offset+frag_len]
            seg.bytes_written += frag_len
            seg.seen_offsets.add(frag_offset)
        
        offset += frag_len
        
        if seg.bytes_written >= seg.total_length:
            del self.pending_segments[start_seq]
            self._handle_send_reliable(bytes(seg.payload), 0, len(seg.payload))
        
        return offset
    
    def _evict_if_full(self):
        if len(self.pending_segments) < MAX_PENDING_SEGMENTS:
            return
        
        oldest_key = None
        oldest_time = None
        
        for key, seg in self.pending_segments.items():
            if oldest_time is None or seg.created_at < oldest_time:
                oldest_key = key
                oldest_time = seg.created_at
        
        if oldest_key is not None:
            del self.pending_segments[oldest_key]
    
    @staticmethod
    def _available(src: bytes, offset: int, count: int) -> bool:
        return count >= 0 and offset >= 0 and len(src) - offset >= count

TYPE_UNKNOWN = 0
TYPE_BOOLEAN = 2
TYPE_BYTE = 3
TYPE_SHORT = 4
TYPE_FLOAT = 5
TYPE_DOUBLE = 6
TYPE_STRING = 7
TYPE_NULL = 8
TYPE_COMPRESSED_INT = 9
TYPE_COMPRESSED_LONG = 10
TYPE_INT1 = 11
TYPE_INT1_NEG = 12
TYPE_INT2 = 13
TYPE_INT2_NEG = 14
TYPE_LONG1 = 15
TYPE_LONG1_NEG = 16
TYPE_LONG2 = 17
TYPE_LONG2_NEG = 18
TYPE_CUSTOM = 19
TYPE_DICTIONARY = 20
TYPE_HASHTABLE = 21
TYPE_OBJECT_ARRAY = 23
TYPE_OPERATION_REQUEST = 24
TYPE_OPERATION_RESP = 25
TYPE_EVENT_DATA = 26
TYPE_BOOL_FALSE = 27
TYPE_BOOL_TRUE = 28
TYPE_SHORT_ZERO = 29
TYPE_INT_ZERO = 30
TYPE_LONG_ZERO = 31
TYPE_FLOAT_ZERO = 32
TYPE_DOUBLE_ZERO = 33
TYPE_BYTE_ZERO = 34
TYPE_ARRAY = 0x40
CUSTOM_TYPE_SLIM_BASE = 0x80
MAX_ARRAY_SIZE = 65536


class Buffer:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
    
    def read_byte(self) -> int:
        if self.pos >= len(self.data):
            return 0
        b = self.data[self.pos]
        self.pos += 1
        return b
    
    def read(self, n: int) -> bytes:
        if self.pos + n > len(self.data):
            n = len(self.data) - self.pos
        result = self.data[self.pos:self.pos+n]
        self.pos += n
        return result
    
    def remaining(self) -> int:
        return len(self.data) - self.pos


def read_compressed_uint32(buf: Buffer) -> int:
    value = 0
    shift = 0
    
    while True:
        b = buf.read_byte()
        if b == 0 and buf.pos > len(buf.data):
            return 0
        
        value |= (b & 0x7F) << shift
        
        if (b & 0x80) == 0:
            return value
        
        shift += 7
        if shift >= 35:
            return 0


def read_compressed_int32(buf: Buffer) -> int:
    v = read_compressed_uint32(buf)
    return (v >> 1) ^ (-(v & 1))


def read_compressed_int64(buf: Buffer) -> int:
    value = 0
    shift = 0
    
    while True:
        b = buf.read_byte()
        if b == 0 and buf.pos > len(buf.data):
            return 0
        
        value |= (b & 0x7F) << shift
        
        if (b & 0x80) == 0:
            break
        
        shift += 7
        if shift >= 70:
            return 0
    
    return (value >> 1) ^ (-(value & 1))


def read_int16(buf: Buffer) -> int:
    b = buf.read(2)
    if len(b) < 2:
        return 0
    return struct.unpack("<h", b)[0]


def read_uint16(buf: Buffer) -> int:
    b = buf.read(2)
    if len(b) < 2:
        return 0
    return struct.unpack("<H", b)[0]


def read_float32(buf: Buffer) -> float:
    b = buf.read(4)
    if len(b) < 4:
        return 0.0
    return struct.unpack("<f", b)[0]


def read_float64(buf: Buffer) -> float:
    b = buf.read(8)
    if len(b) < 8:
        return 0.0
    return struct.unpack("<d", b)[0]


def read_string(buf: Buffer) -> str:
    length = read_compressed_uint32(buf)
    if length <= 0 or length > buf.remaining():
        return ""
    b = buf.read(length)
    return b.decode("utf-8", errors="replace")


def read_count(buf: Buffer) -> int:
    return read_compressed_uint32(buf)


def deserialize(buf: Buffer, tc: int) -> any:
    if tc >= CUSTOM_TYPE_SLIM_BASE:
        return deserialize_custom(buf, tc)
    
    if tc == TYPE_UNKNOWN or tc == TYPE_NULL:
        return None
    elif tc == TYPE_BOOLEAN:
        return buf.read_byte() != 0
    elif tc == TYPE_BYTE:
        return buf.read_byte()
    elif tc == TYPE_SHORT:
        return read_int16(buf)
    elif tc == TYPE_FLOAT:
        return read_float32(buf)
    elif tc == TYPE_DOUBLE:
        return read_float64(buf)
    elif tc == TYPE_STRING:
        return read_string(buf)
    elif tc == TYPE_COMPRESSED_INT:
        return read_compressed_int32(buf)
    elif tc == TYPE_COMPRESSED_LONG:
        return read_compressed_int64(buf)
    elif tc == TYPE_INT1:
        return int(buf.read_byte())
    elif tc == TYPE_INT1_NEG:
        return -int(buf.read_byte())
    elif tc == TYPE_INT2:
        return int(read_uint16(buf))
    elif tc == TYPE_INT2_NEG:
        return -int(read_uint16(buf))
    elif tc == TYPE_LONG1:
        return int(buf.read_byte())
    elif tc == TYPE_LONG1_NEG:
        return -int(buf.read_byte())
    elif tc == TYPE_LONG2:
        return int(read_uint16(buf))
    elif tc == TYPE_LONG2_NEG:
        return -int(read_uint16(buf))
    elif tc == TYPE_CUSTOM:
        return deserialize_custom(buf, 0)
    elif tc == TYPE_DICTIONARY:
        return deserialize_dictionary(buf)
    elif tc == TYPE_HASHTABLE:
        return deserialize_hashtable(buf)
    elif tc == TYPE_OBJECT_ARRAY:
        return deserialize_object_array(buf)
    elif tc == TYPE_OPERATION_REQUEST:
        return deserialize_operation_request_inner(buf)
    elif tc == TYPE_OPERATION_RESP:
        return deserialize_operation_response_inner(buf)
    elif tc == TYPE_EVENT_DATA:
        return deserialize_event_data_inner(buf)
    elif tc == TYPE_BOOL_FALSE:
        return False
    elif tc == TYPE_BOOL_TRUE:
        return True
    elif tc == TYPE_SHORT_ZERO:
        return 0
    elif tc == TYPE_INT_ZERO:
        return 0
    elif tc == TYPE_LONG_ZERO:
        return 0
    elif tc == TYPE_FLOAT_ZERO:
        return 0.0
    elif tc == TYPE_DOUBLE_ZERO:
        return 0.0
    elif tc == TYPE_BYTE_ZERO:
        return 0
    elif tc == 0x79:
        return deserialize_nested_array(buf)
    elif tc & TYPE_ARRAY:
        return deserialize_typed_array(buf, tc & ~TYPE_ARRAY)
    else:
        return None


def deserialize_custom(buf: Buffer, gp_type: int) -> bytes:
    if gp_type < CUSTOM_TYPE_SLIM_BASE:
        buf.read_byte()
    
    size = read_count(buf)
    if size < 0 or size > buf.remaining() or size > MAX_ARRAY_SIZE:
        return b""
    
    return buf.read(size)


def deserialize_dictionary(buf: Buffer) -> dict:
    key_tc = buf.read_byte()
    val_tc = buf.read_byte()
    count = read_count(buf)
    
    if count < 0 or count > MAX_ARRAY_SIZE or count > buf.remaining():
        return {}
    
    result = {}
    for i in range(count):
        if buf.remaining() <= 0:
            break
        
        kt = key_tc if key_tc != 0 else buf.read_byte()
        vt = val_tc if val_tc != 0 else buf.read_byte()
        
        key = deserialize(buf, kt)
        val = deserialize(buf, vt)
        
        if isinstance(key, (int, str, float, bool, type(None), bytes)):
            result[key] = val
        else:
            result[f"UNHASHABLE_{i}_{type(key).__name__}"] = val
    
    return result


def deserialize_hashtable(buf: Buffer) -> dict:
    return deserialize_dictionary(buf)


def deserialize_object_array(buf: Buffer) -> list:
    size = read_count(buf)
    if size < 0 or size > MAX_ARRAY_SIZE or size > buf.remaining():
        return []
    
    result = []
    for _ in range(size):
        tc = buf.read_byte()
        result.append(deserialize(buf, tc))
    
    return result


def deserialize_nested_array(buf: Buffer) -> list:
    size = read_count(buf)
    if size < 0 or size > MAX_ARRAY_SIZE or size > buf.remaining():
        return []
    
    tc = buf.read_byte()
    result = []
    for _ in range(size):
        result.append(deserialize(buf, tc))
    
    return result


def deserialize_typed_array(buf: Buffer, elem_type: int) -> any:
    size = read_count(buf)
    if size < 0 or size > MAX_ARRAY_SIZE:
        return []
    
    if elem_type == TYPE_BOOLEAN:
        result = []
        packed_bytes = (size + 7) // 8
        packed = buf.read(packed_bytes)
        for i in range(size):
            result.append((packed[i // 8] & (1 << (i % 8))) != 0)
        return result
    
    elif elem_type == TYPE_BYTE:
        return buf.read(size)
    
    elif elem_type == TYPE_SHORT:
        return [read_int16(buf) for _ in range(size)]
    
    elif elem_type == TYPE_FLOAT:
        return [read_float32(buf) for _ in range(size)]
    
    elif elem_type == TYPE_DOUBLE:
        return [read_float64(buf) for _ in range(size)]
    
    elif elem_type == TYPE_STRING:
        return [read_string(buf) for _ in range(size)]
    
    elif elem_type == TYPE_COMPRESSED_INT:
        return [read_compressed_int32(buf) for _ in range(size)]
    
    elif elem_type == TYPE_COMPRESSED_LONG:
        return [read_compressed_int64(buf) for _ in range(size)]
    
    elif elem_type == TYPE_DICTIONARY:
        return [deserialize_dictionary(buf) for _ in range(size)]
    
    elif elem_type == TYPE_HASHTABLE:
        return [deserialize_hashtable(buf) for _ in range(size)]
    
    elif elem_type == TYPE_CUSTOM:
        buf.read_byte()
        result = []
        for _ in range(size):
            elem_size = read_count(buf)
            if elem_size < 0 or elem_size > buf.remaining() or elem_size > MAX_ARRAY_SIZE:
                break
            result.append(buf.read(elem_size))
        return result
    
    else:
        return [deserialize(buf, elem_type) for _ in range(size)]


def read_parameter_table(buf: Buffer) -> Dict[int, any]:
    count = read_count(buf)
    if count < 0 or count > MAX_ARRAY_SIZE or count > buf.remaining():
        return {}
    
    params = {}
    for _ in range(count):
        if buf.remaining() <= 0:
            break
        
        key = buf.read_byte()
        tc = buf.read_byte()
        value = deserialize(buf, tc)
        params[key] = value
    
    return params


def deserialize_event_data_inner(buf: Buffer) -> dict:
    code = buf.read_byte()
    params = read_parameter_table(buf)
    return {"code": code, "parameters": params}


def deserialize_operation_request_inner(buf: Buffer) -> dict:
    op_code = buf.read_byte()
    params = read_parameter_table(buf)
    return {"operationCode": op_code, "parameters": params}


def deserialize_operation_response_inner(buf: Buffer) -> dict:
    if buf.remaining() < 3:
        return None
    
    op_code = buf.read_byte()
    return_code = read_int16(buf)
    
    debug_msg = ""
    if buf.remaining() > 0:
        tc = buf.read_byte()
        val = deserialize(buf, tc)
        if isinstance(val, str):
            debug_msg = val
    
    params = read_parameter_table(buf)
    
    return {
        "operationCode": op_code,
        "returnCode": return_code,
        "debugMessage": debug_msg,
        "parameters": params
    }


def deserialize_event(data: bytes) -> Optional[EventData]:
    if len(data) < 1:
        return None
    
    buf = Buffer(data)
    code = buf.read_byte()
    params = read_parameter_table(buf)
    
    return EventData(code=code, parameters=params)


def deserialize_request(data: bytes) -> Optional[OperationRequest]:
    if len(data) < 1:
        return None
    
    buf = Buffer(data)
    op_code = buf.read_byte()
    params = read_parameter_table(buf)
    
    return OperationRequest(operation_code=op_code, parameters=params)


def deserialize_response(data: bytes) -> Optional[OperationResponse]:
    if len(data) < 3:
        return None
    
    buf = Buffer(data)
    op_code = buf.read_byte()
    return_code = read_int16(buf)
    
    debug_msg = ""
    market_orders = None
    
    if buf.remaining() > 0:
        tc = buf.read_byte()
        val = deserialize(buf, tc)
        if isinstance(val, str):
            debug_msg = val
        elif isinstance(val, list) and all(isinstance(x, str) for x in val):
            market_orders = val
    
    params = read_parameter_table(buf)
    
    if market_orders is not None:
        params[0] = market_orders
    
    return OperationResponse(
        operation_code=op_code,
        return_code=return_code,
        debug_message=debug_msg,
        parameters=params
    )
