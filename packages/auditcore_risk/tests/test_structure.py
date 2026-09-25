"""The module structure after the 0.3.1 refactoring keeps every contract.

* Old import paths stay valid (``rules``, ``engine``, ``fraud``, ``profiles``).
* The rule registry keeps its kinds, order and parameter sets.
* Profile validation raises the same first error for every malformed document;
  the expected messages below were recorded from auditcore_risk 0.3.0.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from auditcore_risk import ProfileError, profile_from_dict
from auditcore_risk.fraud import fraud_profile_from_dict

SRC = Path(__file__).parents[1] / "src" / "auditcore_risk"
#: Messages of the first validation error per case, recorded by running the cases
#: below against auditcore_risk 0.3.0 (before the module split).
RECORDED: dict[str, dict[str, str]] = json.loads(
    (Path(__file__).parent / "fixtures" / "validation_errors_0.3.0.json").read_text()
)


def _raw(folder: str, name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((SRC / folder / f"{name}.json").read_text())
    return data


def test_old_import_paths_remain_available() -> None:
    from auditcore_risk import engine, fraud, profiles, rules

    for name in ("KINDS", "validate_params", "identifier_state", "pair_similarity", "find_spec"):
        assert hasattr(rules, name), name
    for name in (
        "LIBRARY",
        "DatasetFinding",
        "Evaluation",
        "FlagHit",
        "RecordResult",
        "evaluate",
        "flatten_record",
        "identifier_missing",
        "missing_columns",
        "name_similarity",
    ):
        assert hasattr(engine, name), name
    for name in (
        "SCHEMA",
        "FRAUD_KINDS",
        "FraudProfile",
        "fraud_profile_from_dict",
        "load_fraud_profile",
        "available_fraud_profiles",
        "score_signals",
        "SignalAssessment",
        "select_contracts",
        "assess_contractor",
        "TedAssessment",
        "DuplicateMatch",
        "exact_duplicates",
        "fuzzy_duplicates",
        "find_duplicates",
        "names_similar",
        "parse_date",
    ):
        assert hasattr(fraud, name), name
    for name in (
        "SCHEMA",
        "STATUSES",
        "SEVERITIES",
        "Rule",
        "RiskProfile",
        "fingerprint",
        "check_template",
        "profile_from_dict",
        "load_profile",
        "available_profiles",
    ):
        assert hasattr(profiles, name), name


#: Kinds in registry order with (scope, required, optional, own validator) as in 0.3.0.
REGISTRY = [
    "round_multiple",
    "near_threshold",
    "missing_procurement",
    "name_similarity",
    "counterparty_concentration",
    "ratio_history",
    "leave_one_out_rate",
    "numeric_compare",
    "text_equals",
    "missing_value",
    "date_before",
    "duplicate_key",
    "nonzero_without_text",
    "balance_mismatch",
    "amount_with_marker",
    "top_share",
    "amount_or_statistic",
    "share_above",
    "all_missing",
    "round_amount_terms",
    "date_outside_range",
    "text_patterns",
    "names_differ",
    "identifier_equal",
    "split_window",
    "truthy_all",
    "text_in_set",
    "number_range",
    "set_overlap",
]


def test_registry_keeps_kinds_and_their_checks() -> None:
    from auditcore_risk.rule_checks import KIND_CHECKS
    from auditcore_risk.rules import KINDS

    assert list(KINDS) == REGISTRY
    assert set(KIND_CHECKS) <= set(KINDS)
    # Kinds with their own validator never reach the common checks.
    assert all(KINDS[kind].validate is None for kind in KIND_CHECKS)
    assert KINDS["top_share"].scope == "dataset"
    assert {k for k, v in KINDS.items() if v.derives_severity} == {"round_amount_terms"}
    optional = {k: v.optional for k, v in KINDS.items() if v.optional}
    assert optional == {
        "near_threshold": frozenset({"missing_amount_reason"}),
        "missing_procurement": frozenset({"missing_amount_reason"}),
        "leave_one_out_rate": frozenset({"propagation"}),
        "split_window": frozenset({"procurement_eu"}),
    }


def test_red_flag_entry_keeps_the_source_keys() -> None:
    from auditcore_risk import load_profile
    from auditcore_risk.summary import red_flag_entry

    rule = load_profile("riskanalysis.legacy", "b5c523bf7eaa").rules[0]
    entry = red_flag_entry(rule, 1, 3, 12.345)
    assert list(entry) == ["code", "bezeichnung", "treffer", "basis", "anteil_prozent", "volumen"]
    assert entry["anteil_prozent"] == 33.33 and entry["volumen"] == 12.35
    assert red_flag_entry(rule, 0, 0, 0.0)["anteil_prozent"] == 0.0


# --------------------------------------------------------------------------- validation order

Mutation = Callable[[dict[str, Any]], None]


def _rule(data: dict[str, Any], code: str) -> dict[str, Any]:
    rule: dict[str, Any] = next(r for r in data["rules"] if r["code"] == code)
    return rule


def _set(*path: str, value: Any) -> Mutation:
    def apply(data: dict[str, Any]) -> None:
        target: Any = data
        for key in path[:-1]:
            target = _rule(target, key[1:]) if key.startswith("@") else target[key]
        target[path[-1]] = value

    return apply


def _drop(*path: str) -> Mutation:
    def apply(data: dict[str, Any]) -> None:
        target: Any = data
        for key in path[:-1]:
            target = _rule(target, key[1:]) if key.startswith("@") else target[key]
        del target[path[-1]]

    return apply


LEGACY = ("profile_data", "riskanalysis.legacy-b5c523bf7eaa")
FLOWSTAT = ("profile_data", "audit_designer.flowstat_belegliste-1254591156d3")
CHECKER = ("profile_data", "flowinvoice.risk_checker-2026.09.3")
RBVK = ("profile_data", "flowinvoice.rbvk_wibank-2026.09.2")
EXANTE = ("profile_data", "flowinvoice.exante_basis-fb2d18568d2e")
YEAR = ("profile_data", "riskanalysis.year_bound-2026.09.5")

CASES: dict[str, tuple[tuple[str, str], Mutation]] = {
    "top-unknown": (LEGACY, _set("extra", value=1)),
    "top-schema": (LEGACY, _set("schema", value="x")),
    "top-status": (LEGACY, _set("status", value="DRAFT")),
    "top-status-empty": (LEGACY, _set("status", value=" ")),
    "top-source": (LEGACY, _set("source", value={})),
    "top-rules-empty": (LEGACY, _set("rules", value=[])),
    "top-duplicate-code": (LEGACY, _set("@RF02", "code", value="RF01")),
    "top-duplicate-column": (LEGACY, _set("@RF02", "column", value="rf01")),
    "top-output": (LEGACY, _set("output", value=[])),
    "top-summary-format": (LEGACY, _set("summary", "format", value="x")),
    "top-summary-amount": (LEGACY, _drop("summary", "amount_field")),
    "top-decisions": (LEGACY, _set("open_decisions", value=[1])),
    "top-id": (LEGACY, _set("id", value="")),
    "rule-object": (LEGACY, _set("rules", value=[1])),
    "rule-unknown": (LEGACY, _set("@RF01", "extra", value=1)),
    "rule-kind": (LEGACY, _set("@RF01", "kind", value="nope")),
    "rule-requires": (LEGACY, _set("@RF01", "requires", value="x")),
    "rule-when": (LEGACY, _set("@RF01", "when_missing_columns", value="x")),
    "rule-interpretation": (LEGACY, _set("@RF01", "interpretation", value="x")),
    "rule-column": (LEGACY, _set("@RF01", "column", value=1)),
    "rule-note": (LEGACY, _set("@RF01", "note", value=1)),
    "rule-origin": (LEGACY, _set("@RF01", "origin", value={})),
    "rule-params": (LEGACY, _set("@RF01", "params", value=[])),
    "rule-undetermined-kind": (LEGACY, _set("@RF01", "when_missing_columns", value="undetermined")),
    "rule-undetermined-columns": (
        YEAR,
        _set("@RF02", "requires", value=["nettobetrag", "x"]),
    ),
    "rule-severity": (LEGACY, _set("@RF01", "severity", value="HUGE")),
    "rule-points": (LEGACY, _set("@RF01", "points", value=True)),
    "rule-echo": (LEGACY, _set("@RF01", "echo_fields", value={"a-b": "x"})),
    "rule-messages": (LEGACY, _set("@RF01", "messages", value={})),
    "rule-messages-parts": (LEGACY, _set("@RF01", "messages", value={"default": {"x": "y"}})),
    "rule-code": (LEGACY, _set("@RF01", "label", value="")),
    "param-missing": (LEGACY, _drop("@RF01", "params", "multiple")),
    "param-unknown": (LEGACY, _set("@RF01", "params", "extra", value=1)),
    "param-parse": (LEGACY, _set("@RF01", "params", "parse", value="x")),
    "param-missing-value": (LEGACY, _set("@RF01", "params", "missing_value", value="x")),
    "param-number": (LEGACY, _set("@RF01", "params", "multiple", value="x")),
    "param-reason-empty": (YEAR, _set("@RF02", "params", "missing_amount_reason", value=" ")),
    "param-reason-substitute": (YEAR, _set("@RF02", "params", "missing_value", value=0)),
    "param-placeholder": (LEGACY, _set("@RF08", "params", "placeholder_pattern", value="(")),
    "param-relevance-keys": (LEGACY, _set("@RF08", "params", "relevance", value={"field": "x"})),
    "param-relevance-missing": (
        LEGACY,
        _set("@RF08", "params", "relevance", "column_missing", value="x"),
    ),
    "param-relevance-pattern": (
        LEGACY,
        _set("@RF08", "params", "relevance", "exclude_pattern", value="("),
    ),
    "param-id-column": (LEGACY, _set("@RF08", "params", "id_column_missing", value="x")),
    "param-thresholds-static": (LEGACY, _set("@RF02", "params", "thresholds", value={})),
    "param-thresholds-key": (LEGACY, _set("@RF02", "params", "thresholds", "x", value=1)),
    "param-thresholds-positive": (
        LEGACY,
        _set("@RF02", "params", "thresholds", "static", value=[-1]),
    ),
    "param-eu-keys": (YEAR, _set("@RF02", "params", "thresholds", "procurement_eu", value={})),
    "param-eu-source": (
        YEAR,
        _set("@RF02", "params", "thresholds", "procurement_eu", "date_source", value="x"),
    ),
    "param-eu-field": (
        YEAR,
        _drop("@RF02", "params", "thresholds", "procurement_eu", "date_field"),
    ),
    "param-lower-both": (
        LEGACY,
        _set("@RF02", "params", "lower", value={"proximity": 0.1, "factor": 0.9}),
    ),
    "param-lower-range": (LEGACY, _set("@RF02", "params", "lower", value={"factor": 1.5})),
    "param-count": (LEGACY, _set("@RF02", "params", "count", value="x")),
    "param-propagation": (LEGACY, _set("@RF12", "params", "propagation", value="x")),
    "param-op": (LEGACY, _set("@RF13", "params", "op", value="eq")),
    "param-normalization": (LEGACY, _set("@RF09", "params", "normalization", value={})),
    "param-scorer": (LEGACY, _set("@RF09", "params", "scorer", value="x")),
    "param-pair": (LEGACY, _set("@RF10", "params", "pair", value={"x": 1})),
    "param-group": (LEGACY, _set("@RF10", "params", "group", value={"x": 1})),
    "param-marker": (
        FLOWSTAT,
        _set("@BL_RF09_DIRECT_AWARD_HIGH_AMOUNT", "params", "marker_pattern", value="("),
    ),
    "invoice-number": (CHECKER, _set("@HIGH_AMOUNT", "params", "sigma", value="x")),
    "invoice-patterns": (CHECKER, _set("@NO_PROJECT_REFERENCE", "params", "patterns", value=[])),
    "invoice-pattern": (CHECKER, _set("@NO_PROJECT_REFERENCE", "params", "patterns", value=["("])),
    "invoice-split-thresholds": (
        CHECKER,
        _set("@SPLIT_INVOICE", "params", "thresholds", value=[0]),
    ),
    "invoice-split-proximity": (CHECKER, _set("@SPLIT_INVOICE", "params", "proximity", value=1)),
    "invoice-split-items": (CHECKER, _set("@SPLIT_INVOICE", "params", "min_items", value=0)),
    "invoice-split-window": (CHECKER, _set("@SPLIT_INVOICE", "params", "window_days", value=-1)),
    "invoice-split-eu": (CHECKER, _set("@SPLIT_INVOICE", "params", "procurement_eu", value={})),
    "invoice-round-severity": (
        CHECKER,
        _set("@ROUND_AMOUNT", "params", "severity_with_terms", value="x"),
    ),
    "invoice-round-multiple": (CHECKER, _set("@ROUND_AMOUNT", "params", "multiple", value=0)),
    "invoice-round-terms": (CHECKER, _set("@ROUND_AMOUNT", "params", "terms", value="x")),
    "invoice-unknown": (CHECKER, _set("@HIGH_AMOUNT", "params", "x", value=1)),
    "score-truthy": (RBVK, _set("@K1", "params", "fields", value=[])),
    "score-truthy-values": (RBVK, _set("@K1", "params", "truthy_values", value="x")),
    "score-set": (RBVK, _set("@K2", "params", "values", value="x")),
    "score-mode": (RBVK, _set("@K20", "params", "mode", value="x")),
    "score-range-bound": (EXANTE, _set("@E1", "params", "lower", value="x")),
    "score-range-none": (
        EXANTE,
        lambda d: _rule(d, "E1")["params"].update(lower=None, upper=None),
    ),
    "score-range-missing": (EXANTE, _set("@E1", "params", "missing_value", value=None)),
    "weighted-keys": (CHECKER, _set("assessment", "extra", value=1)),
    "weighted-kind": (CHECKER, _set("assessment", "kind", value="x")),
    "weighted-weights": (CHECKER, _drop("assessment", "weights", "HIGH")),
    "weighted-number": (CHECKER, _set("assessment", "weights", "HIGH", value="x")),
    "weighted-divisor": (CHECKER, _set("assessment", "divisor", value=0)),
    "weighted-order": (CHECKER, _set("assessment", "severity_order", value=["HIGH"])),
    "weighted-summary": (CHECKER, _set("assessment", "summary", value={})),
    "weighted-template": (CHECKER, _set("assessment", "summary", "one", value="{a.b}")),
    "weighted-template-text": (CHECKER, _set("assessment", "summary", "one", value=5)),
    "weighted-template-syntax": (CHECKER, _set("assessment", "summary", "one", value="{")),
    "weighted-template-conversion": (CHECKER, _set("assessment", "summary", "one", value="{a!r}")),
    "weighted-severity": (CHECKER, _drop("@HIGH_AMOUNT", "severity")),
    "points-keys": (RBVK, _set("assessment", "extra", value=1)),
    "points-rule": (RBVK, _drop("@K1", "points")),
    "points-stages": (RBVK, _set("assessment", "stages", value={})),
    "points-order": (
        RBVK,
        _set("assessment", "stages", value=[{"min": 1, "stage": "a"}, {"min": 2, "stage": "b"}]),
    ),
    "points-cap": (RBVK, _set("assessment", "cap", value="x")),
    "points-override": (RBVK, _set("assessment", "points_override", value="x")),
    "points-template": (RBVK, _set("assessment", "detail_template", value="{a[0]}")),
}

#: First error per malformed document, recorded from auditcore_risk 0.3.0.
EXPECTED: dict[str, str] = RECORDED["profiles"]


@pytest.mark.parametrize("case", sorted(CASES))
def test_first_validation_error_is_unchanged(case: str) -> None:
    (folder, name), mutate = CASES[case]
    data = copy.deepcopy(_raw(folder, name))
    mutate(data)
    with pytest.raises(ProfileError) as info:
        profile_from_dict(data)
    assert str(info.value) == EXPECTED[case]


FRAUD_CASES: dict[str, tuple[str, Mutation]] = {
    "schema": ("flowinvoice.fraud_signals-fb2d18568d2e", _set("schema", value="x")),
    "unknown": ("flowinvoice.fraud_signals-fb2d18568d2e", _set("x", value=1)),
    "kind": ("flowinvoice.fraud_signals-fb2d18568d2e", _set("kind", value="x")),
    "id": ("flowinvoice.fraud_signals-fb2d18568d2e", _set("id", value="")),
    "parameters": ("flowinvoice.fraud_signals-fb2d18568d2e", _set("parameters", value=[])),
    "signal-keys": ("flowinvoice.fraud_signals-fb2d18568d2e", _set("parameters", "x", value=1)),
    "signal-policy": (
        "flowinvoice.fraud_signals-2026.09.2",
        _set("parameters", "policy", "warning_count", value="x"),
    ),
    "signal-order": (
        "flowinvoice.fraud_signals-fb2d18568d2e",
        lambda d: d["parameters"]["order"].append(d["parameters"]["order"][0]),
    ),
    "signal-weight": (
        "flowinvoice.fraud_signals-fb2d18568d2e",
        _set("parameters", "score", "per_blocker", value="x"),
    ),
    "signal-levels": (
        "flowinvoice.fraud_signals-fb2d18568d2e",
        lambda d: d["parameters"]["levels"]["thresholds"].reverse(),
    ),
    "ted-unit": (
        "flowinvoice.ted_contractor-fb2d18568d2e",
        _set("parameters", "legitimacy", "unit", value="x"),
    ),
    "ted-keys": ("flowinvoice.ted_contractor-fb2d18568d2e", _set("parameters", "x", value=1)),
    "ted-condition": (
        "flowinvoice.ted_contractor-fb2d18568d2e",
        lambda d: d["parameters"]["flags"][0]["when"][0].update(op="eq"),
    ),
    "duplicates-keys": ("flowinvoice.duplicates-fb2d18568d2e", _set("parameters", "x", value=1)),
    "duplicates-window": (
        "flowinvoice.duplicates-fb2d18568d2e",
        _set("parameters", "fuzzy", "date_range_days", value=0),
    ),
    "duplicates-weights": (
        "flowinvoice.duplicates-fb2d18568d2e",
        _set("parameters", "fuzzy", "date_weight", value=0.9),
    ),
}

#: First error per malformed fraud profile, recorded from auditcore_risk 0.3.0.
FRAUD_EXPECTED: dict[str, str] = RECORDED["fraud"]


@pytest.mark.parametrize("case", sorted(FRAUD_CASES))
def test_first_fraud_validation_error_is_unchanged(case: str) -> None:
    name, mutate = FRAUD_CASES[case]
    data = copy.deepcopy(_raw("fraud_profiles", name))
    mutate(data)
    with pytest.raises(ProfileError) as info:
        fraud_profile_from_dict(data)
    assert str(info.value) == FRAUD_EXPECTED[case]
