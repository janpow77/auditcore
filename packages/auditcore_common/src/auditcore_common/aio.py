"""Run coroutines from synchronous code (Celery tasks, thread pools)."""

from __future__ import annotations

import asyncio
import os
import threading
from collections.abc import Coroutine
from typing import TypeVar

T = TypeVar("T")


class ThreadLoopRunner:
    """One event loop per thread, recreated after a fork or when closed.

    Async clients (HTTPX, Redis, SQLAlchemy) bind connections to the loop of
    their first call; a new loop per task would break those cached clients.
    Each runner keeps its own loops: give every module that had its own loop
    state its own runner to keep that separation.
    """

    def __init__(self) -> None:
        self._state = threading.local()

    def run(self, coro: Coroutine[object, object, T]) -> T:
        """Run ``coro`` to completion on this thread's loop."""
        process_id = os.getpid()
        loop: asyncio.AbstractEventLoop | None = getattr(self._state, "loop", None)
        owner = getattr(self._state, "process_id", None)
        if loop is None or loop.is_closed() or owner != process_id:
            loop = asyncio.new_event_loop()
            self._state.loop = loop
            self._state.process_id = process_id
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


#: Module-wide runner for callers without their own loop separation.
run_sync = ThreadLoopRunner().run


def run_on_current_loop(coro: Coroutine[object, object, T]) -> T:
    """Legacy variant: the thread's current loop, a new one only if there is none.

    Uses ``asyncio.get_event_loop()``, which warns since Python 3.12 when no
    loop is running; prefer :class:`ThreadLoopRunner`.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
