"""Typed, path-aware access to JSON objects of the profile file."""

from __future__ import annotations

from typing import cast

JsonObject = dict[str, object]


class ProfileFormatError(ValueError):
    """The file is not a readable profile; the message names the field."""


class Reader:
    """Typed access to one JSON object with German error paths."""

    def __init__(self, data: object, where: str) -> None:
        if not isinstance(data, dict):
            raise ProfileFormatError(f"{where}: Objekt erwartet")
        self.data = cast(JsonObject, data)
        self.where = where

    def sub(self, key: str) -> Reader:
        return Reader(self.data.get(key, {}), f"{self.where}.{key}")

    def _get(self, key: str, default: object) -> object:
        return self.data.get(key, default)

    def integer(self, key: str, default: int | None = None) -> int:
        value = self._get(key, default)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ProfileFormatError(f"{self.where}.{key}: ganze Zahl erwartet")
        return value

    def number(self, key: str, default: float | None = None) -> float:
        value = self._get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ProfileFormatError(f"{self.where}.{key}: Zahl erwartet")
        return float(value)

    def text(self, key: str, default: str | None = None) -> str:
        value = self._get(key, default)
        if not isinstance(value, str):
            raise ProfileFormatError(f"{self.where}.{key}: Text erwartet")
        return value

    def flag(self, key: str, default: bool | None = None) -> bool:
        value = self._get(key, default)
        if not isinstance(value, bool):
            raise ProfileFormatError(f"{self.where}.{key}: wahr/falsch erwartet")
        return value

    def texts(self, key: str, default: list[str] | None = None) -> tuple[str, ...]:
        value = self._get(key, default)
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise ProfileFormatError(f"{self.where}.{key}: Liste von Texten erwartet")
        return tuple(cast(list[str], value))

    def integers(self, key: str, default: list[int] | None = None) -> tuple[int, ...]:
        value = self._get(key, default)
        if not isinstance(value, list) or not all(isinstance(x, int) and not isinstance(x, bool) for x in value):
            raise ProfileFormatError(f"{self.where}.{key}: Liste ganzer Zahlen erwartet")
        return tuple(cast(list[int], value))

    def items(self, key: str) -> list[Reader]:
        value = self._get(key, [])
        if not isinstance(value, list):
            raise ProfileFormatError(f"{self.where}.{key}: Liste erwartet")
        return [Reader(v, f"{self.where}.{key}[{i}]") for i, v in enumerate(value)]
