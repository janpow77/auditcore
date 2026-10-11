"""Profil auditcore.hdsig_ji 2026.10.5: Maßstab der Vorprüfung ist § 62 Abs. 1 HDSIG."""

from __future__ import annotations

import json
from importlib.resources import files

import pytest

from auditcore_dataprotection import load_profile
from auditcore_dataprotection.errors import ProfileError
from auditcore_dataprotection.profile_loader import profile_from_dict
from auditcore_dataprotection.screening import screen
from auditcore_dataprotection.wizard_catalog import catalog_for

DECISIVE = "hdsig_62_1_hohes_risiko"
LIST_ENTRY = "dsk_nr11_kuenstliche_intelligenz"


def _all_no() -> dict[str, dict[str, str]]:
    profile = load_profile("auditcore.hdsig_ji", "2026.10.5")
    return {q.key: {"value": "nein"} for q in profile.questions}


def test_listen_und_kriterien_sind_nur_anhaltspunkte() -> None:
    profile = load_profile("auditcore.hdsig_ji", "2026.10.5")
    hard = {q.key for q in profile.questions if q.effect == "hart"}
    assert hard == {DECISIVE, "hdsig_64_1_nr2_form"}
    assert [q.key for q in profile.questions if q.decisive] == [DECISIVE]
    assert not [q for q in profile.questions if q.effect == "punkt"]


def test_anhaltspunkt_allein_loest_keine_dsfa_aus() -> None:
    profile = load_profile("auditcore.hdsig_ji", "2026.10.5")
    answers = _all_no()
    answers[LIST_ENTRY] = {"value": "ja"}
    assert screen(profile, answers).outcome == "unvollstaendig"
    answers[DECISIVE] = {"value": "nein", "justification": "Nur Terminsteuerung."}
    result = screen(profile, answers)
    assert result.outcome == "keine_pflicht"
    assert result.trace[-1]["indications"] == [LIST_ENTRY]
    answers[DECISIVE] = {"value": "ja"}
    assert screen(profile, answers).outcome == "pflicht"


def test_ohne_anhaltspunkt_genuegt_nein_und_offene_fragen_bleiben_offen() -> None:
    profile = load_profile("auditcore.hdsig_ji", "2026.10.5")
    assert screen(profile, _all_no()).outcome == "keine_pflicht"
    answers = _all_no()
    del answers[LIST_ENTRY]
    assert screen(profile, answers).outcome == "unvollstaendig"


def test_paragraf_64_bleibt_muss_kriterium_und_konsultationsgrund() -> None:
    profile = load_profile("auditcore.hdsig_ji", "2026.10.5")
    answers = _all_no()
    answers["hdsig_64_1_nr2_form"] = {"value": "ja"}
    result = screen(profile, answers)
    assert result.outcome == "pflicht"
    assert result.consultation_grounds == ("form_hochriskant",)


def test_fassung_2026_10_4_bleibt_unveraendert() -> None:
    profile = load_profile("auditcore.hdsig_ji", "2026.10.4")
    answers = {q.key: {"value": "nein"} for q in profile.questions}
    answers[LIST_ENTRY] = {"value": "ja"}
    result = screen(profile, answers)
    assert result.outcome == "pflicht"
    assert "indications" not in result.trace[-1]


def test_assistent_verlangt_begruendung_fuer_nein() -> None:
    catalog = catalog_for(load_profile("auditcore.hdsig_ji", "2026.10.5"))
    assert catalog.question(f"W09:{DECISIVE}").justify_values == ("nein",)


def test_anhaltspunkte_brauchen_eine_entscheidende_frage() -> None:
    raw = json.loads(
        files("auditcore_dataprotection.profiles")
        .joinpath("auditcore.hdsig_ji-2026.10.5.json")
        .read_text(encoding="utf-8")
    )
    for q in raw["screening"]["questions"]:
        q.pop("decisive", None)
    with pytest.raises(ProfileError, match="entscheidende Frage"):
        profile_from_dict(raw)
    for q in raw["screening"]["questions"]:
        q["decisive"] = True
    with pytest.raises(ProfileError, match="Höchstens eine"):
        profile_from_dict(raw)
