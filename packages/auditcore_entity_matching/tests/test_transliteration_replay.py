"""Profiles 2026.09.2 reproduce the transliterating originals of 23.09.2026 exactly."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from auditcore_entity_matching import classify, legacy, load_profile, normalize

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "transliteration_observed.json").read_text()
)
CASES = FIXTURE["cases"]
V2 = "2026.09.2"


def run(case: dict[str, Any]) -> Any:
    op, i = case["operation"], case["inputs"]
    if op == "designer_normalize_v2":
        return legacy.designer_normalisiere_name_umschrift(i["text"])
    if op == "workshop_normalize_v2":
        return legacy.flowworkshop_normalize_name_umschrift(i["text"])
    if op == "designer_classify_v2":
        profile = load_profile("audit_designer.sanctions", V2)
        return classify(i["score"], profile, i["q_norm"], i["matched_norm"])
    if op == "workshop_classify_v2":
        profile = load_profile("flowworkshop.sanctions", V2)
        return classify(i["score"], profile, i["q_norm"], i["matched_norm"])
    raise AssertionError(op)


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_original_output_is_reproduced(case: dict[str, Any]) -> None:
    assert case["exception"] is None
    assert run(case) == case["output"]


def test_fixture_scope_and_sources() -> None:
    assert len(CASES) == 220
    assert {s["commit"] for s in FIXTURE["sources"]} == {
        "1254591156d3bdf6ccdf4050dec7713a61ad4a20",
        "3d1cb40221645935c323392d70d84102d05ac7bb",
    }
    assert FIXTURE["environment"]["auditcore_entity_matching_called_by_workshop"] == "0.1.0"


def test_designer_profile_constants_equal_the_executed_source() -> None:
    constants = FIXTURE["constants"]
    rules = load_profile("audit_designer.sanctions", V2).normalization
    assert rules is not None and rules.algorithm == "casefold_nfc_fold_nfkd"
    assert dict(rules.fold_map) == constants["audit_designer.sanctions.fold_map"]
    assert sorted(rules.legal_suffixes) == constants["audit_designer.sanctions.legal_suffixes"]


def test_decision_mueller_and_unchanged_special_letters() -> None:
    designer = load_profile("audit_designer.sanctions", V2)
    workshop = load_profile("flowworkshop.sanctions", V2)
    for profile in (designer, workshop):
        assert normalize("Müller GmbH", profile) == "mueller"
        assert normalize("Straße", profile) == "strasse"
        assert normalize("Søren Ørsted", profile) == "soren orsted"
        assert normalize("Łódź", profile) == "lodz"
        assert normalize("Æther Œuvre", profile) == "aether oeuvre"
        assert normalize("Café", profile) == "cafe"
    # Only difference of the two variants: decomposed umlauts (NFC in the designer).
    assert normalize("Müller", designer) == "mueller"
    assert normalize("Müller", workshop) == "muller"


def test_previous_versions_are_unchanged() -> None:
    assert normalize("Müller GmbH", load_profile("audit_designer.sanctions", "2026.09.1")) == (
        "muller"
    )
    assert normalize("Müller GmbH", load_profile("flowworkshop.sanctions", "2026.09.1")) == (
        "muller"
    )
