"""User decisions of 23.09.2026 as new recommended profiles; legacy profiles unchanged."""

from __future__ import annotations

import pytest

from auditcore_entity_matching import (
    ProfileError,
    load_profile,
    normalize,
    recommended_profile,
)

DECOMPOSED = "Mu\u0308ller-Lu\u0308denscheidt GmbH"


@pytest.mark.parametrize(
    ("purpose", "profile_id", "version"),
    [
        ("entity_normalization", "flowworkshop.state_aid", "2026.09.2"),
        ("sanctions_screening", "audit_designer.sanctions", "2026.09.3"),
        ("pep_screening", "flowinvoice.pep", "2026.09.2"),
        ("payee", "riskanalysis.payee", "2026.09.2"),
    ],
)
def test_recommended_profiles_follow_the_mueller_rule_and_nfc(
    purpose: str, profile_id: str, version: str
) -> None:
    profile = recommended_profile(purpose)
    assert (profile.id, profile.version) == (profile_id, version)
    assert profile.status == "USER_DECIDED"
    composed = normalize("Müller-Lüdenscheidt GmbH", profile)
    assert composed.startswith("mueller luedenscheidt")
    assert normalize(DECOMPOSED, profile) == composed  # R2
    assert normalize("Straße", profile) == "strasse"


def test_r2_flowworkshop_sanctions_nfc() -> None:
    assert (
        normalize("Mu\u0308ller", load_profile("flowworkshop.sanctions", "2026.09.2")) == "muller"
    )
    assert (
        normalize("Mu\u0308ller", load_profile("flowworkshop.sanctions", "2026.09.3")) == "mueller"
    )


def test_r3_pep_keeps_latin_special_letters() -> None:
    new = load_profile("flowinvoice.pep", "2026.09.2")
    assert normalize("Jørgen Ødegård", new) == "jorgen odegard"
    assert normalize("Jørgen Ødegård", load_profile("flowinvoice.pep", "2026.09.1")) == (
        "j rgen degard"
    )


def test_k4_payee_new_profile_legacy_unchanged() -> None:
    new = load_profile("riskanalysis.payee", "2026.09.2")
    old = load_profile("riskanalysis.payee", "2026.09.1")
    assert normalize("Müller GmbH", new) == "mueller"
    assert normalize("Müller GmbH", old) == "mu ller"
    assert normalize("Stadtwerke Nord GmbH & Co. KG", new) == "stadtwerke nord"
    assert normalize("Café Élan", new) == "cafe elan"


def test_unknown_purpose_and_bad_compose() -> None:
    with pytest.raises(ProfileError):
        recommended_profile("unbekannt")
