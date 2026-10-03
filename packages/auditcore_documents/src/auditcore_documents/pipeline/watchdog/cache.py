"""Request-local preparation shared by validation and result assembly."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class PreparedValues:
    """Values live only for one synchronous evaluation; never persist document data."""

    suppliers: dict[str, str] = field(default_factory=dict)
    numeric_text: dict[str, str] = field(default_factory=dict)
    formal: dict[int, tuple[Mapping[str, object], list[str]]] = field(default_factory=dict)


_CURRENT: ContextVar[PreparedValues | None] = ContextVar("watchdog_prepared", default=None)


def current() -> PreparedValues | None:
    """Preparation of the current evaluation, if one is active."""
    return _CURRENT.get()


@contextmanager
def prepared_values() -> Iterator[PreparedValues]:
    """Reuse an enclosing evaluation, and always discard a newly created cache."""
    existing = current()
    if existing is not None:
        yield existing
        return
    values = PreparedValues()
    token = _CURRENT.set(values)
    try:
        yield values
    finally:
        _CURRENT.reset(token)


def prepared_run(function: Callable[P, R]) -> Callable[P, R]:
    """Scope preparation to validation and, when called by the service, its response."""

    @wraps(function)
    def run(*args: P.args, **kwargs: P.kwargs) -> R:
        with prepared_values():
            return function(*args, **kwargs)

    return run
