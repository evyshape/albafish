"""
База данных предметов Albion Online

Загружает и предоставляет доступ к информации о предметах.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from .exceptions import ItemDatabaseError, ItemNotFoundError


logger = logging.getLogger(__name__)


class ItemDatabase:
    """
    База данных предметов Albion Online
    
    Загружает данные из JSON файла и предоставляет методы
    для получения информации о предметах.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Инициализация базы данных
        
        Args:
            data_path: Путь к JSON файлу с данными (опционально)
        """
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "items.json"
        
        self.data_path = Path(data_path)
        
        if not self.data_path.exists():
            raise ItemDatabaseError(
                f"Файл базы данных предметов не найден: {self.data_path}\n"
                f"Убедитесь что пакет установлен корректно."
            )
        
        if not self.data_path.is_file():
            raise ItemDatabaseError(
                f"Путь к базе данных не является файлом: {self.data_path}"
            )
        
        self.items: Dict[int, dict] = {}
        self.version: str = ""
        self.total_items: int = 0
        
        self._load()
    
    def _load(self) -> None:
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError as e:
            raise ItemDatabaseError(f"База данных предметов не найдена: {self.data_path}") from e
        except json.JSONDecodeError as e:
            raise ItemDatabaseError(f"Некорректный JSON в базе данных: {self.data_path}") from e
        
        self.version = data.get("version", "unknown")
        self.total_items = data.get("total_items", 0)
        
        for item_id, item_data in data["items"].items():
            self.items[int(item_id)] = item_data
        
        logger.debug(f"Загружено {self.total_items} предметов из базы данных (версия: {self.version})")
    
    def get(self, item_id: int) -> Optional[dict]:
        return self.items.get(item_id)
    
    def get_name(self, item_id: int) -> str:
        """
        Получить отображаемое имя предмета
        
        Args:
            item_id: ID предмета
        
        Returns:
            Имя предмета или "Unknown Item"
        """
        item = self.get(item_id)
        if not item:
            logger.warning(f"Предмет {item_id} не найден в базе данных")
            return "Unknown Item"
        return item["display_name"]
    
    def get_unique_name(self, item_id: int) -> str:
        """
        Получить уникальное имя предмета
        
        Args:
            item_id: ID предмета
        
        Returns:
            Уникальное имя или "Unknown Item"
        """
        item = self.get(item_id)
        if not item:
            logger.warning(f"Предмет {item_id} не найден в базе данных")
            return "Unknown Item"
        return item["unique_name"]
    
    def is_fish(self, item_id: int) -> bool:
        """
        Проверить является ли предмет рыбой
        
        Args:
            item_id: ID предмета
        
        Returns:
            True если это рыба
        """
        item = self.get(item_id)
        return item is not None and item.get("category") == "fish"
    
    def get_tier(self, item_id: int) -> Optional[int]:
        """
        Получить тир предмета
        
        Args:
            item_id: ID предмета
        
        Returns:
            Тир (1-8) или None
        """
        item = self.get(item_id)
        return item.get("tier") if item else None
    
    def get_category(self, item_id: int) -> Optional[str]:
        """
        Получить категорию предмета
        
        Args:
            item_id: ID предмета
        
        Returns:
            Категория или None
        """
        item = self.get(item_id)
        return item.get("category") if item else None
