"""Lazy import of optional extras with the caller's own error type and message."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from types import ModuleType


def require_module(name: str, error: Callable[[str], Exception], message: str) -> ModuleType:
    """Import ``name`` or raise ``error(message)`` chained to the ``ImportError``.

    Equivalent to the ``try: import x / except ImportError: raise Error(...) from exc``
    blocks of the domain packages; ``name`` may be a submodule (``"rapidfuzz.fuzz"``).
    """
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise error(message) from exc
