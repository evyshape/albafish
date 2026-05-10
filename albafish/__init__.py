__version__ = "1.0.0"

import logging

from .events import FishingEvent, EventHandler, EventBus, Middleware
from .events import LoggingMiddleware, FilterMiddleware, EnrichmentMiddleware
from .fishing import FishingMonitor
from .async_fishing import AsyncFishingMonitor
from .decorators import FishingRouter, create_router
from .async_decorators import AsyncFishingRouter, create_async_router
from .items import ItemDatabase
from .constants import EventCode, EventType, OperationCode
from .exceptions import (
    AlbionFishermanError,
    ItemDatabaseError,
    ItemNotFoundError,
    PacketParseError,
    InvalidPortError,
    PermissionError,
    DependencyError,
)


logging.getLogger("albafish").setLevel(logging.WARNING)


def enable_logging(level: int = logging.INFO) -> None:
    """
    Включить логирование библиотеки
    
    Args:
        level: Уровень логирования (logging.DEBUG, logging.INFO, и т.д.)
    
    Example:
        >>> import albafish
        >>> albafish.enable_logging(logging.DEBUG)
    """
    logging.getLogger("albafish").setLevel(level)


def disable_logging() -> None:
    """
    Отключить логирование библиотеки (только CRITICAL)
    
    Example:
        >>> import albafish
        >>> albafish.disable_logging()
    """
    logging.getLogger("albafish").setLevel(logging.CRITICAL)


__all__ = [
    "FishingMonitor",
    "AsyncFishingMonitor",
    "FishingRouter",
    "AsyncFishingRouter",
    "create_router",
    "create_async_router",

    "FishingEvent",
    "EventHandler",
    "EventBus",

    "Middleware",
    "LoggingMiddleware",
    "FilterMiddleware",
    "EnrichmentMiddleware",

    "ItemDatabase",

    "EventCode",
    "EventType",
    "OperationCode",

    "AlbionFishermanError",
    "ItemDatabaseError",
    "ItemNotFoundError",
    "PacketParseError",
    "InvalidPortError",
    "PermissionError",
    "DependencyError",

    "enable_logging",
    "disable_logging",
]
