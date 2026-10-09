"""Prüfkatalog VVT/DSFA, Abschnitt 12: Rechte, Lebenszyklus, Register, Wizard (T-17 bis T-36)."""

from __future__ import annotations

import socket
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

import pytest
from pruefkatalog_support import (
    ADMIN,
    CHEF,
    DEV,
    DSB,
    FACH,
    LEITUNG,
    TENANT,
    ZENTRAL,
    Kat,
    full_activity,
    kat,
    new_register,
    person,
)

from auditcore_dataprotection.central_register import RECEIPT_CONFLICT, transfer_key
from auditcore_dataprotection.checklist import ItemStatus, Transition
from auditcore_dataprotection.errors import (
    AuthorizationError,
    ConflictError,
    StaleRevisionError,
    ValidationError,
)
from auditcore_dataprotection.operation import DecisionRequest
from auditcore_dataprotection.publication import public_findings, public_pattern, release_for_public
from auditcore_dataprotection.register_content import normalize_content
from auditcore_dataprotection.scope import personal_data_findings
from auditcore_dataprotection.wizard_catalog import KIND_TEXT, KIND_YES_NO

AT = datetime(2026, 9, 2, 9, 0, tzinfo=UTC)
TEXT = "Synthetische Angabe für den Abnahmetest"


def _release(world: Kat) -> Any:
    draft = world.register.draft(TENANT, FACH)
    assert draft is not None
    return world.register.release(TENANT, LEITUNG, expected_revision=draft.revision)


def _revision(world: Kat) -> int | None:
    draft = world.register.draft(TENANT, FACH)
    return None if draft is None else draft.revision


YES = {"W01-06", "W09:gesamt_01_sonstiges_hohes_risiko", "W11-05", "W12-01"}


def _value(question: dict[str, Any]) -> str:
    if question["kind"] == KIND_YES_NO:
        return "ja" if question["id"] in YES else "nein"
    if question["kind"] == KIND_TEXT:
        return TEXT
    if question["choices"]:
        preferred = {"verantwortlicher", "hdsig_ji", "produktion", "synthetisch", "keine"}
        keys = [c["key"] for c in question["choices"]]
        return next((k for k in keys if k in preferred), keys[0])
    return "wirksam_nachgewiesen"


def _answer_everything(world: Kat, activity_id: str) -> None:
    """Walk the wizard in guided mode and answer every visible open question."""
    for _ in range(200):
        overview = world.workspace.overview(TENANT, FACH, activity_id)
        wizard = overview["assistent"]
        open_ = [t for t in wizard["tasks"] if t["kind"] == "fehlt"]
        if not open_:
            return
        task = open_[0]
        step = next(s for s in wizard["steps"] if s["id"] == task["step"])
        question = next(q for q in step["questions"] if q["id"] == task["question"])
        value = _value(question)
        is_dpia = question["target"].startswith(("screening:", "assessment:"))
        world.workspace.answer(
            TENANT,
            FACH,
            activity_id,
            question["id"],
            value,
            justification=TEXT if value in question["justify_values"] else "",
            expected_revision=None if is_dpia else _revision(world),
        )
    raise AssertionError("Wizard endet nicht")


def test_wizard_fuehrt_schrittweise_und_frei_wahlweise() -> None:
    world = kat()
    world.workspace.create_activity(TENANT, FACH, "Neue Tätigkeit", content_if_new=_cover())
    activity_id = str(world.register.draft(TENANT, FACH).activities[0]["id"])  # type: ignore[union-attr]
    view = world.workspace.overview(TENANT, FACH, activity_id)["assistent"]
    assert view["mode"] == "gefuehrt" and view["current_step"] == "W01"
    assert view["next_step"] == "W02"
    with pytest.raises(ConflictError, match="schrittweise"):
        world.workspace.navigate(
            TENANT,
            FACH,
            activity_id,
            mode="gefuehrt",
            step="W07",
            expected_revision=_revision(world),
        )
    world.workspace.navigate(
        TENANT, FACH, activity_id, mode="gefuehrt", step="W02", expected_revision=_revision(world)
    )
    world.workspace.navigate(
        TENANT, FACH, activity_id, mode="frei", step="W07", expected_revision=_revision(world)
    )
    view = world.workspace.overview(TENANT, FACH, activity_id)["assistent"]
    assert view["mode"] == "frei" and view["current_step"] == "W07"


def _cover() -> dict[str, Any]:
    from pruefkatalog_support import cover

    return cover()


def test_wizard_unklar_wird_aufgabe_und_ausgeblendete_antworten_wirken_nicht() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    world.workspace.answer(TENANT, FACH, activity_id, "W05-05", "ja", expected_revision=1)
    world.workspace.answer(
        TENANT, FACH, activity_id, "W05-05a", "Dienstleister in Drittland Y", expected_revision=2
    )
    draft = world.register.draft(TENANT, FACH)
    assert draft is not None and draft.activities[0]["name_empfaenger_drittland"]
    world.workspace.answer(TENANT, FACH, activity_id, "W05-05", "unklar", expected_revision=3)
    overview = world.workspace.overview(TENANT, FACH, activity_id)
    draft = world.register.draft(TENANT, FACH)
    assert draft is not None
    assert draft.activities[0]["drittlandtransfer"] is None  # unklar ≠ nein
    assert draft.activities[0]["name_empfaenger_drittland"] is None  # ausgeblendet
    assert "W05-05a" in overview["assistent"]["hidden_answers"]
    assert {"step": "W05", "question": "W05-05", "kind": "unklar"} in overview["assistent"]["tasks"]


def test_t17_entwicklerrolle_ruft_betriebsentscheidung_direkt_auf() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    _release(world)
    request = DecisionRequest(
        activity_id, "fuer_definierten_umfang_erteilt", "produktion", "1.0", "alle", TEXT * 2
    )
    for intruder in (DEV, ADMIN):
        with pytest.raises(AuthorizationError):
            world.operations.decide(TENANT, intruder, request)


def test_t18_fremde_organisation_sieht_nichts() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    stranger = person("fremd", "fach", tenant="mandant-2")
    with pytest.raises(AuthorizationError):
        world.workspace.overview(TENANT, stranger, activity_id)


def test_t19_t20_personenbezug_in_testbetrieb() -> None:
    assert personal_data_findings({"testdaten": "pseudonymisiert"})
    synthetic = {
        "testdaten": "synthetisch",
        "personenbezug": False,
        "protokollierung": "Zugriffslog mit Kennung der Beschäftigten",
    }
    assert any("Beschäftigtenkennungen" in f for f in personal_data_findings(synthetic))


def test_t21_vvt_historie_ersetzt_keine_fachprotokollierung() -> None:
    world = kat()
    activity_id = new_register(
        world,
        full_activity(
            nachweise=[
                {
                    "id": "N1",
                    "kind": "vvt_historie",
                    "reference": "Änderungshistorie",
                    "version": "1",
                    "checked_on": "2026-09-01",
                    "checked_by": "it_betrieb",
                },
            ]
        ),
    )
    change = Transition(ItemStatus.PROVEN, "fach", AT, evidence_ids=("N1",))
    with pytest.raises(ValidationError, match="fachprotokoll"):
        world.workspace.update_item(
            TENANT, FACH, activity_id, "CHK-16", change, expected_revision=1
        )


def test_t22_oeffentlicher_export_nie_automatisch() -> None:
    content = {
        "taetigkeiten": [
            {
                "name": "X",
                "ansprechperson": "erika@example.org",
                "tom": "https://intranet.local/konzept",
                "x": "token=abc123",
            }
        ]
    }
    assert len(public_findings(content)) == 3
    with pytest.raises(ConflictError):
        release_for_public(content, approved_by="", approval="")
    with pytest.raises(ConflictError, match="Nicht veröffentlichungsfähig"):
        release_for_public(content, approved_by="leitung", approval="Vermerk 1")
    pattern = public_pattern(content)
    assert public_findings(pattern) == ()


def test_t23_regelupdate_laesst_alte_bewertung_reproduzierbar() -> None:
    from auditcore_dataprotection.calculation import propose
    from auditcore_dataprotection.rules import load_profile

    old = load_profile("auditcore.hdsig_ji", "2026.10.3")
    answers = {k: False for k in old.question_keys}
    first = propose(old, answers).to_dict()
    again = propose(load_profile("auditcore.hdsig_ji", "2026.10.3"), answers).to_dict()
    assert first == again and first["profile"]["version"] == "2026.10.3"
    new = load_profile("auditcore.hdsig_ji", "2026.10.4")
    assert propose(new, answers).to_dict()["recommendation"] == "unvollstaendig"


def test_t24_neuer_empfaenger_oeffnet_pruefungen_erneut() -> None:
    world = kat()
    activity_id = new_register(
        world,
        full_activity(
            nachweise=[
                {
                    "id": "V1",
                    "kind": "vertrag",
                    "reference": "AVV 7",
                    "version": "2",
                    "checked_on": "2026-09-01",
                    "checked_by": "fach",
                }
            ]
        ),
    )
    world.workspace.update_item(
        TENANT,
        FACH,
        activity_id,
        "CHK-08",
        Transition(ItemStatus.PROVEN, "fach", AT, evidence_ids=("V1",)),
        expected_revision=1,
    )
    _release(world)
    world.workspace.answer(TENANT, FACH, activity_id, "W05-03a", "Neue externe Stelle")
    result = world.workspace.evaluate(TENANT, FACH, activity_id)
    assert result.checklist["CHK-08"].status is ItemStatus.RECHECK
    assert "GATE-07" in {g.id for g in result.gates}


def test_t25_t26_zentrale_uebernahme_idempotent_und_konflikt() -> None:
    world = kat()
    new_register(world, full_activity())
    released = _release(world)
    first = world.central.transfer(LEITUNG, released, dict(released.content))
    second = world.central.transfer(LEITUNG, released, dict(released.content))
    assert first == second and world.fake_central.calls == 1
    assert first.status.value == "uebernommen" and first.central_id == "HV-00001"
    conflicted = kat()
    new_register(conflicted, full_activity())
    other = _release(conflicted)
    conflicted.fake_central.answer = RECEIPT_CONFLICT
    record = conflicted.central.transfer(LEITUNG, other, dict(other.content))
    assert record.status.value == "konflikt"
    with pytest.raises(ConflictError):
        conflicted.central.confirm_takeover(
            ZENTRAL, TENANT, transfer_key(other), central_id="HV-9", proof="Mail"
        )


def test_t27_parallele_aenderung_wird_erkannt() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    world.workspace.answer(TENANT, FACH, activity_id, "W01-02", "A", expected_revision=1)
    with pytest.raises(StaleRevisionError):
        world.workspace.answer(TENANT, FACH, activity_id, "W01-02", "B", expected_revision=1)


def test_t28_stellungnahme_bleibt_an_alter_version() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    released = _release(world)
    world.workspace.answer(TENANT, FACH, activity_id, "W02-01", "Geänderter Zweck")
    result = world.workspace.evaluate(TENANT, FACH, activity_id)
    assert result.axes.documentation.value == "ueberarbeitungsbeduerftig"
    assert world.register.released(TENANT, FACH) == released  # unverändert


def test_t29_import_wird_als_daten_behandelt() -> None:
    from auditcore_dataprotection.memory import SequentialIds

    hostile = {"taetigkeiten": [{"name": "x", "tom": object()}]}
    with pytest.raises(ValidationError):
        normalize_content(hostile, SequentialIds())
    with pytest.raises(ValidationError):
        normalize_content(
            {"taetigkeiten": [{"name": "x", "uebermittlungen": "rm -rf /"}]}, SequentialIds()
        )


def test_t30_kern_ohne_netzwerk(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("Netzwerkzugriff")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    test_t24_neuer_empfaenger_oeffnet_pruefungen_erneut()


def test_t33_ki_vorschlag_bleibt_unbestaetigt() -> None:
    world = kat()
    activity_id = new_register(world, full_activity(ermaechtigungsgrundlage=None))
    world.workspace.answer(
        TENANT,
        FACH,
        activity_id,
        "W02-03",
        "§ 99 Beispielgesetz (vollständig begründet)",
        origin="ki_vorschlag",
        expected_revision=1,
    )
    draft = world.register.draft(TENANT, FACH)
    assert draft is not None and draft.activities[0]["ermaechtigungsgrundlage"] is None
    tasks = world.workspace.overview(TENANT, FACH, activity_id)["assistent"]["tasks"]
    assert {"step": "W02", "question": "W02-03", "kind": "unbestaetigt"} in tasks
    world.workspace.confirm(TENANT, FACH, activity_id, "W02-03", expected_revision=2)
    draft = world.register.draft(TENANT, FACH)
    assert draft is not None and draft.activities[0]["ermaechtigungsgrundlage"]


def test_t36_veralteter_nachweis_nicht_gruen() -> None:
    world = kat()
    activity_id = new_register(
        world,
        full_activity(
            nachweise=[
                {
                    "id": "T1",
                    "kind": "test",
                    "reference": "Rechtetest",
                    "version": "1",
                    "checked_on": "2025-01-01",
                    "checked_by": "it",
                    "valid_until": "2025-12-31",
                },
                {
                    "id": "T2",
                    "kind": "test",
                    "reference": "Wiederanlauf",
                    "version": "1",
                    "checked_on": "2026-08-01",
                    "checked_by": "it",
                    "available": False,
                },
            ]
        ),
    )
    for evidence in ("T1", "T2"):
        with pytest.raises(ValidationError):
            world.workspace.update_item(
                TENANT,
                FACH,
                activity_id,
                "CHK-14",
                Transition(ItemStatus.PROVEN, "fach", AT, evidence_ids=(evidence,)),
                expected_revision=1,
            )


def test_nicht_anwendbar_braucht_begruendung_und_zweite_person() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    with pytest.raises(ValidationError):
        world.workspace.update_item(
            TENANT,
            FACH,
            activity_id,
            "CHK-19",
            Transition(ItemStatus.NOT_APPLICABLE, "fach", AT),
            expected_revision=1,
        )
    world.workspace.update_item(
        TENANT,
        FACH,
        activity_id,
        "CHK-19",
        Transition(ItemStatus.NOT_APPLICABLE, "fach", AT, justification=TEXT * 2),
        expected_revision=1,
    )
    with pytest.raises(ConflictError, match="zweite Person"):
        world.workspace.confirm_item(TENANT, FACH, activity_id, "CHK-19", expected_revision=2)
    world.workspace.confirm_item(TENANT, DEV, activity_id, "CHK-19", expected_revision=2)


def test_vollstaendiger_durchlauf_bis_zur_betriebsentscheidung() -> None:
    world = kat()
    activity_id = new_register(
        world,
        full_activity(
            nachweise=[
                {
                    "id": "E1",
                    "kind": "test",
                    "reference": "Verschlüsselungstest",
                    "version": "1",
                    "checked_on": "2026-08-30",
                    "checked_by": "it_betrieb",
                }
            ],
            schutzmassnahmen=[
                {"key": "verschluesselung", "state": "wirksam_nachgewiesen", "evidence_ids": ["E1"]}
            ],
        ),
    )
    assessment = world.assessments.start(TENANT, FACH, activity_id, world.profile)
    _answer_everything(world, activity_id)  # inkl. Schwellwertanalyse und DSFA-Texte
    assessment = world.assessments.get(TENANT, FACH, assessment.assessment_id)
    assert assessment.proposal["screening"]["outcome"] == "pflicht"
    scenario = {
        "dimension": "vertraulichkeit",
        "description": "Offenlegung",
        "severity": 2,
        "likelihood": 2,
        "measures": ["verschluesselung"],
    }
    assessment = world.assessments.update(
        TENANT,
        FACH,
        assessment.assessment_id,
        expected_revision=assessment.revision,
        scenarios=[scenario],
    )
    assessment = world.assessments.decide(
        TENANT,
        FACH,
        assessment.assessment_id,
        expected_revision=assessment.revision,
        decision=assessment.proposal["recommendation"],
    )
    assessment = world.assessments.record_dpo_statement(
        TENANT,
        DSB,
        assessment.assessment_id,
        expected_revision=assessment.revision,
        vote="zugestimmt",
        statement="Keine Einwände.",
    )
    released = _release(world)
    world.assessments.release(
        TENANT, LEITUNG, assessment.assessment_id, expected_revision=assessment.revision
    )
    world.central.transfer(LEITUNG, released, dict(released.content))
    result = world.workspace.evaluate(TENANT, FACH, activity_id)
    assert [g.id for g in result.gates] == [], [g.reason for g in result.gates]
    decision = world.operations.decide(
        TENANT,
        CHEF,
        DecisionRequest(
            activity_id,
            "fuer_definierten_umfang_erteilt",
            "produktion",
            "1.0",
            "Pilotbetrieb Referat A",
            "Alle Prüfungen liegen vor; befristeter Pilotbetrieb für drei Monate in Referat A.",
        ),
    )
    assert decision.register_version == released.version
    axes = world.workspace.evaluate(TENANT, FACH, activity_id).axes.to_dict()
    assert axes == {
        "dokumentation": "bestaetigt",
        "dsfa_erforderlichkeit": "erforderlich",
        "dsfa_bearbeitung": "fachlich_abgeschlossen",
        "konsultation": "nicht_erforderlich_begruendet",
        "zentrale_uebernahme": "uebernommen",
        "betriebsentscheidung": "fuer_definierten_umfang_erteilt",
    }
    world.workspace.answer(TENANT, FACH, activity_id, "W02-01", "Neuer Zweck")
    later = world.workspace.evaluate(TENANT, FACH, activity_id).axes
    assert later.operation.value == "neu_zu_beurteilen"
    assert replace(decision) == decision


def test_t34_ausfall_des_verzeichnisdienstes_schaltet_nichts_ab() -> None:
    from auditcore_dataprotection.central_register import CentralRegisterUnavailable

    class Down:
        def submit(self, key: str, payload: object) -> object:
            raise ConnectionError("nicht erreichbar")

    world = kat()
    activity_id = new_register(world, full_activity())
    released = _release(world)
    world.central.port = Down()  # type: ignore[assignment]
    before = world.workspace.evaluate(TENANT, FACH, activity_id).axes
    with pytest.raises(CentralRegisterUnavailable, match="nachzuführen"):
        world.central.transfer(LEITUNG, released, dict(released.content))
    after = world.workspace.evaluate(TENANT, FACH, activity_id).axes
    assert before == after and after.transfer.value == "nicht_uebertragen"


def test_t35_dokumentation_nach_ausserbetriebnahme_verfuegbar() -> None:
    from auditcore_dataprotection.export import register_report
    from auditcore_dataprotection.register_html import render_register_html

    world = kat()
    new_register(world, full_activity())
    released = _release(world)
    # Nur die gespeicherte Fassung und das Profil werden gebraucht, kein laufender Dienst.
    html = render_register_html(register_report(released, world.profile))
    assert "Verfolgung von Ordnungswidrigkeiten" in html
    assert "Amtsgericht – § 69 OWiG" in html


def test_gate02_freigegebene_fassung_mit_luecken_ist_nicht_bestaetigt() -> None:
    world = kat()
    new_register(world, full_activity(rechtsregime="unklar"))
    draft = world.register.draft(TENANT, FACH)
    assert draft is not None
    with pytest.raises(ConflictError, match="unvollständig"):  # sperrende Lücke
        world.register.release(TENANT, LEITUNG, expected_revision=draft.revision)
    other = kat()
    activity_id = new_register(other, full_activity())
    _release(other)  # Verzeichnis vollständig, Angaben des Assistenten noch offen
    result = other.workspace.evaluate(TENANT, FACH, activity_id)
    assert result.axes.documentation.value == "ueberarbeitungsbeduerftig"
    assert "GATE-02" in {g.id for g in result.gates}
