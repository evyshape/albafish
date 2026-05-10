# 🎣 AlbaFish

**Образовательный инструмент для анализа механики рыбалки в Albion Online через анализ сетевых пакетов**

> ⚠️ **ТОЛЬКО ДЛЯ ОБРАЗОВАТЕЛЬНЫХ ЦЕЛЕЙ** =)  
> Эта библиотека создана для изучения сетевых протоколов, анализа пакетов и исследования игровой механики.  
> **НЕ предназначена для создания игровых ботов или инструментов автоматизации.**

## 📚 Что это?

AlbaFish — это Python библиотека, которая перехватывает и парсит сетевые пакеты Albion Online для понимания механики рыбалки. Создана для:

- 🎓 **Обучения** протоколу Photon и анализу пакетов
- 🔬 **Исследования** игровых сетевых взаимодействий и систем событий
- 📊 **Понимания** коммуникации клиент-сервер в MMO

## ✨ Возможности

- 🎯 Мониторинг событий рыбалки в реальном времени (заброс, клёв, улов и т.д.)
- 🐟 Полная база предметов Albion Online (11,000+ предметов)
- ⚡ Поддержка синхронного и асинхронного API
- 🎨 Роутинг событий через декораторы
- 🔧 Система middleware для обработки событий
- 📦 Type hints и комплексная обработка ошибок

## 🚀 Быстрый старт

### Установка

```bash
pip install albafish
```

**Требования:**
- Python 3.7+
- `scapy>=2.5.0` (устанавливается автоматически)
- Права администратора/root (для перехвата пакетов)
- Windows: [Npcap](https://npcap.com/#download)
- Linux: `libpcap-dev`
- macOS: `libpcap` (обычно предустановлен)

### Базовый пример

```python
import albafish

# Создаём базу предметов
items = albafish.ItemDatabase()

# Простой callback
def on_catch(event):
    fish_name = items.get_name(event.item_id)
    print(f"🎣 Поймано: {fish_name}")

# Создаём монитор
monitor = albafish.FishingMonitor(on_catch=on_catch, items_db=items)

# Запускаем мониторинг (требует admin/root)
monitor.start()
```

### Стиль с декораторами

```python
from albafish import create_router

router = create_router()

@router.on_catch(tier=8, fish_only=True)
def rare_fish(event):
    print("🐟 Редкая рыба T8!")

@router.on_bite()
def bite_alert(event):
    print("🎣 Рыба клюёт!")

router.start()
```

### Поддержка async

```python
import asyncio
from albafish import create_async_router

router = create_async_router()

@router.on_catch()
async def handle_catch(event):
    print(f"Поймано: {event.item_id}")
    await asyncio.sleep(0.1)  # async операции

asyncio.run(router.start())
```

## 📖 Документация

### События

- `on_cast` - Начало заброса удочки
- `on_cast_end` - Поплавок упал в воду
- `on_bite` - Рыба клюёт
- `on_start_pull` - Начали тянуть
- `on_pulling` - Процесс вытягивания
- `on_catch` - Предмет пойман
- `on_failed` - Рыба сорвалась
- `on_death` - Игрок умер

### Фильтрация

```python
# Ловить только рыбу T7+
@router.on_catch(min_tier=7, fish_only=True)
def rare_fish(event):
    pass

# Конкретные тиры
@router.on_catch(tier=[6, 7, 8])
def high_tier(event):
    pass

# Конкретные предметы
@router.on_catch(item_ids=[142, 143, 144])
def specific_items(event):
    pass
```

## 🛠️ Продвинутое использование

### Кастомный Event Bus

```python
from albafish import FishingMonitor, EventBus, LoggingMiddleware

bus = EventBus()
bus.add_middleware(LoggingMiddleware())

monitor = FishingMonitor(event_bus=bus)
```

### Фильтрация по игроку

```python
# Автоопределение игрока (по умолчанию)
monitor = FishingMonitor(auto_detect_player=True)

# Конкретный ID игрока
monitor = FishingMonitor(player_id=12345)
```

## 📋 Примеры

Смотри папку `/examples`:
- `basic_monitor.py` - Простой мониторинг событий
- `decorator_router.py` - Роутинг через декораторы
- `async_example.py` - Использование async/await
- `filtered_catch.py` - Продвинутая фильтрация

## ⚠️ Важные замечания

1. **Требуются повышенные права** - Запускай от Администратора (Windows) или через `sudo` (Linux/Mac)
2. **Только для обучения** - Не для автоматизации игры или ботов
3. **Перехват сети** - Мониторит UDP порт 5056 по умолчанию
4. **Приватность** - Перехватывает только игровые пакеты, никаких личных данных

## 🤝 Участие в разработке

Это образовательный проект. Приветствуется:
- Сообщения об ошибках
- Предложения по улучшению
- Обмен опытом обучения

**Не принимается:**
- Функции для автоматизации игры
- Функционал для ботов
- Запросы на коммерческое использование

## 📜 Лицензия

Некоммерческая лицензия - Бесплатно только для образовательных и исследовательских целей.  
Подробности в [LICENSE](https://github.com/evyshape/albafish/blob/main/LICENSE).

## 👤 Автор

**evyshape**

---

**Дисклеймер:** Этот инструмент создан для образовательных целей. Автор не несёт ответственности за неправильное использование.  
Albion Online является торговой маркой Sandbox Interactive GmbH.

=)
