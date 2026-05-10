# 🎣 AlbaFish

**Educational toolkit for analyzing Albion Online fishing mechanics through network packet analysis**

> ⚠️ **FOR EDUCATIONAL PURPOSES ONLY** =)  
> This library is designed for learning about network protocols, packet analysis, and game mechanics research.  
> **NOT intended for creating game bots or automation tools.**

## 📚 What is this?

AlbaFish is a Python library that captures and parses Albion Online network packets to understand fishing mechanics. It's built for:

- 🎓 **Learning** about Photon protocol and packet analysis
- 🔬 **Research** into game networking and event systems
- 📊 **Understanding** MMO client-server communication

## ✨ Features

- 🎯 Real-time fishing event monitoring (cast, bite, catch, etc.)
- 🐟 Complete Albion Online item database (11,000+ items)
- ⚡ Both sync and async API support
- 🎨 Decorator-based event routing
- 🔧 Middleware system for event processing
- 📦 Type hints and comprehensive error handling

## 🚀 Quick Start

### Installation

```bash
pip install albafish
```

**Requirements:**
- Python 3.7+
- `scapy>=2.5.0` (installed automatically)
- Administrator/root privileges (for packet capture)
- Windows: [Npcap](https://npcap.com/#download)
- Linux: `libpcap-dev`
- macOS: `libpcap` (usually pre-installed)

### Basic Example

```python
import albafish

# Create item database
items = albafish.ItemDatabase()

# Simple callback
def on_catch(event):
    fish_name = items.get_name(event.item_id)
    print(f"🎣 Caught: {fish_name}")

# Create monitor
monitor = albafish.FishingMonitor(on_catch=on_catch, items_db=items)

# Start monitoring (requires admin/root)
monitor.start()
```

### Decorator Style

```python
from albafish import create_router

router = create_router()

@router.on_catch(tier=8, fish_only=True)
def rare_fish(event):
    print("🐟 Rare T8 fish!")

@router.on_bite()
def bite_alert(event):
    print("🎣 Fish is biting!")

router.start()
```

### Async Support

```python
import asyncio
from albafish import create_async_router

router = create_async_router()

@router.on_catch()
async def handle_catch(event):
    print(f"Caught item: {event.item_id}")
    await asyncio.sleep(0.1)  # async operations

asyncio.run(router.start())
```

## 📖 Documentation

### Events

- `on_cast` - Rod cast started
- `on_cast_end` - Float landed in water
- `on_bite` - Fish is biting
- `on_start_pull` - Started pulling
- `on_pulling` - Pulling in progress
- `on_catch` - Item caught
- `on_failed` - Fish escaped
- `on_death` - Player died

### Filtering

```python
# Catch only T7+ fish
@router.on_catch(min_tier=7, fish_only=True)
def rare_fish(event):
    pass

# Specific tiers
@router.on_catch(tier=[6, 7, 8])
def high_tier(event):
    pass

# Specific items
@router.on_catch(item_ids=[142, 143, 144])
def specific_items(event):
    pass
```

## 🛠️ Advanced Usage

### Custom Event Bus

```python
from albafish import FishingMonitor, EventBus, LoggingMiddleware

bus = EventBus()
bus.add_middleware(LoggingMiddleware())

monitor = FishingMonitor(event_bus=bus)
```

### Player Filtering

```python
# Auto-detect player (default)
monitor = FishingMonitor(auto_detect_player=True)

# Specific player ID
monitor = FishingMonitor(player_id=12345)
```

## 📋 Examples

Check the `/examples` folder for more:
- `basic_monitor.py` - Simple event monitoring
- `decorator_router.py` - Decorator-based routing
- `async_example.py` - Async/await usage
- `filtered_catch.py` - Advanced filtering

## ⚠️ Important Notes

1. **Requires elevated privileges** - Run as Administrator (Windows) or with `sudo` (Linux/Mac)
2. **Educational use only** - Not for game automation or botting
3. **Network capture** - Monitors UDP port 5056 by default
4. **Privacy** - Only captures game packets, no personal data

## 🤝 Contributing

This is an educational project. Feel free to:
- Report bugs
- Suggest improvements
- Share your learning experiences

**Not accepted:**
- Features for game automation
- Bot-related functionality
- Commercial use requests

## 📜 License

Non-Commercial License - Free for educational and research purposes only.  
See [LICENSE](https://github.com/evyshape/albafish/blob/main/LICENSE) for details.

## 👤 Author

**evyshape**

---

**Disclaimer:** This tool is for educational purposes. The author is not responsible for any misuse.  
Albion Online is a trademark of Sandbox Interactive GmbH.

=)
