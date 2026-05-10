"""
Базовая реализация роутера

Общая логика для синхронных и асинхронных роутеров
"""

import logging
from typing import Optional, List, Union, Callable

from .items import ItemDatabase
from .events import FishingEvent, EventHandler


logger = logging.getLogger(__name__)


class BaseFilteredEventHandler(EventHandler):
    """
    Базовый обработчик событий с логикой фильтрации
    
    Используется в синхронной и асинхронной реализациях.
    """
    
    def __init__(
        self,
        event_type: str,
        filters: dict,
        items_db: ItemDatabase,
    ):
        self._event_type = event_type
        self._filters = filters
        self._items_db = items_db
    
    def can_handle(self, event: FishingEvent) -> bool:
        """Проверить может ли обработчик обработать событие"""
        if event.event_type != self._event_type:
            return False

        if self._event_type == "catch" and self._filters:
            return self._check_filters(event)
        
        return True
    
    def _check_filters(self, event: FishingEvent) -> bool:
        """Проверить проходит ли событие все фильтры"""
        if not event.item_id:
            return False

        if self._filters.get('item_ids'):
            if event.item_id not in self._filters['item_ids']:
                return False

        item_tier = self._items_db.get_tier(event.item_id)
        is_fish = self._items_db.is_fish(event.item_id)

        if self._filters.get('fish_only') and not is_fish:
            return False

        if item_tier is not None:
            tier_filter = self._filters.get('tier')
            if tier_filter is not None:
                if isinstance(tier_filter, list):
                    if item_tier not in tier_filter:
                        return False
                else:
                    if item_tier != tier_filter:
                        return False
            
            if self._filters.get('min_tier') is not None:
                if item_tier < self._filters['min_tier']:
                    return False
            
            if self._filters.get('max_tier') is not None:
                if item_tier > self._filters['max_tier']:
                    return False
        
        return True


class BaseRouter:
    """
    Базовый роутер с общей логикой
    
    Предоставляет общие методы для создания декораторов и построения фильтров.
    """
    
    def __init__(self, items_db: Optional[ItemDatabase] = None):
        self.items_db = items_db or ItemDatabase()
    
    def _build_filters(
        self,
        tier: Optional[Union[int, List[int]]] = None,
        min_tier: Optional[int] = None,
        max_tier: Optional[int] = None,
        fish_only: bool = False,
        item_ids: Optional[List[int]] = None,
    ) -> dict:
        """Построить словарь фильтров из параметров"""
        return {
            'tier': tier,
            'min_tier': min_tier,
            'max_tier': max_tier,
            'fish_only': fish_only,
            'item_ids': item_ids,
        }
    
    @staticmethod
    def list_interfaces() -> list:
        """Получить список доступных сетевых интерфейсов"""
        from .fishing import FishingMonitor
        return FishingMonitor.list_interfaces()
