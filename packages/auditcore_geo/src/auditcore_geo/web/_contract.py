"""Request validation shared by the geo REST contract (framework-free).

Every rejected request raises :class:`ContractError` with an HTTP status and
a German message naming the field path; nothing is silently replaced by a
default.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from ..distanz import KUGELPROFILE, Kugelprofil
from ..koordinaten import Punkt


class ContractError(ValueError):
    """Anfrage erfüllt den REST-Vertrag nicht (Status, Code, deutsche Meldung)."""

    def __init__(
        self, message: str, *, status: int = 422, code: str = "ungueltige_eingabe"
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code

    def to_dict(self) -> dict[str, object]:
        """JSON-Fehlerkörper ``{"error": {"code", "message"}}``."""
        return {"error": {"code": self.code, "message": str(self)}}


@dataclass(frozen=True)
class Body:
    """A JSON object of the request with typed, path-aware field access."""

    data: Mapping[str, object]
    path: str = "Anfrage"

    @classmethod
    def of(cls, value: object, path: str = "Anfrage") -> Body:
        """Wrap a JSON object with string keys or reject the value."""
        if not isinstance(value, Mapping) or not all(isinstance(k, str) for k in value):
            raise ContractError(f"'{path}' muss ein JSON-Objekt sein.")
        return cls(value, path)

    def name(self, key: str) -> str:
        """Field path for messages."""
        return key if self.path == "Anfrage" else f"{self.path}.{key}"

    def value(self, key: str) -> object:
        """A mandatory field; missing fields are never defaulted."""
        found = self.data.get(key)
        if found is None:
            raise ContractError(f"Feld '{self.name(key)}' fehlt.")
        return found

    def has(self, key: str) -> bool:
        """Whether an optional field is present (``null`` counts as absent)."""
        return self.data.get(key) is not None

    def child(self, key: str) -> Body:
        """A nested JSON object."""
        return Body.of(self.value(key), self.name(key))

    def number(self, key: str, *, minimum: float | None = None) -> float:
        """A finite JSON number (no booleans, no strings)."""
        found = self.value(key)
        if isinstance(found, bool) or not isinstance(found, (int, float)):
            raise ContractError(f"'{self.name(key)}' muss eine endliche Zahl sein.")
        number = float(found)
        if not math.isfinite(number):
            raise ContractError(f"'{self.name(key)}' muss eine endliche Zahl sein.")
        if minimum is not None and number < minimum:
            raise ContractError(f"'{self.name(key)}' darf nicht kleiner als {minimum:g} sein.")
        return number

    def integer(self, key: str, low: int, high: int) -> int:
        """A JSON integer within ``low..high``."""
        found = self.value(key)
        if isinstance(found, bool) or not isinstance(found, int) or not low <= found <= high:
            raise ContractError(f"'{self.name(key)}' muss eine ganze Zahl {low}..{high} sein.")
        return found

    def flag(self, key: str) -> bool:
        """A JSON boolean."""
        found = self.value(key)
        if not isinstance(found, bool):
            raise ContractError(f"'{self.name(key)}' muss true oder false sein.")
        return found

    def text(self, key: str, *, max_length: int = 500) -> str:
        """A non-empty JSON string of bounded length."""
        found = self.value(key)
        if not isinstance(found, str) or not found.strip():
            raise ContractError(f"'{self.name(key)}' muss ein nichtleerer Text sein.")
        if len(found) > max_length:
            raise ContractError(f"'{self.name(key)}' ist länger als {max_length} Zeichen.")
        return found.strip()

    def choice(self, key: str, allowed: Mapping[str, object] | tuple[str, ...]) -> str:
        """One of the allowed keys; the message lists them."""
        found = self.value(key)
        if not isinstance(found, str) or found not in allowed:
            raise ContractError(
                f"Unbekannter Wert {found!r} für '{self.name(key)}'; "
                f"erlaubt: {', '.join(sorted(allowed))}.",
                code="profil_fehler",
            )
        return found

    def objects(self, key: str, limit: int) -> list[Body]:
        """A JSON array of objects with at most ``limit`` entries."""
        found = self.value(key)
        if not isinstance(found, list):
            raise ContractError(f"'{self.name(key)}' muss eine Liste sein.")
        if len(found) > limit:
            raise ContractError(
                f"'{self.name(key)}' hat {len(found)} Einträge; höchstens {limit} je Anfrage.",
                status=413,
                code="zu_gross",
            )
        return [Body.of(entry, f"{self.name(key)}[{i}]") for i, entry in enumerate(found)]

    def point(self, key: str | None = None) -> Punkt:
        """``{"lat": …, "lon": …}``; named axes avoid any axis-order guessing."""
        body = self if key is None else self.child(key)
        return Punkt(lat=body.number("lat"), lon=body.number("lon"))

    def earth_model(self) -> Kugelprofil:
        """The explicitly named earth model (decision D1: no silent default)."""
        return KUGELPROFILE[self.choice("erdmodell", tuple(KUGELPROFILE))]
