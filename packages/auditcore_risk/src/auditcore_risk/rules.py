"""Rule kinds: the reusable mechanics behind every profile rule.

A rule kind is pure mechanics. Every fachliche setting — amounts, thresholds,
proximity, patterns, minimum counts, the name-matching profile and scorer —
comes from the profile parameters; there are no hidden defaults. Each kind
returns, per record, a flag (``True``/``False``, or ``None`` if the record
cannot be decided), the evidence that led to it and a German reason.

The kinds live in :mod:`.amount_rules`, :mod:`.field_rules`,
:mod:`.group_rules`, :mod:`.invoice_rules` and :mod:`.score_rules`; this
module holds the name matching, the registry :data:`KINDS` and
:func:`validate_params`.
"""

from __future__ import annotations

from importlib.util import find_spec
from typing import Any

from .amount_rules import (
    amount_with_marker,
    balance_mismatch,
    identifier_state,
    missing_procurement,
    near_threshold,
    nonzero_without_text,
    round_multiple,
)
from .base import Context, JsonObject, Kind, KindRun, Outcome, Table, need
from .errors import DependencyError
from .field_rules import (
    date_before,
    duplicate_key,
    missing_value,
    numeric_compare,
    ratio_history,
    text_equals,
)
from .group_rules import counterparty_concentration, leave_one_out_rate, top_share
from .invoice_rules import INVOICE_KINDS
from .rule_checks import COMMON_CHECKS, KIND_CHECKS
from .score_rules import SCORE_KINDS
from .values import is_missing

# --------------------------------------------------------------------------- name matching


def _entity_profile(p: JsonObject, ctx: Context) -> Any:
    """Normalization profile of ``auditcore_entity_matching`` (extra ``fuzzy``), cached.

    Typed ``Any``: the profile class belongs to a package imported lazily only.
    """
    if find_spec("rapidfuzz") is None:
        raise DependencyError("Der Namensabgleich verlangt 'auditcore_risk[fuzzy]' (rapidfuzz).")
    from auditcore_entity_matching import load_profile

    spec = p["normalization"]
    key = ("entity", spec["profile"], spec["version"])
    if key not in ctx.cache:
        ctx.cache[key] = load_profile(spec["profile"], spec["version"])
    return ctx.cache[key]


def pair_similarity(
    p: JsonObject, raw_a: object, raw_b: object, ctx: Context
) -> tuple[float, str, str, str]:
    """Score, method and both comparison forms of one name pair (``str()`` like the source)."""
    from auditcore_entity_matching import normalize, pair_score

    profile = _entity_profile(p, ctx)
    minimum = int(p["min_length"])
    a = normalize(None if raw_a is None else str(raw_a), profile)
    b = normalize(None if raw_b is None else str(raw_b), profile)
    if not a or not b or len(a) < minimum or len(b) < minimum:
        return 0.0, "zu kurz", a, b
    if a in b or b in a:
        return float(p["containment_score"]), "enthalten", a, b
    return pair_score(a, b, p["scorer"]) / float(p["scale"]), str(p["scorer"]), a, b


def name_similarity(p: JsonObject, table: Table, ctx: Context) -> Outcome:
    """Beneficiary and contractor name match (or a pre-computed override column)."""
    profile = _entity_profile(p, ctx)
    override = (
        p["override_field"] if p["override_field"] and table.has(p["override_field"]) else None
    )
    out = Outcome.constant(len(table), False)
    scores: list[float] = []
    for i in range(len(table)):
        score, how, a, b = pair_similarity(
            p, table.value(i, p["left_field"]), table.value(i, p["right_field"]), ctx
        )
        scores.append(score)
        if override is not None:
            value = table.value(i, override)
            flag = False if is_missing(value) else bool(value)
            basis = "übernommene Vorberechnung"
        else:
            flag = score >= float(p["threshold"])
            basis = f"Ähnlichkeit {score:.4f} ≥ {p['threshold']}"
        out.flags[i] = flag
        if flag:
            out.reasons[i] = (
                f"Begünstigter und Auftragnehmer stimmen überein ({basis}; "
                f"Vergleichsform {a!r} / {b!r})."
            )
            out.evidence[i] = {
                "left": a,
                "right": b,
                "score": score,
                "method": how,
                "override_field": override,
                "normalization": dict(profile.reference),
            }
    out.values[p["value_name"]] = scores
    return out


# --------------------------------------------------------------------------- registry

_AMOUNT = frozenset({"parse", "missing_value"})
# Fehlender Betrag → unbestimmt mit dieser Begründung (verlangt missing_value null).
_MISSING_AMOUNT = frozenset({"missing_amount_reason"})


def _record(run: KindRun, *required: str, optional: frozenset[str] = frozenset()) -> Kind:
    return Kind("record", frozenset(required), optional, run)


def _amount_record(run: KindRun, *required: str, optional: frozenset[str] = frozenset()) -> Kind:
    return Kind("record", frozenset(required) | _AMOUNT, optional, run)


KINDS: dict[str, Kind] = {
    "round_multiple": _amount_record(round_multiple, "field", "multiple", "positive_only"),
    "near_threshold": _amount_record(
        near_threshold, "field", "thresholds", "lower", "count", optional=_MISSING_AMOUNT
    ),
    "missing_procurement": _amount_record(
        missing_procurement,
        "amount_field",
        "amount_gt",
        "id_field",
        "id_column_missing",
        "blank_values",
        "blank_casefold",
        "placeholder_pattern",
        "relevance",
        optional=_MISSING_AMOUNT,
    ),
    "name_similarity": _record(
        name_similarity,
        "left_field",
        "right_field",
        "normalization",
        "min_length",
        "containment_score",
        "scorer",
        "scale",
        "threshold",
        "override_field",
        "value_name",
    ),
    "counterparty_concentration": _amount_record(
        counterparty_concentration,
        "amount_field",
        "payee_field",
        "case_field",
        "group_field",
        "relevance",
        "pair",
        "group",
    ),
    "ratio_history": _record(ratio_history, "total_field", "part_field", "ratio_gt", "total_min"),
    "leave_one_out_rate": _amount_record(
        leave_one_out_rate,
        "group_field",
        "case_field",
        "amount_field",
        "deduction_field",
        "deduction_missing_value",
        "rate_gt",
        "percent_factor",
        "min_cases_gt",
        optional=frozenset({"propagation"}),
    ),
    "numeric_compare": _record(
        numeric_compare, "field", "column_missing_value", "missing_value", "op", "value"
    ),
    "text_equals": _record(text_equals, "field", "column_missing_value", "value"),
    "missing_value": _record(missing_value, "field"),
    "date_before": _record(date_before, "field", "before_field"),
    "duplicate_key": _record(duplicate_key, "fields"),
    "nonzero_without_text": _amount_record(nonzero_without_text, "amount_field", "text_field"),
    "balance_mismatch": _amount_record(balance_mismatch, "minuend", "subtrahends", "tolerance"),
    "amount_with_marker": _amount_record(
        amount_with_marker,
        "amount_field",
        "amount_gt",
        "marker_field",
        "marker_pattern",
        "lowercase",
    ),
    "top_share": Kind(
        "dataset", frozenset({"group_field", "amount_field", "share_ge"}), frozenset(), top_share
    ),
}

KINDS.update(INVOICE_KINDS)
KINDS.update(SCORE_KINDS)


def validate_params(kind: str, params: JsonObject, where: str) -> None:
    """Exact parameter set of the kind plus the value checks that matter for safety."""
    spec = KINDS[kind]
    keys = set(params)
    need(spec.required <= keys, where, f"fehlende Parameter {sorted(spec.required - keys)}")
    unknown = keys - spec.required - spec.optional
    need(not unknown, where, f"unbekannte Parameter {sorted(unknown)}")
    if spec.validate is not None:
        spec.validate(params, where)
        return
    for check in COMMON_CHECKS:
        check(params, where)
    kind_check = KIND_CHECKS.get(kind)
    if kind_check is not None:
        kind_check(params, where)


__all__ = ["KINDS", "identifier_state", "pair_similarity", "validate_params"]
