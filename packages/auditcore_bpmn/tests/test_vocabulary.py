"""Vokabulare: allgemeingültig, zweisprachig, periodenabhängige Rollen."""

from __future__ import annotations

from auditcore_bpmn import vocabulary as v


def test_labels_and_fallback() -> None:
    assert v.label(v.DIAGRAM_STATUS["in_pruefung"]) == "in Prüfung"
    assert v.label(v.DIAGRAM_STATUS["in_pruefung"], "en") == "under review"
    assert v.label(v.DIAGRAM_STATUS["entwurf"], "fr") == "Entwurf"
    assert v.label(None) == ""


def test_roles_bound_to_periods() -> None:
    assert v.ROLES["bb"].applies_to("2014-2020") and not v.ROLES["bb"].applies_to("2021-2027")
    assert v.ROLES["rfs"].applies_to("2021-2027") and v.ROLES["rfs"].applies_to("2028-2034")
    assert not v.ROLES["rfs"].applies_to("2014-2020")
    assert v.ROLES["vb"].applies_to(None) and v.ROLES["vb"].applies_to("unbekannt")
    assert v.period_start("2021-2027") == 2021 and v.period_start("20x1-2027") is None


def test_all_vocabularies_bilingual_and_neutral() -> None:
    forbidden = ("hessen", "hmwvw", "wibank", "efre hessen")
    for vocabulary in (
        v.DIAGRAM_STATUS,
        v.MARKERS,
        v.AUDIT_TYPES,
        v.FUNDS,
        v.PROGRAMMING_PERIODS,
        v.CONTROL_TYPES,
        v.EXECUTION_MODES,
        v.RISK_CATEGORIES,
        v.RISK_LEVELS,
        v.TEST_RESULTS,
        v.FINDING_TYPES,
        v.FINDING_SEVERITIES,
        v.FINDING_STATUS,
        v.SOURCE_TYPES,
        v.DEADLINE_UNITS,
        v.CONFIDENTIALITY,
        v.VARIANTS,
        v.FUNCTIONING_CATEGORIES,
    ):
        for labels in vocabulary.values():
            assert set(labels) == {"de", "en"}
            assert not any(word in labels["de"].lower() for word in forbidden)
    for role in v.ROLES.values():
        assert set(role.labels) == {"de", "en"}
    assert set(v.MARKER_COLORS) <= set(v.MARKERS) and set(v.COLOR_PRIORITY) <= set(v.MARKERS)
