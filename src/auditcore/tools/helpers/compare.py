"""Compare the outcome of a helper call with the expectation of a contract case."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from auditcore.tools.helpers.model import as_dict, as_list

EMPTY_MARKERS = ("$undefined", "$nan")


@dataclass(frozen=True)
class Outcome:
    """What a helper returned (encoded JSON value) or the error it raised."""

    value: object = None
    error: str | None = None

    @classmethod
    def from_json(cls, data: object) -> Outcome:
        """Decode a runner result entry ``{"value": ...}`` or ``{"error": ...}``."""
        entry = as_dict(data)
        if "error" in entry:
            return cls(error=str(entry["error"]))
        return cls(value=entry.get("value"))


def show(value: object) -> str:
    """Short, readable rendering of an encoded value for reports."""
    marker = as_dict(value)
    if "$undefined" in marker:
        return "undefined"
    if "$nan" in marker:
        return "NaN"
    for key in ("$decimal", "$date", "$error"):
        if key in marker:
            return f"{key[1:]}({marker[key]})"
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= 80 else text[:77] + "..."


def _is_empty(outcome: Outcome) -> bool:
    marker = as_dict(outcome.value)
    return (
        outcome.error is not None
        or outcome.value is None
        or any(k in marker for k in EMPTY_MARKERS)
    )


def as_decimal(value: object) -> Decimal | None:
    """Interpret a returned number, Decimal marker or numeric string."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = value if isinstance(value, str) else as_dict(value).get("$decimal")
    if not isinstance(text, str):
        return None
    try:
        return Decimal(text.strip())
    except InvalidOperation:
        return None


def _actual(outcome: Outcome) -> str:
    return f"Ausnahme „{outcome.error}“" if outcome.error is not None else show(outcome.value)


def _decimal(expect: dict[str, object], outcome: Outcome) -> tuple[bool, str]:
    if expect.get("invalid") is True:
        if _is_empty(outcome):
            return True, "abgelehnt"
        return False, f"{_actual(outcome)} statt Ablehnung"
    wanted = as_decimal(expect.get("value"))
    got = None if _is_empty(outcome) else as_decimal(outcome.value)
    if wanted is not None and got is not None and got == wanted:
        return True, str(got)
    return False, f"{_actual(outcome)} statt {expect.get('value')}"


def _text(expect: dict[str, object], outcome: Outcome) -> tuple[bool, str]:
    wanted = expect.get("value")
    if outcome.error is None and outcome.value == wanted:
        return True, show(wanted)
    return False, f"{_actual(outcome)} statt {show(wanted)}"


def _boolean(expect: dict[str, object], outcome: Outcome) -> tuple[bool, str]:
    wanted = expect.get("value")
    if outcome.error is None and isinstance(outcome.value, bool) and outcome.value == wanted:
        return True, show(wanted)
    return False, f"{_actual(outcome)} statt {show(wanted)}"


def _contains(expect: dict[str, object], outcome: Outcome) -> tuple[bool, str]:
    if "value" in expect:
        return _text(expect, outcome)
    text = outcome.value if isinstance(outcome.value, str) and outcome.error is None else None
    if text is None:
        return False, f"{_actual(outcome)} statt Text"
    missing = [str(item) for item in as_list(expect.get("contains")) if str(item) not in text]
    forbidden = [str(item) for item in as_list(expect.get("not_contains")) if str(item) in text]
    if missing or forbidden:
        parts = [f"fehlt „{m}“" for m in missing] + [f"enthält „{f}“" for f in forbidden]
        return False, f"{show(text)}: " + ", ".join(parts)
    return True, show(text)


def normalise_csv(text: str) -> str:
    """Unify line endings and drop one trailing line break."""
    unified = text.replace("\r\n", "\n")
    return unified[:-1] if unified.endswith("\n") else unified


def _csv(expect: dict[str, object], outcome: Outcome) -> tuple[bool, str]:
    wanted = expect.get("value")
    got = outcome.value if outcome.error is None else None
    if (
        isinstance(got, str)
        and isinstance(wanted, str)
        and normalise_csv(got) == normalise_csv(wanted)
    ):
        return True, "gleich"
    return False, f"{_actual(outcome)} statt {show(wanted)}"


COMPARATORS: dict[str, Callable[[dict[str, object], Outcome], tuple[bool, str]]] = {
    "decimal": _decimal,
    "text": _text,
    "boolean": _boolean,
    "text-contains": _contains,
    "csv": _csv,
}


def compare(result: str, expect: dict[str, object], outcome: Outcome) -> tuple[bool, str]:
    """Return ``(passed, detail)`` for one case."""
    return COMPARATORS[result](expect, outcome)
