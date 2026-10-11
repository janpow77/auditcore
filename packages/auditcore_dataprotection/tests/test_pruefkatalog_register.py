"""Prüfkatalog VVT/DSFA, Abschnitt 12: Rechtsprofile, Rollen und Verzeichnis (T-01 bis T-06)."""

from __future__ import annotations

from typing import Any

import pytest
from pruefkatalog_support import FACH, TENANT, full_activity, gdpr, hdsig, kat, new_register

from auditcore_dataprotection.export import register_report
from auditcore_dataprotection.register_content import check_activity
from auditcore_dataprotection.rules import load_profile


def codes(activity: dict[str, Any], profile: Any = None) -> dict[str, bool]:
    return {
        f"{i.code}:{i.subject.split(':')[-1]}": i.blocking
        for i in check_activity(activity, profile or hdsig())
    }


def test_t01_fehlendes_rechtsprofil_kein_stiller_dsgvo_standard() -> None:
    world = kat()
    activity = full_activity()
    del activity["rechtsregime"]
    activity_id = new_register(world, activity)  # Entwurf bleibt speicherbar
    found = codes(activity)
    assert found["missing_regime:rechtsregime"] is True
    result = world.workspace.evaluate(TENANT, FACH, activity_id)
    assert "GATE-01" in {g.id for g in result.gates}
    assert result.axes.documentation.value == "entwurf"


def test_t01_unklares_regime_ist_eigene_sperre() -> None:
    found = codes(full_activity(rechtsregime="unklar"))
    assert found["unclear_regime:rechtsregime"] is True


def test_t02_getrennte_zuordnung_je_taetigkeit() -> None:
    owi = full_activity(anwendungs_ids=["app-1"])
    markt = full_activity(
        name="Allgemeine Marktbeobachtung",
        zweck="Statistische Marktbeobachtung",
        rechtsregime="dsgvo",
        anwendungs_ids=["app-1"],
    )
    assert "regime_mismatch:rechtsregime" not in codes(owi)
    assert codes(markt)["regime_mismatch:rechtsregime"] is True
    assert "regime_mismatch:rechtsregime" not in codes(markt, gdpr())


def test_t03_zwei_anwendungen_eine_taetigkeit_ohne_dublette() -> None:
    from auditcore_dataprotection.scope import activities_of_application, duplicate_hints

    activity = {**full_activity(anwendungs_ids=["app-1", "app-2"]), "id": "t-1"}
    assert activities_of_application([activity], "app-1") == ("t-1",)
    assert activities_of_application([activity], "app-2") == ("t-1",)
    copy_ = {**activity, "id": "t-2"}
    assert duplicate_hints([activity, copy_])


def test_t04_hdsig_uebermittlung_ohne_rechtsgrundlage() -> None:
    activity = full_activity(uebermittlungen=[{"empfaenger": "Amtsgericht"}])
    assert codes(activity)["missing_field:uebermittlungen[0].rechtsgrundlage"] is True
    without = full_activity()
    del without["uebermittlungen"]
    assert codes(without)["missing_transfer_basis:uebermittlungen"] is True


def test_t05_profiling_im_hdsig_export_nicht_weggelassen() -> None:
    profile = hdsig()
    assert "profiling" in dict(profile.register_columns)
    world = kat()
    new_register(world, full_activity(profiling=True, profiling_beschreibung="Priorisierung"))
    draft = world.register.draft(TENANT, FACH)
    assert draft is not None
    report = register_report(draft, profile)
    text = repr(report)
    assert "Profiling" in text and "uebermittlungen" in repr(dict(profile.register_columns))
    missing = full_activity()
    del missing["profiling"]
    assert codes(missing)["undecided_flag:profiling"] is True  # im HDSIG sperrend
    assert codes(missing, gdpr())["undecided_flag:profiling"] is False  # DSGVO: Hinweis


def test_t06_rolle_auftragsverarbeiter_wechselt_vorlage() -> None:
    processor = {
        "name": "Hosting im Auftrag",
        "rechtsregime": "hdsig_ji",
        "rolle": "auftragsverarbeiter",
    }
    found = codes(processor)
    assert found["missing_field:auftraggeber"] is True
    assert found["missing_field:kategorien_verarbeitungen"] is True
    assert "missing_field:zweck" not in found  # Verantwortlichenformular gilt nicht
    assert dict(hdsig().processor_columns)["auftraggeber"]


def test_wenn_moeglich_felder_brauchen_begruendung_und_pruefstelle() -> None:
    activity = full_activity(speicherdauer="")
    assert codes(activity)["missing_field:speicherdauer"] is True
    justified = full_activity(
        speicherdauer="",
        speicherdauer_begruendung="Frist hängt von Abstimmung mit dem Archiv ab",
        speicherdauer_pruefstelle="Referat Z",
    )
    assert codes(justified)["open_justified:speicherdauer"] is False


@pytest.mark.parametrize("version", ["2026.10.1", "2026.10.2", "2026.10.3"])
def test_aeltere_profile_bleiben_unveraendert(version: str) -> None:
    old = load_profile("auditcore.hdsig_ji", version)
    assert not old.register_regime_checks
    assert not old.justification_required_for
    assert "hdsig_64_1_nr2_form" not in old.question_keys
