"""
Все кастомные исключения наследуются от AlbionFishermanError.
"""


class AlbionFishermanError(Exception):
    """Базовое исключение для всех ошибок библиотеки"""
    pass


class ItemDatabaseError(AlbionFishermanError):
    """Ошибки связанные с базой данных предметов"""
    pass


class ItemNotFoundError(ItemDatabaseError):
    """Предмет не найден в базе данных"""
    pass


class PacketParseError(AlbionFishermanError):
    """Ошибка парсинга сетевого пакета"""
    pass


class InvalidPortError(AlbionFishermanError):
    """Некорректный номер порта"""
    pass


class PermissionError(AlbionFishermanError):
    """Недостаточно прав для захвата пакетов"""
    pass


class DependencyError(AlbionFishermanError):
    """Отсутствуют необходимые зависимости"""
    pass
