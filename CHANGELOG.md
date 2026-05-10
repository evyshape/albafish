# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.5] - 2026-05-10

### Fixed
- Fixed NameError: FishingEventType not imported at module level in fishing.py

## [1.0.4] - 2026-05-10

### Fixed
- Fixed player ID filtering - removed auto-reassignment that caused ID to switch between nearby players
- Player ID is now locked permanently after first detection

### Added
- `set_player_id()` method exposed on `AsyncFishingRouter`

## [1.0.3] - 2026-05-10

### Added
- `set_player_id()` method in `AsyncFishingRouter` to lock player ID filtering
- `_player_id` field in `AsyncFishingRouter` to persist player ID before monitor starts

### Fixed
- Player ID is now correctly passed to the underlying monitor when set before `start()`

## [1.0.2] - 2026-05-10

### Added
- Added missing event decorators for complete event coverage:
  - `on_cast_end()` - Cast end event (float landed in water)
  - `on_float()` - Float appearance/update event
  - `on_start_pull()` - Started pulling fish event
  - `on_pulling()` - Pulling fish process event
  - `on_stop_pull()` - Stopped pulling event
  - `on_fishing_catch()` - Fishing catch in progress event
  - `on_cancel()` - Cast cancelled event
- All decorators now available in both `FishingRouter` and `AsyncFishingRouter`
- Complete parity between event types in `FishingEvent` and available decorators

### Changed
- Improved decorator documentation

## [1.0.1] - 2026-05-10

### Fixed
- Fixed ItemDatabase path resolution - now correctly finds items.json after package installation

## [1.0.0] - 2026-05-10

### Added
- Initial release
- Photon protocol parser for Albion Online packets
- Real-time fishing event monitoring (cast, bite, catch, failed, death)
- Complete item database with 11,000+ Albion Online items
- Sync and async API support
- Decorator-based event routing with filters
- Event bus with middleware system
- Tier-based filtering (min_tier, max_tier, specific tiers)
- Fish-only filtering
- Item ID filtering
- Player ID detection and filtering
- Type hints throughout the codebase
- Comprehensive error handling with custom exceptions
- Logging system with configurable levels
- Network interface selection
- Examples for basic usage, decorators, async, and filtering

### Features
- `FishingMonitor` - Synchronous event monitoring
- `AsyncFishingMonitor` - Asynchronous event monitoring
- `FishingRouter` - Decorator-based sync routing
- `AsyncFishingRouter` - Decorator-based async routing
- `ItemDatabase` - Item information lookup
- `EventBus` - Event management with middleware
- Multiple middleware types (Logging, Filter, Enrichment)

### Documentation
- README with quick start guide
- 4 example scripts
- Inline documentation and docstrings
- License file
