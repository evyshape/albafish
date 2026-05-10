"""
Event system для fishing monitor

Предоставляет event bus и middleware для обработки событий.
"""

import logging
from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FishingEvent:
    """
    Неизменяемое событие рыбалки
    
    Attributes:
        timestamp: Время события
        event_type: Тип события (cast, success, catch, death)
        player_id: ID игрока (опционально)
        item_id: ID предмета (опционально)
        param2: Дополнительный параметр (опционально)
        object_id: ID объекта (опционально)
        metadata: Дополнительные метаданные
    """
    timestamp: datetime
    event_type: str
    player_id: Optional[int] = None
    item_id: Optional[int] = None
    param2: Optional[int] = None
    object_id: Optional[int] = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})
    
    @property
    def is_cast(self) -> bool:
        """Проверка: событие заброса удочки"""
        return self.event_type == "cast"
    
    @property
    def is_cast_end(self) -> bool:
        """Проверка: конец заброса (поплавок упал)"""
        return self.event_type == "cast_end"
    
    @property
    def is_float(self) -> bool:
        """Проверка: событие появления/обновления поплавка"""
        return self.event_type == "float"
    
    @property
    def is_bite(self) -> bool:
        """Проверка: событие клева"""
        return self.event_type == "bite"
    
    @property
    def is_start_pull(self) -> bool:
        """Проверка: начали тянуть рыбу"""
        return self.event_type == "start_pull"
    
    @property
    def is_pulling(self) -> bool:
        """Проверка: тянем рыбу"""
        return self.event_type == "pulling"
    
    @property
    def is_stop_pull(self) -> bool:
        """Проверка: перестали тянуть (отпустили)"""
        return self.event_type == "stop_pull"
    
    @property
    def is_catch(self) -> bool:
        """Проверка: событие поимки"""
        return self.event_type == "catch"
    
    @property
    def is_fishing_catch(self) -> bool:
        """Проверка: улов в процессе рыбалки"""
        return self.event_type == "fishing_catch"
    
    @property
    def is_failed(self) -> bool:
        """Проверка: срыв рыбы"""
        return self.event_type == "failed"
    
    @property
    def is_cancel(self) -> bool:
        """Проверка: событие отмены заброса"""
        return self.event_type == "cancel"
    
    @property
    def is_death(self) -> bool:
        """Проверка: событие смерти"""
        return self.event_type == "death"
    
    def with_metadata(self, **kwargs) -> 'FishingEvent':
        """
        Создать новое событие с дополнительными метаданными
        
        Args:
            **kwargs: Метаданные для добавления
        
        Returns:
            Новое событие с обновленными метаданными
        """
        new_metadata = {**self.metadata, **kwargs}
        return FishingEvent(
            timestamp=self.timestamp,
            event_type=self.event_type,
            player_id=self.player_id,
            item_id=self.item_id,
            param2=self.param2,
            object_id=self.object_id,
            metadata=new_metadata,
        )


class EventHandler(ABC):
    """
    Базовый класс для обработчиков событий
    """
    
    @abstractmethod
    def handle(self, event: FishingEvent) -> None:
        """
        Обработать событие
        
        Args:
            event: Событие для обработки
        """
        pass
    
    @abstractmethod
    def can_handle(self, event: FishingEvent) -> bool:
        """
        Проверить может ли обработчик обработать событие
        
        Args:
            event: Событие для проверки
        
        Returns:
            True если может обработать
        """
        pass


class CallbackEventHandler(EventHandler):
    """
    Обработчик событий на основе callback функции
    """
    
    def __init__(self, callback: Callable[[FishingEvent], None], event_type: Optional[str] = None):
        """
        Args:
            callback: Функция для вызова при событии
            event_type: Тип события для фильтрации (None = все события)
        """
        self._callback = callback
        self._event_type = event_type
    
    def can_handle(self, event: FishingEvent) -> bool:
        if self._event_type is None:
            return True
        return event.event_type == self._event_type
    
    def handle(self, event: FishingEvent) -> None:
        try:
            self._callback(event)
        except Exception as e:
            logger.exception(f"Ошибка в callback обработчике: {e}")


class Middleware(ABC):
    """
    Базовый класс для middleware
    
    Middleware может:
    - Модифицировать события
    - Блокировать события
    - Добавлять метаданные
    - Логировать события
    """
    
    @abstractmethod
    def process(self, event: FishingEvent, next_handler: Callable[[FishingEvent], None]) -> None:
        """
        Обработать событие и передать дальше по цепочке
        
        Args:
            event: Событие для обработки
            next_handler: Следующий обработчик в цепочке
        """
        pass


class LoggingMiddleware(Middleware):
    """
    Middleware для логирования событий
    """
    
    def __init__(self, level: int = logging.DEBUG):
        """
        Args:
            level: Уровень логирования
        """
        self.level = level
    
    def process(self, event: FishingEvent, next_handler: Callable[[FishingEvent], None]) -> None:
        logger.log(
            self.level,
            f"Event: {event.event_type} | "
            f"player_id={event.player_id} | "
            f"item_id={event.item_id}"
        )
        next_handler(event)


class FilterMiddleware(Middleware):
    """
    Middleware для фильтрации событий
    """
    
    def __init__(self, predicate: Callable[[FishingEvent], bool]):
        """
        Args:
            predicate: Функция для проверки события (True = пропустить)
        """
        self.predicate = predicate
    
    def process(self, event: FishingEvent, next_handler: Callable[[FishingEvent], None]) -> None:
        if self.predicate(event):
            next_handler(event)
        else:
            logger.debug(f"Событие отфильтровано: {event.event_type}")


class EnrichmentMiddleware(Middleware):
    """
    Middleware для засовывания в событие метаданных
    """
    
    def __init__(self, enricher: Callable[[FishingEvent], dict]):
        """
        Args:
            enricher: Функция для получения дополнительных метаданных
        """
        self.enricher = enricher
    
    def process(self, event: FishingEvent, next_handler: Callable[[FishingEvent], None]) -> None:
        try:
            metadata = self.enricher(event)
            enriched_event = event.with_metadata(**metadata)
            next_handler(enriched_event)
        except Exception as e:
            logger.exception(f"Ошибка в enrichment middleware: {e}")
            next_handler(event)


class EventBus:
    """
    Event bus для управления событиями и обработчиками
    
    Поддерживает:
    - Регистрацию обработчиков
    - Middleware цепочку
    - Приоритеты обработчиков
    """
    
    def __init__(self):
        self._handlers: List[tuple[int, EventHandler]] = []
        self._middlewares: List[Middleware] = []
        self._enabled = True
    
    def register_handler(self, handler: EventHandler, priority: int = 0) -> None:
        """
        Зарегистрировать обработчик событий
        
        Args:
            handler: Обработчик для регистрации
            priority: Приоритет (больше = раньше выполняется)
        """
        self._handlers.append((priority, handler))
        self._handlers.sort(key=lambda x: x[0], reverse=True)
        logger.debug(f"Зарегистрирован обработчик: {handler.__class__.__name__} (priority={priority})")
    
    def unregister_handler(self, handler: EventHandler) -> None:
        """
        Удалить обработчик
        
        Args:
            handler: Обработчик для удаления
        """
        self._handlers = [(p, h) for p, h in self._handlers if h != handler]
        logger.debug(f"Удален обработчик: {handler.__class__.__name__}")
    
    def add_middleware(self, middleware: Middleware) -> None:
        """
        Добавить middleware в цепочку
        
        Args:
            middleware: Middleware для добавления
        """
        self._middlewares.append(middleware)
        logger.debug(f"Добавлен middleware: {middleware.__class__.__name__}")
    
    def remove_middleware(self, middleware: Middleware) -> None:
        """
        Удалить middleware из цепочки
        
        Args:
            middleware: Middleware для удаления
        """
        self._middlewares = [m for m in self._middlewares if m != middleware]
        logger.debug(f"Удален middleware: {middleware.__class__.__name__}")
    
    def emit(self, event: FishingEvent) -> None:
        """
        Отправить событие всем обработчикам через middleware цепочку
        
        Args:
            event: Событие для отправки
        """
        if not self._enabled:
            return

        def final_handler(evt: FishingEvent) -> None:
            for _, handler in self._handlers:
                if handler.can_handle(evt):
                    try:
                        handler.handle(evt)
                    except Exception as e:
                        logger.exception(f"Ошибка в обработчике {handler.__class__.__name__}: {e}")

        handler = final_handler
        for middleware in reversed(self._middlewares):
            current_middleware = middleware
            current_handler = handler
            handler = lambda evt, m=current_middleware, h=current_handler: m.process(evt, h)

        try:
            handler(event)
        except Exception as e:
            logger.exception(f"Ошибка в middleware цепочке: {e}")
    
    def enable(self) -> None:
        self._enabled = True
    
    def disable(self) -> None:
        self._enabled = False
    
    def clear(self) -> None:
        self._handlers.clear()
        self._middlewares.clear()
    
    @property
    def handler_count(self) -> int:
        return len(self._handlers)
    
    @property
    def middleware_count(self) -> int:
        return len(self._middlewares)
