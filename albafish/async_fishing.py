"""
Async обертка для FishingMonitor

Предоставляет asyncio-совместимый интерфейс для монитора рыбалки.
"""

import asyncio
import logging
import threading
from typing import Optional, Callable, Awaitable
from queue import Queue

from .fishing import FishingMonitor
from .events import FishingEvent
from .items import ItemDatabase


logger = logging.getLogger(__name__)


class AsyncFishingMonitor:
    """
    Async обертка для FishingMonitor
    
    Этот класс запускает блокирующий FishingMonitor в отдельном потоке
    и предоставляет async callbackи для событий.
    
    Пример:
        async def on_catch(event):
            print(f"Поймано: {event.item_id}")
        
        monitor = AsyncFishingMonitor(on_catch=on_catch)
        await monitor.start()
    """
    
    def __init__(
        self,
        on_cast: Optional[Callable[[FishingEvent], Awaitable[None]]] = None,
        on_bite: Optional[Callable[[FishingEvent], Awaitable[None]]] = None,
        on_catch: Optional[Callable[[FishingEvent], Awaitable[None]]] = None,
        on_death: Optional[Callable[[FishingEvent], Awaitable[None]]] = None,
        items_db: Optional[ItemDatabase] = None,
    ):
        self._async_handlers = {
            'cast': on_cast,
            'bite': on_bite,
            'catch': on_catch,
            'death': on_death,
        }
        
        self._event_queue: Queue = Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._event_processor_task: Optional[asyncio.Task] = None
        self._running = False

        self._monitor = FishingMonitor(
            on_cast=lambda e: self._enqueue_event('cast', e) if on_cast else None,
            on_bite=lambda e: self._enqueue_event('bite', e) if on_bite else None,
            on_catch=lambda e: self._enqueue_event('catch', e) if on_catch else None,
            on_death=lambda e: self._enqueue_event('death', e) if on_death else None,
            items_db=items_db,
        )
        
        logger.info("AsyncFishingMonitor inited")
    
    def _enqueue_event(self, event_type: str, event: FishingEvent) -> None:
        self._event_queue.put((event_type, event))
    
    async def _process_events(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(0.01)
                
                if not self._event_queue.empty():
                    event_type, event = self._event_queue.get_nowait()
                    handler = self._async_handlers.get(event_type)
                    
                    if handler:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.exception(f"Ошибка в async {event_type} обработчике: {e}")
                
            except Exception as e:
                logger.exception(f"Ошибка обработки событий: {e}")
    
    def _run_monitor(self, port: int, interface: Optional[str]) -> None:
        try:
            self._monitor.start(port=port, interface=interface)
        except Exception as e:
            logger.exception(f"Ошибка потока монитора: {e}")
    
    async def start(self, port: int = 5056, interface: Optional[str] = None) -> None:
        """
        Запуск мониторинга
        
        Args:
            port: UDP порт для мониторинга (по умолчанию 5056)
            interface: Сетевой интерфейс для захвата (по умолчанию None = все интерфейсы)
        """
        if self._running:
            logger.warning("AsyncFishingMonitor уже запущен")
            return
        
        self._running = True
        self._loop = asyncio.get_running_loop()
        self._event_processor_task = asyncio.create_task(self._process_events())

        self._monitor_thread = threading.Thread(
            target=self._run_monitor,
            args=(port, interface),
            daemon=True
        )
        self._monitor_thread.start()

        logger.info(f"AsyncFishingMonitor запущен на порту {port}")

        await asyncio.get_running_loop().run_in_executor(
            None, self._monitor_thread.join
        )
    
    async def stop(self) -> None:
        if not self._running:
            logger.warning("AsyncFishingMonitor не запущен")
            return
        
        logger.info("Остановка AsyncFishingMonitor...")
        self._running = False

        self._monitor.stop()

        if self._event_processor_task:
            self._event_processor_task.cancel()
            try:
                await self._event_processor_task
            except asyncio.CancelledError:
                pass

        if self._monitor_thread and self._monitor_thread.is_alive():
            await asyncio.get_running_loop().run_in_executor(
                None, self._monitor_thread.join, 2.0
            )
        
        logger.info("AsyncFishingMonitor остановлен")
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    @property
    def player_id(self) -> Optional[int]:
        return self._monitor.player_id
    
    @property
    def items_db(self) -> ItemDatabase:
        return self._monitor.items_db
    
    @staticmethod
    def list_interfaces() -> list:
        return FishingMonitor.list_interfaces()
