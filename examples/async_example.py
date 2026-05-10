"""
Async Router Example

Shows how to use async/await with fishing events.
Run as Administrator (Windows) or with sudo (Linux/Mac).
"""

import asyncio
from albafish import create_async_router

print("AlbaFish - Async Example")
print("=" * 50)
print("Using async/await for event handling")
print("Press Ctrl+C to stop")
print("=" * 50)
print()

# Create async router
router = create_async_router()


@router.on_cast()
async def handle_cast(event):
    """Async cast handler"""
    print("Rod cast!")
    await asyncio.sleep(0.1)  # Simulate async operation


@router.on_bite()
async def handle_bite(event):
    """Async bite handler"""
    print("Fish is biting!")
    await asyncio.sleep(0.05)


@router.on_catch()
async def handle_catch(event):
    """Async catch handler"""
    item_name = router.items_db.get_name(event.item_id)
    tier = router.items_db.get_tier(event.item_id)
    is_fish = router.items_db.is_fish(event.item_id)
    
    print(f"Caught: {item_name} (T{tier})")
    
    # Simulate async database save
    await save_to_database(event)


@router.on_catch(tier=8, fish_only=True)
async def handle_rare_fish(event):
    """Handle rare fish with async notification"""
    item_name = router.items_db.get_name(event.item_id)
    print(f"T8 FISH: {item_name}")
    
    # Could send async notification
    await send_notification(f"Caught rare fish: {item_name}")


@router.on_death()
async def handle_death(event):
    """Async death handler"""
    print(f"You died! Killer: {event.object_id}")
    await asyncio.sleep(0.1)


async def save_to_database(event):
    """Simulate async database operation"""
    await asyncio.sleep(0.01)
    print(f"  Saved to database")


async def send_notification(message):
    """Simulate async notification"""
    await asyncio.sleep(0.01)
    print(f"  Notification: {message}")


async def main():
    """Main async function"""
    try:
        # Start async router (blocks until stopped)
        await router.start()
    except KeyboardInterrupt:
        print("\n\nStopping async router...")
        await router.stop()


if __name__ == "__main__":
    asyncio.run(main())
