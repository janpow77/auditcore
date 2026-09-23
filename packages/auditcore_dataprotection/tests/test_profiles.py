"""Packaged rule profiles equal the executed source catalog and validate strictly."""

from __future__ import annotations

import copy
import json
from importlib import resources
from typing import Any

import pytest

from auditcore_dataprotection.errors import ProfileError
from auditcore_dataprotection.rules import (
    DECISIONS,
    available_profiles,
    fingerprint,
    load_profile,
    profile_from_dict,
)

VERSION = "2026.09.1"


def raw(profile_id: str = "regulierung.dsgvo") -> dict[str, Any]:
    entry = resources.files("auditcore_dataprotection.profiles").joinpath(
        f"{profile_id}-{VERSION}.json"
    )
    return json.loads(entry.read_text(encoding="utf-8"))


def test_available_profiles_are_the_two_regimes_in_both_versions() -> None:
    assert available_profiles() == (
        ("auditcore.dsgvo", "2026.10.1"),
        ("auditcore.dsgvo", "2026.10.2"),
        ("auditcore.hdsig_ji", "2026.10.1"),
        ("auditcore.hdsig_ji", "2026.10.2"),
        ("regulierung.dsgvo", VERSION),
        ("regulierung.hdsig_ji", VERSION),
    )


@pytest.mark.parametrize(
    "profile_id,regime", [("regulierung.dsgvo", "dsgvo"), ("regulierung.hdsig_ji", "hdsig_ji")]
)
def test_profiles_load_with_identity_and_source(profile_id: str, regime: str) -> None:
    profile = load_profile(profile_id, VERSION)
    assert profile.regime == regime
    assert profile.status == "SOURCE_CHARACTERIZED"
    assert "Keine rechtliche Prüfung" in profile.legal_status
    assert profile.source["commit"] == "a5d48ea4b90a410210ec25e707781ef9e21ad743"
    assert profile.source["rights"] == "USER_AUTHORIZED_MIT"
    assert profile.reference == {
        "id": profile_id,
        "version": VERSION,
        "fingerprint": profile.fingerprint,
    }
    assert len(profile.questions) == 18
    assert len(profile.measures) == 7
    assert set(profile.recommendation_texts) == set(DECISIONS)


def test_fingerprint_is_stable_and_detects_edits() -> None:
    data = raw()
    assert load_profile("regulierung.dsgvo", VERSION).fingerprint == fingerprint(data)
    assert fingerprint(copy.deepcopy(data)) == fingerprint(data)
    edited = copy.deepcopy(data)
    edited["screening"]["points_threshold"] = 3
    assert fingerprint(edited) != fingerprint(data)
    assert profile_from_dict(edited).points_threshold == 3
    assert (
        load_profile("regulierung.dsgvo", VERSION).fingerprint
        != load_profile("regulierung.hdsig_ji", VERSION).fingerprint
    )


@pytest.mark.parametrize(
    "profile_id,regime", [("regulierung.dsgvo", "dsgvo"), ("regulierung.hdsig_ji", "hdsig_ji")]
)
def test_profile_content_equals_executed_source_catalog(
    legacy: dict[str, Any], profile_id: str, regime: str
) -> None:
    catalog = legacy["catalog"]
    profile = load_profile(profile_id, VERSION)
    assert [
        (
            q.key,
            q.block,
            q.text,
            q.legal_basis,
            q.legal_basis_ji,
            q.effect,
            q.explanation,
            q.prefill,
        )
        for q in profile.questions
    ] == [
        (
            f["schluessel"],
            f["block"],
            f["text"],
            f["rechtsgrundlage"],
            f["rechtsgrundlage_ji"],
            f["wirkung"],
            f["erlaeuterung"],
            f["vorbelegung"],
        )
        for f in catalog["fragen"]
    ]
    assert [
        (m.key, m.title, m.legal_basis, m.reduces_likelihood, m.reduces_severity, m.explanation)
        for m in profile.measures
    ] == [
        (
            m["schluessel"],
            m["bezeichnung"],
            m["rechtsgrundlage"],
            m["senkt_wahrscheinlichkeit"],
            m["senkt_schwere"],
            m["erlaeuterung"],
        )
        for m in catalog["massnahmen"]
    ]
    assert dict(profile.norms) == catalog["normen"][regime]
    texts = catalog["vorschlag_text_ji" if regime == "hdsig_ji" else "vorschlag_text"]
    assert dict(profile.recommendation_texts) == texts
    assert profile.points_threshold == catalog["schwelle_punkte"]
    assert profile.large_scale_threshold == catalog["umfang_schwelle"]
    assert profile.min_justification_length == catalog["mindestlaenge_begruendung"]
    assert list(profile.significant_fields.items()) == list(catalog["wesentliche_felder"].items())
    assert list(profile.dimensions.items()) == list(catalog["dimensionen"].items())
    assert sorted(profile.sdm_dimensions) == catalog["sdm_dimensionen"]
    assert profile.blocks == tuple(catalog["block_titel"].items())
    assert [list(c) for c in profile.register_columns] == catalog["verzeichnis_spalten"]
    assert dict(profile.register_references) == catalog["verzeichnis_fundstellen"]
    assert {str(k): v for k, v in profile.severity_levels.items()} == catalog["schwere"]
    assert profile.regime_title == catalog["regime_titel"][regime]


def test_ji_references_follow_source_fundstelle(legacy: dict[str, Any]) -> None:
    """Observed JI outputs cite the question reference used by the JI profile."""
    ji = load_profile("regulierung.hdsig_ji", VERSION)
    cases = {c["name"]: c for c in legacy["cases"]}
    for question in ji.questions:
        single = cases[f"threshold-hdsig_ji-single-{question.key}"]["output"]["begruendung"]
        if question.effect == "hart":
            assert question.reference in single
    observed = cases["threshold-hdsig_ji-two-hard"]["output"]["begruendung"]
    assert ji.question("art35_3_a").reference in observed
    assert ji.question("dsk_03_biometrie").reference in observed


@pytest.mark.parametrize(
    "mutate,message",
    [
        (
            lambda d: d["screening"]["questions"].append(dict(d["screening"]["questions"][0])),
            "Doppelte Frageschlüssel",
        ),
        (lambda d: d["screening"]["questions"][0].update(effect="stark"), "Unbekannte Wirkung"),
        (lambda d: d["screening"]["questions"][0].update(block="x"), "ohne bekannten Block"),
        (
            lambda d: d["risk"]["measures"].append(dict(d["risk"]["measures"][0])),
            "Doppelte Maßnahmen",
        ),
        (lambda d: d["risk"]["bands"].reverse(), "Risikostufen"),
        (lambda d: d["risk"]["bands"].pop(), "Risikostufen"),
        (lambda d: d["risk"].update(scale={"min": 4, "max": 1}), "skala"),
        (lambda d: d["recommendation"].update(conditions_from=11), "Empfehlungsschwellen"),
        (lambda d: d["recommendation"]["texts"].pop("freigabe"), "Empfehlungstexte"),
        (lambda d: d.update(schema="x"), "Profilschema"),
        (lambda d: d["risk"].pop("measures"), "unvollständig"),
        (lambda d: d["risk"]["dimensions"].append(dict(d["risk"]["dimensions"][0])), "geordneten"),
    ],
)
def test_profile_validation_rejects_malformed_documents(mutate: Any, message: str) -> None:
    data = raw()
    mutate(data)
    with pytest.raises(ProfileError, match=message):
        profile_from_dict(data)


@pytest.mark.parametrize(
    "profile_id,version",
    [
        ("regulierung.dsgvo", "2026.09.2"),
        ("unbekannt", VERSION),
        ("../regulierung.dsgvo", VERSION),
        ("regulierung.dsgvo", "../../x"),
        ("regulierung.dsgvo/..", VERSION),
        ("", ""),
    ],
)
def test_load_profile_rejects_unknown_and_path_tricks(profile_id: str, version: str) -> None:
    with pytest.raises(ProfileError):
        load_profile(profile_id, version)


def test_no_implicit_default_profile() -> None:
    with pytest.raises(TypeError):
        load_profile()  # type: ignore[call-arg]
    with pytest.raises(ProfileError):
        load_profile(None, None)  # type: ignore[arg-type]


def test_profile_lookup_errors() -> None:
    profile = load_profile("regulierung.dsgvo", VERSION)
    with pytest.raises(ProfileError):
        profile.question("x")
    with pytest.raises(ProfileError):
        profile.measure("x")
    with pytest.raises(ProfileError):
        profile.norm("x")
    assert [profile.band(v) for v in (0, 1, 4, 5, 9, 10, 16)] == [
        "offen",
        "gering",
        "gering",
        "mittel",
        "mittel",
        "hoch",
        "hoch",
    ]
