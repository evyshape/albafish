"""
Async декораторы для удобной работы с событиями рыбалки

Позволяет использовать декораторы с async функциями.
"""

import asyncio
import logging
from typing import Callable, Optional, List, Union, Awaitable

from .async_fishing import AsyncFishingMonitor
from .events import FishingEvent
from .items import ItemDatabase
from ._base_router import BaseFilteredEventHandler, BaseRouter


logger = logging.getLogger(__name__)


class AsyncFilteredEventHandler(BaseFilteredEventHandler):
    
    def __init__(
        self,
        callback: Callable[[FishingEvent], Awaitable[None]],
        event_type: str,
        filters: dict,
        items_db: ItemDatabase,
        loop: asyncio.AbstractEventLoop,
    ):
        super().__init__(event_type, filters, items_db)
        self._callback = callback
        self._loop = loop
    
    def handle(self, event: FishingEvent) -> None:
        try:
            asyncio.run_coroutine_threadsafe(self._callback(event), self._loop)
        except Exception as e:
            logger.exception(f"Ошибка в async обработчике {self._callback.__name__}: {e}")


class AsyncFishingRouter(BaseRouter):
    """
    Async роутер для событий.
    
    Использует AsyncFishingMonitor для async обработки событий.
    
    Пример:
        router = AsyncFishingRouter()
        
        @router.on_catch()
        async def handle_catch(event):
            print(f"Поймано: {event.item_id}")
            await asyncio.sleep(0.1)
        
        await router.start()
    """
    
    def __init__(self, items_db: Optional[ItemDatabase] = None):
        """
        Инициализация async роутера
        
        Args:
            items_db: База данных предметов
        """
        super().__init__(items_db)
        self._monitor: Optional[AsyncFishingMonitor] = None
        self._handlers: List[tuple] = []
        self._player_id: Optional[int] = None
        
        logger.info("AsyncFishingRouter инициализирован")
    
    def on_cast(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события заброса удочки
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_cast()
            async def my_handler(event):
                print("Удочка заброшена!")
                await asyncio.sleep(0.1)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "cast", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик заброса: {func.__name__}")
            return func
        return decorator
    
    def on_cast_end(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события окончания заброса (поплавок упал в воду)
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_cast_end()
            async def my_handler(event):
                print("Поплавок упал в воду!")
                await asyncio.sleep(0.1)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "cast_end", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик окончания заброса: {func.__name__}")
            return func
        return decorator
    
    def on_float(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события появления/обновления поплавка
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "float", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик поплавка: {func.__name__}")
            return func
        return decorator
    
    def on_start_pull(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события начала вытягивания рыбы
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "start_pull", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик начала вытягивания: {func.__name__}")
            return func
        return decorator
    
    def on_pulling(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события вытягивания рыбы (процесс)
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "pulling", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик вытягивания: {func.__name__}")
            return func
        return decorator
    
    def on_stop_pull(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события остановки вытягивания (отпустили)
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "stop_pull", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик остановки вытягивания: {func.__name__}")
            return func
        return decorator
    
    def on_fishing_catch(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки улова в процессе рыбалки
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "fishing_catch", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик улова в процессе: {func.__name__}")
            return func
        return decorator
    
    def on_cancel(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события отмены заброса
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "cancel", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик отмены: {func.__name__}")
            return func
        return decorator
    
    def on_bite(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события клёва
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_bite()
            async def my_handler(event):
                print("Рыба клюёт!")
                await save_to_db(event)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "bite", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик клёва: {func.__name__}")
            return func
        return decorator
    
    def on_catch(
        self,
        tier: Optional[Union[int, List[int]]] = None,
        min_tier: Optional[int] = None,
        max_tier: Optional[int] = None,
        fish_only: bool = False,
        item_ids: Optional[List[int]] = None,
        priority: int = 0,
    ) -> Callable:
        """
        Декоратор для обработки события поимки с фильтрами
        
        Args:
            tier: Конкретный тир или список тиров
            min_tier: Минимальный тир (включительно)
            max_tier: Максимальный тир (включительно)
            fish_only: Только рыба (не мусор)
            item_ids: Список конкретных ID предметов
            priority: Приоритет обработчика (больше = раньше)
        
        Примеры:
            @router.on_catch(tier=8)
            async def handle_t8(event):
                print("T8 предмет!")
                await send_notification(event)
            
            @router.on_catch(min_tier=7, fish_only=True)
            async def handle_rare_fish(event):
                print("Редкая рыба T7+!")
                await vivod_babla(event)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            filters = self._build_filters(tier, min_tier, max_tier, fish_only, item_ids)
            self._handlers.append((func, "catch", filters, priority))
            logger.debug(f"Зарегистрирован async обработчик поимки: {func.__name__} с фильтрами {filters}")
            return func
        return decorator
    
    def on_failed(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события срыва рыбы
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_failed()
            async def my_handler(event):
                print("Рыба сорвалась!")
                await log_failure(event)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "failed", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик срыва: {func.__name__}")
            return func
        return decorator
    
    def on_death(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события смерти
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_death()
            async def my_handler(event):
                print("Вы умерли!")
                await log_death(event)
        """
        def decorator(func: Callable[[FishingEvent], Awaitable[None]]) -> Callable:
            self._handlers.append((func, "death", {}, priority))
            logger.debug(f"Зарегистрирован async обработчик смерти: {func.__name__}")
            return func
        return decorator
    
    async def start(self, port: int = 5056, interface: Optional[str] = None) -> None:
        """
        Запуск async мониторинга
        
        Args:
            port: UDP порт для мониторинга (по умолчанию 5056)
            interface: Сетевой интерфейс (по умолчанию все)
        """
        self._monitor = AsyncFishingMonitor(items_db=self.items_db)
        loop = asyncio.get_running_loop()

        for callback, event_type, filters, priority in self._handlers:
            handler = AsyncFilteredEventHandler(
                callback, event_type, filters, self.items_db, loop
            )
            self._monitor._monitor.event_bus.register_handler(handler, priority)
        
        if self._player_id is not None:
            self._monitor._monitor.set_player_id(self._player_id)
        
        logger.info("Запуск async роутера")
        await self._monitor.start(port=port, interface=interface)
    
    def set_player_id(self, player_id: int) -> None:
        """Установить player_id для фильтрации чужих событий"""
        self._player_id = player_id
        if self._monitor:
            self._monitor._monitor.set_player_id(player_id)
        logger.info(f"Player ID установлен: {player_id}")
    
    async def stop(self) -> None:
        if self._monitor:
            await self._monitor.stop()
    
    @property
    def is_running(self) -> bool:
        return self._monitor.is_running if self._monitor else False
    
    @property
    def player_id(self) -> Optional[int]:
        return self._monitor.player_id if self._monitor else None


def create_async_router(items_db: Optional[ItemDatabase] = None) -> AsyncFishingRouter:
    return AsyncFishingRouter(items_db=items_db)
