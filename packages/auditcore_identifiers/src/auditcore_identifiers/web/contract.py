"""REST contract ``identifiers_ui/1``: catalogue, single and batch checks (framework-free).

Every request names its profile explicitly; the catalogue recommends
``strict`` but nothing is defaulted silently. Invalid identifiers are results,
not errors: only requests that break the contract raise :class:`ContractError`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from auditcore_common import rest

from .. import __version__
from ..profiles import PROFILES, STRICT, Profile, UnsupportedKindError
from ..result import CheckResult, IdentifierKind, Status
from .labels import DETAIL_LABELS, KIND_LABELS, REASON_LABELS, VALUE_LABELS

CONTRACT = "identifiers_ui/1"
LIBRARY = f"auditcore_identifiers {__version__}"
Json = dict[str, object]


@dataclass(frozen=True)
class Limits:
    """Request limits of the contract (reported in the catalogue)."""

    max_items: int = 10_000
    max_value_length: int = 200
    max_body_bytes: int = 4 * 1024 * 1024


class ContractError(rest.ContractError):
    """Request does not satisfy the ``identifiers_ui/1`` contract (status, code, ``to_dict``)."""


def catalogue(limits: Limits | None = None) -> Json:
    """``GET /catalogue``: kinds, profiles, reason and detail labels, limits."""
    limits = limits or Limits()
    return {
        "contract": CONTRACT,
        "library": LIBRARY,
        "recommended_profile": STRICT,
        "kinds": [
            {"id": kind.value, "label": label, "description": text, "country": country}
            for kind, (label, text, country) in KIND_LABELS.items()
        ],
        "profiles": [_profile(p) for p in PROFILES.values()],
        "reasons": [{"id": r.value, "label": text} for r, text in REASON_LABELS.items()],
        "detail_labels": dict(DETAIL_LABELS),
        "value_labels": dict(VALUE_LABELS),
        "limits": {
            "max_items": limits.max_items,
            "max_value_length": limits.max_value_length,
            "max_body_bytes": limits.max_body_bytes,
        },
    }


def _profile(profile: Profile) -> Json:
    return {
        "id": profile.name,
        "title": profile.title,
        "rationale": profile.rationale,
        "origin": profile.origin,
        "legacy": profile.legacy,
        "kinds": [kind.value for kind in IdentifierKind if kind in profile.checkers],
    }


def _profile_of(body: Mapping[str, object]) -> Profile:
    name = body.get("profile")
    if not isinstance(name, str) or name not in PROFILES:
        raise ContractError(
            f"'profile' muss eines der Profile {', '.join(PROFILES)} sein.", code="unknown_profile"
        )
    return PROFILES[name]


def _kind(value: object, path: str) -> IdentifierKind:
    if isinstance(value, str) and value in {kind.value for kind in IdentifierKind}:
        return IdentifierKind(value)
    allowed = ", ".join(kind.value for kind in IdentifierKind)
    raise ContractError(f"'{path}' muss eine der Arten {allowed} sein.", code="unknown_kind")


def _text(body: Mapping[str, object], key: str, path: str, limit: int) -> str | None:
    value = body.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ContractError(f"'{path}' muss Text oder null sein.")
    if len(value) > limit:
        raise ContractError(f"'{path}' ist länger als {limit} Zeichen.")
    return value


def result_dict(result: CheckResult) -> Json:
    """``CheckResult.to_dict()`` plus German labels of kind and reason."""
    data: Json = dict(result.to_dict())
    data["kind_label"] = KIND_LABELS[result.kind][0]
    data["reason_label"] = None if result.reason is None else REASON_LABELS[result.reason]
    return data


def _run(profile: Profile, body: Mapping[str, object], path: str, limits: Limits) -> Json:
    prefix = "" if path == "Anfrage" else f"{path}."
    kind = _kind(body.get("kind"), f"{prefix}kind")
    value = _text(body, "value", f"{prefix}value", limits.max_value_length)
    country = _text(body, "country", f"{prefix}country", 3)
    try:
        return result_dict(profile.check(kind, value, country))
    except UnsupportedKindError as exc:
        raise ContractError(
            f"Profil {profile.name} prüft keine Kennungsart {kind.value}.",
            code="unsupported_kind",
        ) from exc


def check_one(payload: object, limits: Limits | None = None) -> Json:
    """``POST /check``: one value of one kind under the named profile."""
    body = rest.json_object(payload, "Anfrage", error=ContractError)
    profile = _profile_of(body)
    return {"contract": CONTRACT, "result": _run(profile, body, "Anfrage", limits or Limits())}


def _reference(entry: Mapping[str, object], index: int) -> str:
    ref = entry.get("ref")
    if ref is None:
        return str(index + 1)
    if isinstance(ref, bool) or not isinstance(ref, (str, int)):
        raise ContractError(f"'items[{index}].ref' muss Text oder ganze Zahl sein.")
    return str(ref)


def _batch_entry(profile: Profile, raw: object, index: int, limits: Limits) -> Json:
    path = f"items[{index}]"
    entry = rest.json_object(raw, path, error=ContractError)
    ref = _reference(entry, index)
    try:
        return {"index": index, "ref": ref, "error": None, **_run(profile, entry, path, limits)}
    except ContractError as exc:
        if exc.code not in {"unsupported_kind", "unknown_kind"}:
            raise
        return {"index": index, "ref": ref, "error": exc.to_dict()["error"]}


def _summary(results: list[Json]) -> Json:
    statuses = [r.get("status") for r in results]
    return {
        "total": len(results),
        "valid": statuses.count(Status.VALID.value),
        "invalid": statuses.count(Status.INVALID.value),
        "missing": statuses.count(Status.MISSING.value),
        "not_checked": sum(1 for r in results if r["error"] is not None),
    }


def check_batch(payload: object, limits: Limits | None = None) -> Json:
    """``POST /check/batch``: many values (e.g. from a table) under one profile.

    Rows whose kind is unknown or not offered by the profile are reported per
    row (``error``) instead of rejecting the whole table.
    """
    limits = limits or Limits()
    body = rest.json_object(payload, "Anfrage", error=ContractError)
    profile = _profile_of(body)
    items = body.get("items")
    if not isinstance(items, list) or not items:
        raise ContractError("'items' muss eine nicht leere Liste sein.")
    if len(items) > limits.max_items:
        raise ContractError(
            f"'items' hat {len(items)} Einträge; höchstens {limits.max_items} je Anfrage.",
            status=413,
            code="too_large",
        )
    results = [_batch_entry(profile, raw, i, limits) for i, raw in enumerate(items)]
    return {
        "contract": CONTRACT,
        "profile": profile.name,
        "results": results,
        "summary": _summary(results),
    }
