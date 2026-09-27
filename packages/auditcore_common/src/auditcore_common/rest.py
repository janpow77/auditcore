"""Framework-neutral parts of the small JSON REST contracts of the domain packages.

The Starlette and FastAPI adapters of a package turn a :class:`Reply` into a
framework response; everything before that (body size limit, JSON decoding,
contract errors, JSON replies, typical field checks) lives here and needs no
web framework. Each package keeps its own :class:`ContractError` subclass so
that hosts can tell the contracts apart; every helper takes that class as
``error`` and raises it with the unchanged German messages.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

JSON_MEDIA_TYPE = "application/json"


class ContractError(ValueError):
    """Request does not satisfy the REST contract."""

    def __init__(self, message: str, *, status: int = 422, code: str = "invalid_input") -> None:
        super().__init__(message)
        self.status = status
        self.code = code

    def to_dict(self) -> dict[str, object]:
        """JSON error body."""
        return {"error": {"code": self.code, "message": str(self)}}


@dataclass(frozen=True)
class Reply:
    """Status, body, media type and extra headers of one response."""

    status: int
    body: bytes
    media_type: str = JSON_MEDIA_TYPE
    headers: Mapping[str, str] = field(default_factory=dict)


def json_reply(status: int, data: object) -> Reply:
    """``data`` as UTF-8 JSON (``ensure_ascii=False``) with ``status``."""
    return Reply(status, json.dumps(data, ensure_ascii=False).encode("utf-8"))


def decode_body(
    raw: bytes,
    limit: int,
    *,
    error: type[ContractError] = ContractError,
    parse_float: Callable[[str], object] | None = None,
    too_large_code: str = "too_large",
    invalid_json_code: str = "invalid_json",
) -> object:
    """Parsed JSON body; ``413 too_large`` above ``limit`` bytes, ``400 invalid_json`` else.

    ``parse_float`` is passed to :func:`json.loads` (e.g. ``Decimal`` for exact
    digits). ``too_large_code``/``invalid_json_code`` keep the error codes of a
    contract that names them differently (geo: ``zu_gross``/``ungueltiges_json``).
    """
    if len(raw) > limit:
        raise error("Anfrage zu groß.", status=413, code=too_large_code)
    try:
        return json.loads(raw, parse_float=parse_float)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise error("Kein gültiges JSON.", status=400, code=invalid_json_code) from exc


def guarded(action: Callable[[], Reply], *, error: type[ContractError] = ContractError) -> Reply:
    """``action()``, or the JSON error body of a raised ``error`` with its status."""
    try:
        return action()
    except error as exc:
        return json_reply(exc.status, exc.to_dict())


def json_object(
    value: object, path: str, *, error: type[ContractError] = ContractError
) -> Mapping[str, object]:
    """``value`` if it is a JSON object with string keys, else ``error`` naming ``path``."""
    if not isinstance(value, Mapping) or not all(isinstance(k, str) for k in value):
        raise error(f"'{path}' muss ein JSON-Objekt sein.")
    return value


def choice(
    value: object,
    name: str,
    allowed: tuple[str, ...],
    *,
    error: type[ContractError] = ContractError,
) -> str:
    """``value`` if it is one of the explicitly ``allowed`` values."""
    if value not in allowed:
        raise error(f"'{name}' muss einer der Werte {', '.join(allowed)} sein.")
    return str(value)


def bounded_list(
    raw: object,
    name: str,
    maximum: int,
    noun: str,
    *,
    error: type[ContractError] = ContractError,
) -> list[object]:
    """A non-empty JSON list of at most ``maximum`` entries (``413`` above)."""
    if not isinstance(raw, list) or not raw:
        raise error(f"'{name}' muss eine nicht leere Liste sein.")
    if len(raw) > maximum:
        raise error(f"Höchstens {maximum} {noun} je Anfrage.", status=413)
    return raw
