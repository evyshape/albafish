"""
Basic Fishing Monitor Example

Shows how to monitor all fishing events with simple callbacks.
Run as Administrator (Windows) or with sudo (Linux/Mac).
"""

import albafish

# Create item database
items = albafish.ItemDatabase()

print("AlbaFish - Basic Monitor")
print("=" * 50)
print("Monitoring fishing events...")
print("Press Ctrl+C to stop")
print("=" * 50)
print()


def on_cast(event):
    """Called when rod is cast"""
    print("Cast!")


def on_bite(event):
    """Called when fish bites"""
    print("Bite!")


def on_catch(event):
    """Called when item is caught"""
    item_name = items.get_name(event.item_id)
    tier = items.get_tier(event.item_id)
    is_fish = items.is_fish(event.item_id)
    
    print(f"Caught: {item_name} (T{tier})")


def on_failed(event):
    """Called when fish escapes"""
    print("Fish escaped!")


def on_death(event):
    """Called when player dies"""
    print(f"You died! (Killer ID: {event.object_id})")


# Create monitor with callbacks
monitor = albafish.FishingMonitor(
    on_cast=on_cast,
    on_bite=on_bite,
    on_catch=on_catch,
    on_failed=on_failed,
    on_death=on_death,
    items_db=items,
)

try:
    # Start monitoring (blocks until stopped)
    monitor.start()
except KeyboardInterrupt:
    print("\n\nStopping monitor...")
    monitor.stop()
