"""
Декораторы для удобной работы с событиями рыбалки

Позволяет использовать декораторы для регистрации обработчиков событий.
"""

import logging
from typing import Callable, Optional, List, Union

from .fishing import FishingMonitor
from .events import FishingEvent
from .items import ItemDatabase
from ._base_router import BaseFilteredEventHandler, BaseRouter


logger = logging.getLogger(__name__)


class FilteredEventHandler(BaseFilteredEventHandler):
    
    def __init__(
        self,
        callback: Callable[[FishingEvent], None],
        event_type: str,
        filters: dict,
        items_db: ItemDatabase,
    ):
        super().__init__(event_type, filters, items_db)
        self._callback = callback
    
    def handle(self, event: FishingEvent) -> None:
        try:
            self._callback(event)
        except Exception as e:
            logger.exception(f"Ошибка в обработчике {self._callback.__name__}: {e}")


class FishingRouter(BaseRouter):
    """
    Роутер для событий рыбалки
    
    Использует event bus для управления обработчиками.
    Поддерживает фильтрацию событий.
    
    Пример:
        router = FishingRouter()
        
        @router.on_catch()
        def handle_catch(event):
            print(f"Поймано: {event.item_id}")
        
        @router.on_catch(tier=8)
        def handle_rare_catch(event):
            print("Редкая рыба!")
        
        router.start()
    """
    
    def __init__(self, items_db: Optional[ItemDatabase] = None):
        """
        Инициализация роутера
        
        Args:
            items_db: База шмоток
        """
        super().__init__(items_db)
        self._monitor: Optional[FishingMonitor] = None
        
        logger.info("FishingRouter инициализирован")
    
    def on_cast(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события заброса удочки
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_cast()
            def my_handler(event):
                print("Удочка заброшена!")
        """
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "cast", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик заброса: {func.__name__}")
            return func
        return decorator
    
    def on_cast_end(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события окончания заброса (поплавок упал в воду)
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_cast_end()
            def my_handler(event):
                print("Поплавок упал в воду!")
        """
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "cast_end", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик окончания заброса: {func.__name__}")
            return func
        return decorator
    
    def on_float(self, priority: int = 0) -> Callable:
        """Декоратор для обработки события появления/обновления поплавка"""
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "float", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик поплавка: {func.__name__}")
            return func
        return decorator
    
    def on_start_pull(self, priority: int = 0) -> Callable:
        """Декоратор для обработки события начала вытягивания рыбы"""
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "start_pull", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик начала вытягивания: {func.__name__}")
            return func
        return decorator
    
    def on_pulling(self, priority: int = 0) -> Callable:
        """Декоратор для обработки события вытягивания рыбы (процесс)"""
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "pulling", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик вытягивания: {func.__name__}")
            return func
        return decorator
    
    def on_stop_pull(self, priority: int = 0) -> Callable:
        """Декоратор для обработки события остановки вытягивания (отпустили)"""
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "stop_pull", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик остановки вытягивания: {func.__name__}")
            return func
        return decorator
    
    def on_fishing_catch(self, priority: int = 0) -> Callable:
        """Декоратор для обработки улова в процессе рыбалки"""
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "fishing_catch", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик улова в процессе: {func.__name__}")
            return func
        return decorator
    
    def on_cancel(self, priority: int = 0) -> Callable:
        """Декоратор для обработки события отмены заброса"""
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "cancel", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик отмены: {func.__name__}")
            return func
        return decorator
    
    def on_bite(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события клёва
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_bite()
            def my_handler(event):
                print("Рыба клюёт!")
        """
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "bite", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик клёва: {func.__name__}")
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
            def handle_t8(event):
                print("T8 предмет!")
            
            @router.on_catch(min_tier=7, fish_only=True)
            def handle_rare_fish(event):
                print("Редкая рыба T7+!")
        """
        def decorator(func: Callable) -> Callable:
            filters = self._build_filters(tier, min_tier, max_tier, fish_only, item_ids)
            if self._monitor:
                handler = FilteredEventHandler(func, "catch", filters, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик поимки: {func.__name__} с фильтрами {filters}")
            return func
        return decorator
    
    def on_failed(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события срыва рыбы
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_failed()
            def my_handler(event):
                print("Рыба сорвалась!")
        """
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "failed", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик срыва: {func.__name__}")
            return func
        return decorator
    
    def on_death(self, priority: int = 0) -> Callable:
        """
        Декоратор для обработки события смерти
        
        Args:
            priority: Приоритет обработчика (больше = раньше)
        
        Пример:
            @router.on_death()
            def my_handler(event):
                print("Вы умерли!")
        """
        def decorator(func: Callable) -> Callable:
            if self._monitor:
                handler = FilteredEventHandler(func, "death", {}, self.items_db)
                self._monitor.event_bus.register_handler(handler, priority)
            logger.debug(f"Зарегистрирован обработчик смерти: {func.__name__}")
            return func
        return decorator
    
    def start(self, port: int = 5056, interface: Optional[str] = None) -> None:
        """
        Запуск мониторинга
        
        Args:
            port: UDP порт для мониторинга (по умолчанию 5056)
            interface: Сетевой интерфейс (по умолчанию все)
        """
        self._monitor = FishingMonitor(items_db=self.items_db)
        
        logger.info(f"Запуск роутера")
        self._monitor.start(port=port, interface=interface)
    
    def stop(self) -> None:
        if self._monitor:
            self._monitor.stop()
    
    @property
    def is_running(self) -> bool:
        return self._monitor.is_running if self._monitor else False
    
    @property
    def player_id(self) -> Optional[int]:
        return self._monitor.player_id if self._monitor else None
    
    @property
    def event_bus(self):
        return self._monitor.event_bus if self._monitor else None


def create_router(items_db: Optional[ItemDatabase] = None) -> FishingRouter:
    return FishingRouter(items_db=items_db)
