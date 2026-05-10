"""
Константы для событий и операций игры

Определяет коды событий, операций и типы событий рыбалки.
"""

from enum import IntEnum


class EventCode(IntEnum):
    """Коды событий Photon18 протокола"""
    NEW_SIMPLE_ITEM = 32      # Новый предмет
    KNOCKED_DOWN = 166        # Игрок нокнулся
    FISHING_EVENT = 353       # Событие рыбалки
    NEW_FLOAT_OBJECT = 358    # Новый плавающий объект (поплавок вероятно)


class FishingEventType(IntEnum):
    """Типы событий рыбалки"""
    CAST = 3          # Заброс удочки
    CAST_END = 4      # Конец заброса (поплавок булькнул)
    BITE = 5          # Поклевка
    STOP_PULL = 7     # Не тянем
    PULLING = 8       # Тянем
    CATCH = 9         # Улов
    FAILED = 10       # Срыв рыбы (передернул/недодернул)
    CANCEL = 15       # Отмена заброса


class OperationCode(IntEnum):
    """Коды операций Photon18 протокола"""
    GENERIC_ACTION = 1        # Общее действие


class EventType(IntEnum):
    """Типы событий рыбалки"""
    CAST = 1            # Заброс удочки (начало)
    CAST_END = 2        # Конец заброса (поплавок упал в воду)
    FLOAT = 3           # Поплавок обновился
    BITE = 4            # Клев рыбы
    START_PULL = 5      # Начали тянуть рыбу
    PULLING = 6         # Тянем рыбу
    STOP_PULL = 7       # Перестали тянуть
    CATCH = 8           # Улов
    FISHING_CATCH = 9   # Улов в процессе
    FAILED = 10         # Срыв рыбы
    CANCEL = 11         # Отмена заброса
    DEATH = 12          # Смерть игрока


EVENT_TYPE_NAMES = {
    EventType.CAST: "cast",
    EventType.CAST_END: "cast_end",
    EventType.FLOAT: "float",
    EventType.BITE: "bite",
    EventType.START_PULL: "start_pull",
    EventType.PULLING: "pulling",
    EventType.STOP_PULL: "stop_pull",
    EventType.CATCH: "catch",
    EventType.FISHING_CATCH: "fishing_catch",
    EventType.FAILED: "failed",
    EventType.CANCEL: "cancel",
    EventType.DEATH: "death",
}


class RequestParameter(IntEnum):
    """Параметры запросов"""
    ACTION_TYPE = 253


class FishingAction(IntEnum):
    """Действия связанные с рыбалкой (REQUEST)"""
    START_PULL = 319  # Начали тянуть рыбу
    STOP_PULL = 320   # Перестали тянуть
    PULLING = 321     # Тянем рыбу
    CAST_ROD = 322    # Заброс удочки
    CANCEL_ROD = 323  # Отмена заброса
