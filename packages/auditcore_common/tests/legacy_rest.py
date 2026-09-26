"""Verbatim copies of the REST helpers merged into ``auditcore_common.rest`` (oracle).

Copied from janpow77/auditcore@f03aa0e4a1f811b90dd69e9e8846a219937d4289
(``packages/auditcore_sampling`` and ``packages/auditcore_statistics``, ``web``);
the ``_object`` checks from janpow77/auditcore@e5698cfd49ec2d918a7b8fb44e77f8000c607783
(``auditcore_identifiers``) and @2025d08f82663a2a85c1c6ed5325042a3c9012b5
(``auditcore_reporting``, branch of PR #162);
each block names its source file and symbol, ``provenance.json`` lists the git
blobs. Only lines marked ``[adapted]`` differ: class and function names carry a
package prefix, and the per-item parsers ``_item``/``_value`` are the identity,
because only the list checks around them were merged.
"""
# ruff: noqa: E501, UP038

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal

SAMPLING_MAX_BODY_BYTES = 32 * 1024 * 1024
STATISTICS_MAX_BODY_BYTES = 64 * 1024 * 1024
MAX_ITEMS = 200_000
MAX_VALUES = 1_000_000


# packages/auditcore_sampling/src/auditcore_sampling/web/_validate.py :: ContractError
class SamplingContractError(ValueError):  # [adapted] name
    """Request does not satisfy the REST contract."""

    def __init__(self, message: str, *, status: int = 422, code: str = "invalid_input") -> None:
        super().__init__(message)
        self.status = status
        self.code = code

    def to_dict(self) -> dict[str, object]:
        """JSON error body."""
        return {"error": {"code": self.code, "message": str(self)}}


# packages/auditcore_statistics/src/auditcore_statistics/web/analysis.py :: ContractError
class StatisticsContractError(ValueError):  # [adapted] name
    """Request does not satisfy the REST contract."""

    def __init__(self, message: str, *, status: int = 422, code: str = "invalid_input") -> None:
        super().__init__(message)
        self.status = status
        self.code = code

    def to_dict(self) -> dict[str, object]:
        """JSON error body."""
        return {"error": {"code": self.code, "message": str(self)}}


# packages/auditcore_sampling/src/auditcore_sampling/web/_http.py :: Reply
@dataclass(frozen=True)
class SamplingReply:  # [adapted] name
    """Status, body and headers of one response."""

    status: int
    body: bytes
    media_type: str
    headers: dict[str, str]


# packages/auditcore_statistics/src/auditcore_statistics/web/_http.py :: Reply
@dataclass(frozen=True)
class StatisticsReply:  # [adapted] name
    """Status, JSON body and media type of one response."""

    status: int
    body: bytes
    media_type: str = "application/json"


# packages/auditcore_sampling/src/auditcore_sampling/web/_http.py :: _json
def sampling_json(status: int, data: object) -> SamplingReply:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return SamplingReply(status, body, "application/json", {})


# packages/auditcore_statistics/src/auditcore_statistics/web/_http.py :: _json
def statistics_json(status: int, data: object) -> StatisticsReply:
    return StatisticsReply(status, json.dumps(data, ensure_ascii=False).encode("utf-8"))


# packages/auditcore_sampling/src/auditcore_sampling/web/_http.py :: decode
def sampling_decode(raw: bytes, limit: int = SAMPLING_MAX_BODY_BYTES) -> object:
    """Parsed JSON body within the size limit."""
    if len(raw) > limit:
        raise SamplingContractError("Anfrage zu groß.", status=413, code="too_large")
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SamplingContractError("Kein gültiges JSON.", status=400, code="invalid_json") from exc


# packages/auditcore_statistics/src/auditcore_statistics/web/_http.py :: decode
def statistics_decode(raw: bytes, limit: int = STATISTICS_MAX_BODY_BYTES) -> object:
    """JSON body with numbers as exact Decimal/int, within the size limit."""
    if len(raw) > limit:
        raise StatisticsContractError("Anfrage zu groß.", status=413, code="too_large")
    try:
        return json.loads(raw, parse_float=Decimal)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StatisticsContractError(
            "Kein gültiges JSON.", status=400, code="invalid_json"
        ) from exc


# packages/auditcore_sampling/src/auditcore_sampling/web/_http.py :: handle
def sampling_handle(
    handler: Callable[[object], dict[str, object]],  # [adapted] handler instead of name
    raw: bytes,
    limit: int = SAMPLING_MAX_BODY_BYTES,
) -> SamplingReply:
    """Run one POST endpoint and map contract errors to HTTP replies."""
    try:
        payload = sampling_decode(raw, limit)
        return sampling_json(200, handler(payload))  # [adapted] JSON endpoints only
    except SamplingContractError as exc:
        return sampling_json(exc.status, exc.to_dict())


# packages/auditcore_statistics/src/auditcore_statistics/web/_http.py :: handle_analyse
def statistics_handle_analyse(
    analyse: Callable[[object], dict[str, object]],  # [adapted] handler as parameter
    raw: bytes,
    limit: int = STATISTICS_MAX_BODY_BYTES,
) -> StatisticsReply:
    """``POST /analyze`` with contract errors mapped to HTTP replies."""
    try:
        return statistics_json(200, analyse(statistics_decode(raw, limit)))
    except StatisticsContractError as exc:
        return statistics_json(exc.status, exc.to_dict())


# packages/auditcore_sampling/src/auditcore_sampling/web/_validate.py :: choice
def sampling_choice(value: object, name: str, allowed: tuple[str, ...]) -> str:
    """One of the explicitly allowed values."""
    if value not in allowed:
        raise SamplingContractError(f"'{name}' muss einer der Werte {', '.join(allowed)} sein.")
    return str(value)


# packages/auditcore_statistics/src/auditcore_statistics/web/analysis.py :: _field
def statistics_field(body: Mapping[str, object], key: str, allowed: tuple[str, ...]) -> str:
    value = body.get(key)
    if value not in allowed:
        raise StatisticsContractError(f"'{key}' muss einer der Werte {', '.join(allowed)} sein.")
    return str(value)


# packages/auditcore_sampling/src/auditcore_sampling/web/draw.py :: parse_items
def sampling_parse_items(raw: object) -> list[object]:
    """Validated population, at most :data:`MAX_ITEMS` elements."""
    if not isinstance(raw, list) or not raw:
        raise SamplingContractError("'items' muss eine nicht leere Liste sein.")
    if len(raw) > MAX_ITEMS:
        raise SamplingContractError(f"Höchstens {MAX_ITEMS} Elemente je Anfrage.", status=413)
    return list(raw)  # [adapted] _item is the identity


# packages/auditcore_statistics/src/auditcore_statistics/web/analysis.py :: _values
def statistics_values(raw: object) -> list[object]:
    if not isinstance(raw, list) or not raw:
        raise StatisticsContractError("'values' muss eine nicht leere Liste sein.")
    if len(raw) > MAX_VALUES:
        raise StatisticsContractError(f"Höchstens {MAX_VALUES} Werte je Anfrage.", status=413)
    return list(raw)  # [adapted] _value is the identity


# packages/auditcore_identifiers/src/auditcore_identifiers/web/contract.py :: ContractError
class IdentifiersContractError(ValueError):  # [adapted] name
    """Request does not satisfy the contract (status, code, German message)."""

    def __init__(self, message: str, *, status: int = 422, code: str = "invalid_input") -> None:
        super().__init__(message)
        self.status = status
        self.code = code

    def to_dict(self) -> dict[str, object]:
        """JSON error body ``{"error": {"code", "message"}}``."""
        return {"error": {"code": self.code, "message": str(self)}}


# packages/auditcore_reporting/src/auditcore_reporting/web/contract.py :: ContractError
class ReportingContractError(ValueError):  # [adapted] name
    """Request does not satisfy the REST contract (status, code, German message)."""

    def __init__(self, message: str, *, status: int = 422, code: str = "invalid_input") -> None:
        super().__init__(message)
        self.status = status
        self.code = code

    def to_dict(self) -> dict[str, object]:
        """JSON error body ``{"error": {"code", "message"}}``."""
        return {"error": {"code": self.code, "message": str(self)}}


# packages/auditcore_identifiers/src/auditcore_identifiers/web/contract.py :: _object
def identifiers_object(value: object, path: str) -> Mapping[str, object]:  # [adapted] name
    if not isinstance(value, Mapping) or not all(isinstance(k, str) for k in value):
        raise IdentifiersContractError(f"'{path}' muss ein JSON-Objekt sein.")  # [adapted] name
    return value


# packages/auditcore_reporting/src/auditcore_reporting/web/contract.py :: _object
def reporting_object(value: object, path: str) -> Mapping[str, object]:  # [adapted] name
    if not isinstance(value, Mapping) or not all(isinstance(k, str) for k in value):
        raise ReportingContractError(f"'{path}' muss ein JSON-Objekt sein.")  # [adapted] name
    return value
