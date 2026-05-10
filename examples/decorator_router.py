"""
Decorator Router Example

Shows how to use decorators for event handling with filters.
Run as Administrator (Windows) or with sudo (Linux/Mac).
"""

from albafish import create_router

print("AlbaFish - Decorator Router")
print("=" * 50)
print("Using decorators for event handling")
print("Press Ctrl+C to stop")
print("=" * 50)
print()

# Create router
router = create_router()


@router.on_cast()
def handle_cast(event):
    """Handle all casts"""
    print("Rod cast!")


@router.on_bite()
def handle_bite(event):
    """Handle all bites"""
    print("Fish is biting!")


@router.on_catch()
def handle_any_catch(event):
    """Handle all catches"""
    item_name = router.items_db.get_name(event.item_id)
    print(f"Caught: {item_name}")


@router.on_catch(tier=8, fish_only=True)
def handle_rare_fish(event):
    """Handle only T8 fish"""
    item_name = router.items_db.get_name(event.item_id)
    print(f"T8 FISH: {item_name}")


@router.on_catch(min_tier=6, fish_only=True)
def handle_valuable_fish(event):
    """Handle T6+ fish"""
    item_name = router.items_db.get_name(event.item_id)
    tier = router.items_db.get_tier(event.item_id)
    print(f"Valuable T{tier} fish: {item_name}")


@router.on_failed()
def handle_failed(event):
    """Handle fish escapes"""
    print("Fish escaped!")


@router.on_death()
def handle_death(event):
    """Handle player death"""
    print(f"You died! Killer: {event.object_id}")


try:
    # Start router (blocks until stopped)
    router.start()
except KeyboardInterrupt:
    print("\n\nStopping router...")
    router.stop()
