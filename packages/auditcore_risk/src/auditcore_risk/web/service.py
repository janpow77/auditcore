"""Framework-free handlers of the risk REST API (contract: ``docs/ui/risk-rest.md``).

Each handler takes decoded JSON and returns JSON data or raises
:class:`ApiError` with an HTTP status, a stable code and a German message. The
Starlette app and the FastAPI router only translate HTTP to these calls.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date

from ..engine import Evaluation, evaluate, flatten_record, missing_columns
from ..errors import DependencyError, InputError, ProfileError, RiskError
from ..profiles import RiskProfile, load_profile
from .catalog import list_profiles, profile_detail, rule_inputs, rules_view
from .jsontypes import JsonObject, JsonValue, json_object, json_safe

#: Default upper bound of records per request (configurable per app).
MAX_RECORDS = 20_000
_EVALUATE_KEYS = frozenset(
    {"profile", "records", "columns", "reference_date", "record_key", "flatten", "points"}
)
Record = Mapping[str, object]


class ApiError(Exception):
    """Error answer: HTTP ``status``, machine-readable ``code``, German ``message``."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message

    def to_dict(self) -> JsonObject:
        """Response body ``{"error": {"code": …, "message": …}}``."""
        return {"error": {"code": self.code, "message": self.message}}


@dataclass(frozen=True)
class Limits:
    """Request limits of one app instance."""

    max_records: int = MAX_RECORDS


def _invalid(message: str) -> ApiError:
    return ApiError(400, "invalid_request", message)


def library_error(exc: RiskError) -> ApiError:
    """HTTP answer of a library error (dependency 503, input 400, profile 422)."""
    if isinstance(exc, DependencyError):
        return ApiError(503, exc.code, str(exc))
    if isinstance(exc, InputError):
        return ApiError(400, exc.code, str(exc))
    return ApiError(422, exc.code, str(exc))


def get_profile(profile_id: object, version: object) -> RiskProfile:
    """The explicitly named profile; unknown id/version is a 404, never a default."""
    if not isinstance(profile_id, str) or not isinstance(version, str):
        raise _invalid("Profil braucht 'id' und 'version' als Text.")
    try:
        return load_profile(profile_id, version)
    except ProfileError as exc:
        raise ApiError(404, "profile_not_found", str(exc)) from exc


def handle_profiles() -> JsonObject:
    """``GET /profiles``."""
    return {"profiles": list_profiles()}


def handle_profile(profile_id: str, version: str) -> JsonObject:
    """``GET /profiles/{id}/{version}``."""
    return profile_detail(get_profile(profile_id, version))


def _string_list(value: object, name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise _invalid(f"'{name}' muss eine Liste von Texten sein.")
    return [str(v) for v in value]


def handle_check_columns(profile_id: str, version: str, body: object) -> JsonObject:
    """``POST /profiles/{id}/{version}/check-columns``: consequences of absent columns."""
    profile = get_profile(profile_id, version)
    if not isinstance(body, Mapping):
        raise _invalid("Erwartet wird ein Objekt mit 'columns'.")
    columns = _string_list(body.get("columns"), "columns")
    absent = missing_columns(profile, columns)
    rules: list[JsonValue] = [
        {
            "code": rule.code,
            "label": rule.label,
            "missing": list[JsonValue](absent[rule.code]),
            "when_missing_columns": rule.when_missing_columns,
        }
        for rule in profile.rules
        if rule.code in absent
    ]
    aborts = any(profile.rule(code).when_missing_columns == "error" for code in absent)
    return {
        "profile": json_object(profile.reference),
        "columns": list[JsonValue](columns),
        "complete": not rules,
        "aborts": aborts,
        "rules": rules,
    }


def _records(body: Mapping[str, object], limits: Limits) -> list[Record]:
    records = body.get("records")
    if not isinstance(records, list):
        raise _invalid("'records' muss eine Liste von Objekten sein.")
    if len(records) > limits.max_records:
        raise ApiError(
            413,
            "too_many_records",
            f"Höchstens {limits.max_records} Datensätze je Anfrage ({len(records)} erhalten).",
        )
    rows: list[Record] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise _invalid("Jeder Datensatz muss ein Objekt sein.")
        rows.append(flatten_record(record) if body.get("flatten") is True else dict(record))
    return rows


def _reference_date(value: object) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise _invalid("'reference_date' muss ein ISO-Datum sein.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise _invalid(f"Kein ISO-Datum: {value!r}.") from exc


def _points(value: object) -> dict[str, float] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise _invalid("'points' muss Code → Zahl zuordnen.")
    points: dict[str, float] = {}
    for code, number in value.items():
        if not isinstance(code, str) or isinstance(number, bool):
            raise _invalid("'points' muss Code → Zahl zuordnen.")
        if not isinstance(number, int | float):
            raise _invalid("'points' muss Code → Zahl zuordnen.")
        points[code] = number
    return points


def _check_body(body: object) -> Mapping[str, object]:
    if not isinstance(body, Mapping):
        raise _invalid("Erwartet wird ein JSON-Objekt.")
    unknown = sorted(str(k) for k in set(body) - _EVALUATE_KEYS)
    if unknown:
        raise _invalid(f"Unbekannte Felder: {', '.join(unknown)}.")
    if not isinstance(body.get("profile"), Mapping):
        raise _invalid("'profile' mit 'id' und 'version' fehlt.")
    key = body.get("record_key")
    if key is not None and not isinstance(key, str):
        raise _invalid("'record_key' muss Text sein.")
    return body


def _profile_of(body: Mapping[str, object]) -> RiskProfile:
    spec = body["profile"]
    if not isinstance(spec, Mapping):
        raise _invalid("'profile' mit 'id' und 'version' fehlt.")
    return get_profile(spec.get("id"), spec.get("version"))


def handle_evaluate(body: object, limits: Limits | None = None) -> JsonObject:
    """``POST /evaluate``: evaluate one explicitly named profile over the records."""
    checked = _check_body(body)
    profile = _profile_of(checked)
    records = _records(checked, limits or Limits())
    raw_columns = checked.get("columns")
    columns = None if raw_columns is None else _string_list(raw_columns, "columns")
    try:
        evaluation = evaluate(
            records,
            profile,
            columns=columns,
            reference_date=_reference_date(checked.get("reference_date")),
            points=_points(checked.get("points")),
        )
    except RiskError as exc:
        raise library_error(exc) from exc
    present = columns if columns is not None else _union(records)
    key = checked.get("record_key")
    result = json_object(evaluation.to_dict())
    result["records"] = _record_views(evaluation, result, profile, records, key)
    result["rules"] = rules_view(profile)
    result["columns"] = list[JsonValue](present)
    result["missing_columns"] = json_object(missing_columns(profile, present))
    return result


def _union(records: Sequence[Record]) -> list[str]:
    seen: dict[str, None] = {}
    for record in records:
        for key in record:
            seen.setdefault(str(key), None)
    return list(seen)


def _record_views(
    evaluation: Evaluation,
    result: JsonObject,
    profile: RiskProfile,
    records: Sequence[Record],
    record_key: object,
) -> list[JsonValue]:
    """Records of ``to_dict()`` plus ``key`` and the input values per hit/undetermined rule."""
    inputs = rule_inputs(profile)
    raw = result.get("records")
    views = raw if isinstance(raw, list) else []
    out: list[JsonValue] = []
    for view, record_result in zip(views, evaluation.records, strict=True):
        if not isinstance(view, dict):
            continue
        record = records[record_result.index]
        shown = [*record_result.codes, *record_result.undetermined]
        values = {c: json_object({n: record.get(n) for n in inputs.get(c, [])}) for c in shown}
        view["key"] = json_safe(record.get(record_key)) if isinstance(record_key, str) else None
        view["inputs"] = dict[str, JsonValue](values)
        hits = view.get("hits")
        for hit in hits if isinstance(hits, list) else []:
            if isinstance(hit, dict) and isinstance(hit.get("code"), str):
                hit["inputs"] = values.get(str(hit["code"]), {})
        out.append(view)
    return out
