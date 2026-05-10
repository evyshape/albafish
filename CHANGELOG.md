# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
