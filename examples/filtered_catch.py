"""
Filtered Catch Example

Shows advanced filtering options for catch events.
Run as Administrator (Windows) or with sudo (Linux/Mac).
"""

from albafish import create_router

print("AlbaFish - Filtered Catch")
print("=" * 50)
print("Demonstrating catch filters")
print("Press Ctrl+C to stop")
print("=" * 50)
print()

router = create_router()


@router.on_catch(fish_only=True)
def only_fish(event):
    """Only fish, no trash items"""
    item_name = router.items_db.get_name(event.item_id)
    print(f"Fish: {item_name}")


@router.on_catch(tier=8)
def tier_8_items(event):
    """Only T8 items"""
    item_name = router.items_db.get_name(event.item_id)
    is_fish = router.items_db.is_fish(event.item_id)
    print(f"T8: {item_name}")


@router.on_catch(tier=[6, 7, 8])
def high_tier_items(event):
    """T6, T7, or T8 items"""
    item_name = router.items_db.get_name(event.item_id)
    tier = router.items_db.get_tier(event.item_id)
    print(f"High tier T{tier}: {item_name}")


@router.on_catch(min_tier=5, max_tier=7, fish_only=True)
def mid_tier_fish(event):
    """T5-T7 fish only"""
    item_name = router.items_db.get_name(event.item_id)
    tier = router.items_db.get_tier(event.item_id)
    print(f"Mid-tier T{tier} fish: {item_name}")


@router.on_catch(item_ids=[142, 143, 144])
def specific_fish(event):
    """Specific fish IDs only"""
    item_name = router.items_db.get_name(event.item_id)
    print(f"Specific fish: {item_name}")


@router.on_bite()
def bite_alert(event):
    """All bites"""
    print("Bite!")


try:
    router.start()
except KeyboardInterrupt:
    print("\n\nStopping...")
    router.stop()
