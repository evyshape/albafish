"""
Fishing monitor - основной модуль для мониторинга рыбалки
"""

import logging
import sys
import threading
from typing import Callable, Optional
from datetime import datetime

from .protocol import PhotonParser, EventData, OperationRequest
from .items import ItemDatabase
from .events import FishingEvent, EventBus, CallbackEventHandler
from .constants import (
    EventCode,
    OperationCode,
    EventType,
    EVENT_TYPE_NAMES,
    RequestParameter,
    FishingAction,
    FishingEventType,
)
from .exceptions import (
    PacketParseError,
    InvalidPortError,
    PermissionError,
    DependencyError,
)


logger = logging.getLogger(__name__)


class FishingMonitor:
    """
    Монитор событий рыбалки

    Поддерживает middleware, множественные обработчики и фильтрацию.
    """
    
    def __init__(
        self,
        on_cast: Optional[Callable[[FishingEvent], None]] = None,
        on_cast_end: Optional[Callable[[FishingEvent], None]] = None,
        on_float: Optional[Callable[[FishingEvent], None]] = None,
        on_bite: Optional[Callable[[FishingEvent], None]] = None,
        on_start_pull: Optional[Callable[[FishingEvent], None]] = None,
        on_pulling: Optional[Callable[[FishingEvent], None]] = None,
        on_stop_pull: Optional[Callable[[FishingEvent], None]] = None,
        on_catch: Optional[Callable[[FishingEvent], None]] = None,
        on_fishing_catch: Optional[Callable[[FishingEvent], None]] = None,
        on_failed: Optional[Callable[[FishingEvent], None]] = None,
        on_cancel: Optional[Callable[[FishingEvent], None]] = None,
        on_death: Optional[Callable[[FishingEvent], None]] = None,
        items_db: Optional[ItemDatabase] = None,
        event_bus: Optional[EventBus] = None,
        player_id: Optional[int] = None,
        auto_detect_player: bool = True,
    ):
        """
        
        Args:
            on_cast: Callback для события заброса удочки (начало)
            on_cast_end: Callback для конца заброса (поплавок упал)
            on_float: Callback для события появления/обновления поплавка
            on_bite: Callback для события клева
            on_start_pull: Callback для начала вытягивания рыбы
            on_pulling: Callback для процесса вытягивания
            on_stop_pull: Callback для остановки вытягивания
            on_catch: Callback для события поимки предмета
            on_fishing_catch: Callback для улова в процессе рыбалки
            on_failed: Callback для срыва рыбы (передернул/недодернул)
            on_cancel: Callback для события отмены заброса
            on_death: Callback для события смерти
            items_db: База данных предметов
            event_bus: Event bus (создается автоматически если не передан)
            player_id: ID игрока для фильтрации (None = автоопределение по первому челику)
            auto_detect_player: Автоматически определять player_id при первом событии
        """
        self.items_db = items_db or ItemDatabase()
        self.event_bus = event_bus or EventBus()
        
        self._player_id: Optional[int] = player_id
        self._auto_detect_player = auto_detect_player
        self._player_id_locked = player_id is not None
        self._running = False
        self._stop_event = threading.Event()

        callbacks = {
            "cast": on_cast,
            "cast_end": on_cast_end,
            "float": on_float,
            "bite": on_bite,
            "start_pull": on_start_pull,
            "pulling": on_pulling,
            "stop_pull": on_stop_pull,
            "catch": on_catch,
            "fishing_catch": on_fishing_catch,
            "failed": on_failed,
            "cancel": on_cancel,
            "death": on_death,
        }
        
        for event_type, callback in callbacks.items():
            if callback:
                self.event_bus.register_handler(
                    CallbackEventHandler(callback, event_type)
                )

        self._parser = PhotonParser(
            on_event=self._handle_event,
            on_request=self._handle_request,
        )
        
        logger.info("FishingMonitor инициализирован")
    
    @property
    def player_id(self) -> Optional[int]:
        return self._player_id
    
    def set_player_id(self, player_id: int) -> None:
        """
        Установить player_id вручную
        
        Args:
            player_id: ID игрока для фильтрации событий
        """
        self._player_id = player_id
        self._player_id_locked = True
        logger.info(f"Player ID установлен вручную: {player_id}")
    
    def _create_event(
        self,
        event_type: EventType,
        player_id: Optional[int] = None,
        item_id: Optional[int] = None,
        param2: Optional[int] = None,
        object_id: Optional[int] = None,
    ) -> FishingEvent:
        return FishingEvent(
            timestamp=datetime.now(),
            event_type=EVENT_TYPE_NAMES[event_type],
            player_id=player_id,
            item_id=item_id,
            param2=param2,
            object_id=object_id,
        )
    
    def _emit_event(self, event: FishingEvent) -> None:
        self.event_bus.emit(event)
    
    def _handle_event(self, event: EventData) -> None:
        if 252 not in event.parameters:
            event.parameters[252] = event.code
        
        event_code = event.parameters.get(252)
        
        try:
            if event_code == EventCode.NEW_SIMPLE_ITEM:
                self._handle_catch_event(event)
            elif event_code == EventCode.FISHING_EVENT:
                self._handle_fishing_event(event)
            elif event_code == EventCode.NEW_FLOAT_OBJECT:
                self._handle_float_event(event)
            elif event_code == EventCode.KNOCKED_DOWN:
                self._handle_death_event(event)
        except Exception as e:
            logger.exception(f"Error handling event {event_code}: {e}")
    
    def _handle_fishing_event(self, event: EventData) -> None:
        fishing_type = event.parameters.get(3)
        player_id = event.parameters.get(0)
        
        if fishing_type is None or player_id is None:
            return

        if self._player_id is None and self._auto_detect_player:
            self._player_id = player_id

        if self._player_id is not None and player_id != self._player_id:
            return

        event_map = {
            FishingEventType.CAST: EventType.CAST,
            FishingEventType.CAST_END: EventType.CAST_END,
            FishingEventType.BITE: EventType.BITE,
            FishingEventType.STOP_PULL: EventType.PULLING,
            FishingEventType.PULLING: EventType.STOP_PULL,
            FishingEventType.CATCH: EventType.FISHING_CATCH,
            FishingEventType.FAILED: EventType.FAILED,
            FishingEventType.CANCEL: EventType.CANCEL,
        }
        
        event_type = event_map.get(fishing_type)
        if event_type:
            fishing_event = self._create_event(event_type, player_id=player_id)
            self._emit_event(fishing_event)
    
    def _handle_catch_event(self, event: EventData) -> None:
        item_id = event.parameters.get(1)
        param2 = event.parameters.get(2)
        object_id = event.parameters.get(0)
        
        fishing_event = self._create_event(
            EventType.CATCH,
            item_id=item_id,
            param2=param2,
            object_id=object_id,
        )
        
        logger.debug(f"Catch event: item_id={item_id}, param2={param2}")
        self._emit_event(fishing_event)
    
    def _handle_float_event(self, event: EventData) -> None:
        player_id = event.parameters.get(3)
        
        if player_id is None:
            return

        if self._player_id is not None and player_id != self._player_id:
            logger.debug(f"Пропущено событие другого игрока: {player_id}")
            return
        
        fishing_event = self._create_event(
            EventType.FLOAT,
            player_id=player_id,
        )
        
        logger.debug(f"Float event: player_id={player_id}")
        self._emit_event(fishing_event)
    

    
    def _handle_death_event(self, event: EventData) -> None:
        player_id = event.parameters.get(0)
        killer_id = event.parameters.get(1)
        
        if player_id is None:
            return

        if self._player_id is not None and player_id != self._player_id:
            return
        
        fishing_event = self._create_event(
            EventType.DEATH,
            player_id=player_id,
            object_id=killer_id,
        )
        self._emit_event(fishing_event)
    
    def _handle_request(self, request: OperationRequest) -> None:
        if request.operation_code != OperationCode.GENERIC_ACTION:
            return
        
        params = request.parameters
        action_type = params.get(RequestParameter.ACTION_TYPE)

        if action_type == FishingAction.START_PULL:
            fishing_event = self._create_event(EventType.START_PULL)
            logger.debug("Start pull event")
            self._emit_event(fishing_event)
        elif action_type == FishingAction.CAST_ROD:
            logger.debug("Cast ROD request (final)")
        elif action_type == FishingAction.CANCEL_ROD:
            logger.debug("Cancel ROD request")
    
    def _packet_handler(self, packet) -> None:
        try:
            from scapy.all import UDP
        except ImportError:
            return
        
        if UDP not in packet:
            return
        
        payload = bytes(packet[UDP].payload)
        if len(payload) == 0:
            return
        
        try:
            self._parser.receive_packet(payload)
        except Exception as e:
            logger.debug(f"Packet parse error: {e}")
    
    def _validate_port(self, port: int) -> None:
        if not isinstance(port, int):
            raise InvalidPortError(f"Port must be an integer, got {type(port).__name__}")
        
        if port < 1 or port > 65535:
            raise InvalidPortError(f"Port must be between 1 and 65535, got {port}")
    
    def _check_dependencies(self) -> None:
        try:
            import scapy.all
        except ImportError as e:
            raise DependencyError(
                "scapy is not installed. Install it with: pip install scapy"
            ) from e

        if sys.platform == "win32":
            try:
                from scapy.all import conf
                if not hasattr(conf, 'use_pcap') or conf.use_pcap is False:
                    raise DependencyError(
                        "Npcap is not installed or not detected.\n"
                        "Download and install from: https://npcap.com/#download\n"
                        "Make sure to check 'Install Npcap in WinPcap API-compatible Mode' during installation."
                    )
            except DependencyError:
                raise
            except Exception as e:
                logger.warning(f"Could not verify npcap installation: {e}")
        else:
            try:
                from scapy.all import conf
                if not conf.L3socket:
                    raise DependencyError(
                        "libpcap is not installed.\n"
                        "Install it with:\n"
                        "  Ubuntu/Debian: sudo apt-get install libpcap-dev\n"
                        "  RedHat/CentOS: sudo yum install libpcap-devel\n"
                        "  macOS: brew install libpcap"
                    )
            except DependencyError:
                raise
            except Exception as e:
                logger.warning(f"Could not verify libpcap installation: {e}")
    
    def _check_permissions(self) -> None:
        import os
        
        if sys.platform == "win32":
            try:
                import ctypes
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    logger.warning(
                        "Not running as Administrator. Packet capture may fail. "
                        "Try running your script as Administrator."
                    )
            except Exception:
                pass
        else:
            if os.geteuid() != 0:
                logger.warning(
                    "Not running as root. Packet capture may fail. "
                    "Try running with sudo or as root user."
                )
    
    def start(self, port: int = 5056, interface: Optional[str] = None) -> None:
        self._validate_port(port)
        self._check_dependencies()
        self._check_permissions()
        
        if self._running:
            return
        
        self._running = True
        self._stop_event.clear()
        
        logger.info(f"Starting packet capture on port {port}" + 
                   (f" (interface: {interface})" if interface else " (all interfaces)"))
        
        try:
            from scapy.all import sniff
            
            sniff_kwargs = {
                "filter": f"udp port {port}",
                "prn": self._packet_handler,
                "store": False,
                "stop_filter": lambda _: self._stop_event.is_set(),
            }
            
            if interface:
                sniff_kwargs["iface"] = interface
            
            sniff(**sniff_kwargs)
            
        except KeyboardInterrupt:
            logger.info("Stopped by user")
        except OSError as e:
            error_msg = str(e).lower()
            if "operation not permitted" in error_msg or "access is denied" in error_msg:
                raise PermissionError(
                    "Permission denied. Run as Administrator (Windows) or with sudo (Linux/Mac)."
                ) from e
            elif "no such device" in error_msg or "device not found" in error_msg:
                raise DependencyError(
                    f"Network interface not found: {interface}\n"
                    f"Use monitor.list_interfaces() to see available interfaces."
                ) from e
            raise
        except Exception as e:
            logger.exception(f"Error during packet capture: {e}")
            raise
        finally:
            self._running = False
    
    @staticmethod
    def list_interfaces() -> list:
        try:
            from scapy.all import get_if_list
            interfaces = get_if_list()
            return interfaces
        except Exception as e:
            logger.error(f"Failed to list interfaces: {e}")
            return []
    
    def stop(self) -> None:
        if not self._running:
            logger.warning("FishingMonitor is not running")
            return
        
        logger.info("Stopping packet capture...")
        self._stop_event.set()
        self._running = False
    
    @property
    def is_running(self) -> bool:
        return self._running
