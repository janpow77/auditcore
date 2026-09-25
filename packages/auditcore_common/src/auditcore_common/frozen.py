"""Read-only copies of JSON data and their mutable counterparts."""

from __future__ import annotations

from types import MappingProxyType


def freeze(value: object) -> object:
    """``dict`` → ``MappingProxyType`` and ``list`` → ``tuple``, recursively; else unchanged."""
    if isinstance(value, dict):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(freeze(v) for v in value)
    return value


def thaw(value: object) -> object:
    """Inverse of :func:`freeze`: ``MappingProxyType`` → ``dict``, ``tuple`` → ``list``."""
    if isinstance(value, MappingProxyType):
        return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw(v) for v in value]
    return value
