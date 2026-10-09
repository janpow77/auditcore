"""Grenz- und Fehlerfälle der Prüfkatalog-Bausteine (Eingabeprüfung, Rechte, Zustände)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest
from pruefkatalog_support import (
    CHEF,
    FACH,
    LEITUNG,
    TENANT,
    ZENTRAL,
    cover,
    full_activity,
    gdpr,
    hdsig,
    kat,
    new_register,
)

from auditcore_dataprotection.central_register import (
    Receipt,
    TransferRecord,
    _status_of,
    transfer_key,
    transfer_status,
)
from auditcore_dataprotection.checklist import (
    ChecklistItem,
    ItemStatus,
    Transition,
    confirm_not_applicable,
    definition,
    filter_items,
    items_from_data,
    reopen,
    settled,
)
from auditcore_dataprotection.errors import (
    ConflictError,
    NotFoundError,
    ProfileError,
    StaleRevisionError,
    ValidationError,
)
from auditcore_dataprotection.evidence import (
    Evidence,
    EvidenceKind,
    evidence_from_data,
    evidence_problem,
    safeguards_from_data,
)
from auditcore_dataprotection.operation import DecisionRequest
from auditcore_dataprotection.operation_model import UrgentStart
from auditcore_dataprotection.publication import public_findings
from auditcore_dataprotection.register_regime import item_text
from auditcore_dataprotection.review_package import review_package
from auditcore_dataprotection.scope import duplicate_hints
from auditcore_dataprotection.status import StatusAxes
from auditcore_dataprotection.wizard import (
    WizardAnswer,
    assessment_texts,
    navigate,
    record_answer,
    screening_answers,
)
from auditcore_dataprotection.wizard_catalog import catalog_for, catalog_from_dict, load_catalog

AT = datetime(2026, 9, 2, 9, 0, tzinfo=UTC)
TEXT = "Synthetische Begründung mit ausreichender Länge für die Prüfung im Test."


def _release(world: Any) -> Any:
    draft = world.register.draft(TENANT, FACH)
    return world.register.release(TENANT, LEITUNG, expected_revision=draft.revision)


# ----------------------------------------------------------------- Nachweise


def test_nachweise_werden_geprueft() -> None:
    with pytest.raises(ValidationError, match="Nachweisart"):
        Evidence.from_dict({"id": "x", "kind": "foto", "reference": "r"})
    with pytest.raises(ValidationError, match="Kennung"):
        Evidence.from_dict({"id": "", "kind": "test", "reference": "r"})
    with pytest.raises(ValidationError, match="Datum"):
        Evidence.from_dict({"id": "x", "kind": "test", "reference": "r", "checked_on": "gestern"})
    with pytest.raises(ValidationError):
        evidence_from_data("keine Liste")
    with pytest.raises(ValidationError):
        evidence_from_data(["x"])
    one = {"id": "a", "kind": "test", "reference": "r"}
    with pytest.raises(ValidationError, match="Doppelte"):
        evidence_from_data([one, one])
    assert evidence_from_data(None) == {}
    item = Evidence.from_dict({**one, "checked_on": date(2026, 1, 1), "checked_by": " it "})
    assert item.to_dict()["checked_on"] == "2026-01-01" and item.checked_by == "it"
    assert "Version" in (evidence_problem(item, date(2026, 2, 1)) or "")
    unchecked = Evidence("b", EvidenceKind.TEST, "r", "1")
    assert "nicht geprüft" in (evidence_problem(unchecked, date(2026, 2, 1)) or "")


def test_schutzmassnahmen_werden_geprueft() -> None:
    assert safeguards_from_data(None) == {}
    for raw in ("x", [{"state": "geplant"}], [{"key": "a", "state": "fertig"}]):
        with pytest.raises(ValidationError):
            safeguards_from_data(raw)
    with pytest.raises(ValidationError):
        safeguards_from_data([{"key": "a", "state": "geplant", "evidence_ids": "E1"}])


# ---------------------------------------------------------------- Checkliste


def test_checkliste_daten_und_filter() -> None:
    with pytest.raises(ValidationError):
        definition("CHK-99")
    with pytest.raises(ValidationError):
        items_from_data("x")
    with pytest.raises(ValidationError, match="Unbekannte"):
        items_from_data({"CHK-99": {}})
    with pytest.raises(ValidationError):
        items_from_data({"CHK-01": "offen"})
    with pytest.raises(ValidationError, match="Status"):
        items_from_data({"CHK-01": {"status": "fertig"}})
    with pytest.raises(ValidationError):
        items_from_data({"CHK-01": {"evidence_ids": "E"}})
    items = items_from_data({"CHK-01": {"status": "nachgewiesen", "owner": "fach"}})
    assert settled(items["CHK-01"]) and not settled(items["CHK-02"])
    assert filter_items(items, owner="fach") == (items["CHK-01"],)
    assert items["CHK-01"] not in filter_items(items, blocking_only=True)
    assert items["CHK-04"] not in filter_items(items, blocking_only=True)
    assert len(filter_items(items, missing_evidence=True)) == 29
    reopened = reopen(items, ["CHK-01", "CHK-02"], "Änderung", AT)
    assert filter_items(reopened, recheck_only=True) == (reopened["CHK-01"],)
    optional = ChecklistItem("CHK-30", ItemStatus.NOT_APPLICABLE)
    assert settled(optional)
    with pytest.raises(ConflictError):
        confirm_not_applicable(items["CHK-02"], "zweite")


def test_nachgewiesen_nur_mit_erfasstem_nachweis() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    change = Transition(ItemStatus.PROVEN, "fach", AT, evidence_ids=("fehlt",))
    with pytest.raises(ValidationError, match="nicht erfasst"):
        world.workspace.update_item(
            TENANT, FACH, activity_id, "CHK-14", change, expected_revision=1
        )
    with pytest.raises(NotFoundError):
        world.workspace.update_item(
            TENANT,
            FACH,
            activity_id,
            "CHK-99",
            Transition(ItemStatus.OPEN, "f", AT),
            expected_revision=1,
        )


def test_nachweise_und_schutzmassnahmen_speichern() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    world.workspace.set_records(
        TENANT,
        FACH,
        activity_id,
        evidence=[{"id": "E1", "kind": "test", "reference": "Test", "version": "1"}],
        safeguards=[{"key": "verschluesselung", "state": "geplant"}],
        expected_revision=1,
    )
    activity = world.register.draft(TENANT, FACH).activities[0]  # type: ignore[union-attr]
    assert activity["nachweise"][0]["id"] == "E1"
    with pytest.raises(NotFoundError):
        world.workspace.set_records(TENANT, FACH, "unbekannt", evidence=[], expected_revision=2)


# ------------------------------------------------------------------ Assistent


def test_assistent_prueft_werte() -> None:
    catalog = catalog_for(hdsig())
    activity: dict[str, object] = {"rechtsregime": "hdsig_ji"}
    context = {"regime": "hdsig_ji", "dsfa": ""}

    def answer(question: str, value: str, why: str = "", origin: str = "bestaetigt") -> Any:
        return record_answer(
            catalog, activity, context, question, WizardAnswer(value, why, "f", "t", origin)
        )

    with pytest.raises(ValidationError, match="Herkunft"):
        answer("W01-01", "x", origin="geraten")
    with pytest.raises(ValidationError, match="nicht vorgesehen"):
        answer("W01-01", "nicht_anwendbar")
    with pytest.raises(ValidationError, match="zulässig"):
        answer("W01-06", "vielleicht")
    with pytest.raises(ValidationError, match="leer"):
        answer("W01-01", "  ")
    with pytest.raises(ValidationError, match="begründen"):
        answer("W01-06", "nein")
    with pytest.raises(ConflictError, match="ausgeblendet"):
        answer("W05-05a", "Land Y")
    with pytest.raises(ProfileError):
        answer("W99-01", "x")


def test_nicht_anwendbar_braucht_im_assistenten_begruendung() -> None:
    raw = load_catalog()
    steps = [
        {
            "id": s.id,
            "title": s.title,
            "questions": [{**q.to_dict(), "na_allowed": True} for q in s.questions],
        }
        for s in raw.steps
    ]
    catalog = catalog_from_dict({"version": "x", "steps": steps})
    wa = WizardAnswer("nicht_anwendbar", "", "f", "t", "bestaetigt")
    with pytest.raises(ValidationError, match="Begründung"):
        record_answer(catalog, {}, {}, "W01-01", wa)
    ok = WizardAnswer("nicht_anwendbar", "trifft nicht zu", "f", "t", "bestaetigt")
    data = record_answer(catalog, {}, {}, "W01-01", ok)
    assert data["name"] is None


def test_fragenkatalog_wird_geprueft() -> None:
    base = {"id": "Q", "text": "t", "kind": "text"}
    with pytest.raises(ProfileError, match="Antwortart"):
        catalog_from_dict(
            {
                "version": "1",
                "steps": [{"id": "S", "title": "s", "questions": [{**base, "kind": "zahl"}]}],
            }
        )
    with pytest.raises(ProfileError, match="fehlerhaft"):
        catalog_from_dict({"version": "1"})
    with pytest.raises(ProfileError, match="Doppelte"):
        catalog_from_dict(
            {"version": "1", "steps": [{"id": "S", "title": "s", "questions": [base, base]}]}
        )
    with pytest.raises(ProfileError, match="unbekannte Frage"):
        catalog_from_dict(
            {
                "version": "1",
                "steps": [
                    {
                        "id": "S",
                        "title": "s",
                        "questions": [{**base, "show_if": {"question": "X", "in": ["ja"]}}],
                    }
                ],
            }
        )
    with pytest.raises(ProfileError, match="genau eine"):
        catalog_from_dict(
            {
                "version": "1",
                "steps": [
                    {"id": "S", "title": "s", "questions": [{**base, "show_if": {"in": ["ja"]}}]}
                ],
            }
        )
    catalog = load_catalog()
    with pytest.raises(ProfileError):
        catalog.step("W99")


def test_navigation_und_assistentendaten() -> None:
    catalog = catalog_for(hdsig())
    with pytest.raises(ValidationError, match="Modus"):
        navigate(catalog, {}, {}, mode="schnell", step="W01")
    with pytest.raises(ValidationError, match="nicht verfügbar"):
        navigate(catalog, {}, {}, mode="frei", step="W10")
    activity = {
        "assistent": {
            "antworten": {
                "W09:gesamt_01_sonstiges_hohes_risiko": {"value": "unklar", "origin": "bestaetigt"},
                "W09:art35_3_a": {"value": "ja", "origin": "ki_vorschlag"},
                "W10-02": {"value": "notwendig", "origin": "bestaetigt"},
                "W10-02a": {"value": "unklar", "origin": "bestaetigt"},
                "kaputt": "x",
            }
        }
    }
    assert screening_answers(activity) == {
        "gesamt_01_sonstiges_hohes_risiko": {"value": "unbekannt", "justification": ""}
    }
    filtered = {
        "assistent": {
            "antworten": {
                k: v for k, v in activity["assistent"]["antworten"].items() if k != "kaputt"
            }
        }
    }
    assert assessment_texts(catalog, filtered) == {"necessity": "notwendig"}


# ---------------------------------------------------- Antworten zur DSFA


def test_dsfa_fragen_im_assistenten() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    with pytest.raises(ConflictError, match="offene Fassung"):
        world.workspace.answer(TENANT, FACH, activity_id, "W09:art35_3_a", "ja")
    started = world.assessments.start(TENANT, FACH, activity_id, world.profile)
    with pytest.raises(ValidationError, match="Person"):
        world.workspace.answer(
            TENANT, FACH, activity_id, "W09:art35_3_a", "ja", origin="ki_vorschlag"
        )
    with pytest.raises(StaleRevisionError):
        world.workspace.answer(
            TENANT, FACH, activity_id, "W09:art35_3_a", "ja", expected_revision=99
        )
    with pytest.raises(ValidationError, match="ja, nein"):
        world.workspace.answer(TENANT, FACH, activity_id, "W09:art35_3_a", "vielleicht")
    world.workspace.answer(TENANT, FACH, activity_id, "W09:art35_3_a", "ja")
    world.workspace.answer(TENANT, FACH, activity_id, "W10-02", "Notwendig, weil …")
    world.workspace.answer(TENANT, FACH, activity_id, "W10-02a", "Verhältnismäßig, weil …")
    world.workspace.answer(TENANT, FACH, activity_id, "W10-07", "Standpunkt eingeholt")
    with pytest.raises(ValidationError, match="leer"):
        world.workspace.answer(TENANT, FACH, activity_id, "W10-07", " ")
    current = world.assessments.get(TENANT, FACH, started.assessment_id)
    assert current.answers["art35_3_a"].value.value == "ja"
    assert current.necessity and current.proportionality and current.data_subject_view
    view = world.workspace.overview(TENANT, FACH, activity_id)["assistent"]
    step9 = next(s for s in view["steps"] if s["id"] == "W09")  # type: ignore[index]
    question = next(q for q in step9["questions"] if q["id"] == "W09:art35_3_a")
    assert question["value"] == "ja"


def test_ohne_dsfa_dienst_keine_dsfa_fragen() -> None:
    world = kat()
    world.workspace.assessment_service = None
    activity_id = new_register(world, full_activity())
    with pytest.raises(ConflictError, match="kein Dienst"):
        world.workspace.answer(TENANT, FACH, activity_id, "W10-02", "x")


def test_arbeitsbereich_ohne_verzeichnis_und_neue_taetigkeit() -> None:
    world = kat()
    with pytest.raises(NotFoundError):
        world.workspace.overview(TENANT, FACH, "x")
    world.workspace.create_activity(TENANT, FACH, "Erste Tätigkeit", content_if_new=cover())
    activity_id = new_register_id(world)
    with pytest.raises(NotFoundError):
        world.workspace.evaluate(TENANT, FACH, "fehlt")
    world.workspace.create_activity(TENANT, FACH, "Zweite", expected_revision=1)
    assert len(world.register.draft(TENANT, FACH).activities) == 2  # type: ignore[union-attr]
    assert activity_id


def new_register_id(world: Any) -> str:
    return str(world.register.draft(TENANT, FACH).activities[0]["id"])


# ------------------------------------------------- Übernahme und Betrieb


def test_zentrale_uebernahme_grenzfaelle() -> None:
    world = kat()
    new_register(world, full_activity())
    draft = world.register.draft(TENANT, FACH)
    with pytest.raises(ConflictError, match="freigegebene"):
        world.central.transfer(LEITUNG, draft, {})
    released = _release(world)
    exported = world.central.mark_exported(LEITUNG, released)
    assert exported.status.value == "exportiert"
    assert world.central.mark_exported(LEITUNG, released) == exported
    with pytest.raises(NotFoundError):
        world.central.confirm_takeover(ZENTRAL, TENANT, "x", central_id="1", proof="p")
    with pytest.raises(ConflictError, match="exportiert"):
        world.central.confirm_takeover(
            ZENTRAL, TENANT, transfer_key(released), central_id="1", proof="p"
        )
    world.fake_central.answer = "empfangen"
    record = world.central.transfer(LEITUNG, released, {})
    assert record.status.value == "uebertragen"
    with pytest.raises(ValidationError):
        world.central.confirm_takeover(ZENTRAL, TENANT, record.key, central_id=" ", proof="p")
    done = world.central.confirm_takeover(
        ZENTRAL, TENANT, record.key, central_id="HV-7", proof="Mail vom 01.10."
    )
    assert transfer_status(done, released).value == "uebernommen"
    assert transfer_status(done, None).value == "nicht_uebertragen"
    with pytest.raises(ValidationError):
        _status_of(Receipt("vielleicht"))
    world.central.port = None
    other = kat()
    new_register(other, full_activity())
    rel = _release(other)
    other.central.port = None
    with pytest.raises(ConflictError, match="konfiguriert"):
        other.central.transfer(LEITUNG, rel, {})
    assert isinstance(done, TransferRecord)


def test_betriebsentscheidung_grenzfaelle() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())

    def request(**over: object) -> DecisionRequest:
        base: dict[str, object] = {
            "activity_id": activity_id,
            "outcome": "abgelehnt",
            "environment": "produktion",
            "application_version": "1",
            "scope": "alle",
            "justification": TEXT,
        }
        return DecisionRequest(**{**base, **over})  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match="Ergebnis"):
        world.operations.decide(TENANT, CHEF, request(outcome="vielleicht"))
    with pytest.raises(ValidationError, match="Begründung"):
        world.operations.decide(TENANT, CHEF, request(justification="kurz"))
    with pytest.raises(ValidationError, match="Umgebung"):
        world.operations.decide(TENANT, CHEF, request(scope=" "))
    with pytest.raises(ConflictError, match="freigegebene"):
        world.operations.decide(TENANT, CHEF, request())
    _release(world)
    rejected = world.operations.decide(TENANT, CHEF, request(conditions=(" a ", "")))
    assert rejected.conditions == ("a",)
    assert world.operations.history(TENANT, CHEF, activity_id) == [rejected]
    assert world.workspace.evaluate(TENANT, FACH, activity_id).axes.operation.value == "abgelehnt"
    urgent = UrgentStart(TEXT, "2026-09-01", "Nachverfolgung")
    with pytest.raises(ConflictError, match="eingeleitete"):
        world.operations.decide(
            TENANT, CHEF, request(outcome="fuer_definierten_umfang_erteilt", urgent=urgent)
        )
    gdpr_world = kat(gdpr())
    gid = new_register(gdpr_world, full_activity(rechtsregime="dsgvo"))
    _release(gdpr_world)
    with pytest.raises(ConflictError, match="Dritten Teil"):
        gdpr_world.operations.decide(
            TENANT,
            CHEF,
            request(activity_id=gid, outcome="fuer_definierten_umfang_erteilt", urgent=urgent),
        )


# --------------------------------------------------- Prüfpaket, Sonstiges


def test_pruefpaket_nennt_stand_und_dsfa() -> None:
    world = kat()
    activity_id = new_register(world, full_activity())
    world.assessments.start(TENANT, FACH, activity_id, world.profile)
    package = review_package(world.workspace, TENANT, FACH, activity_id)
    assert package["art"] == "pruefpaket"
    assert "keine Betriebsentscheidung" not in package["stand"]["bezeichnung"]
    assert package["folgenabschaetzung"]["schema"]
    assert package["stand"]["geltungsbereich"]["taetigkeit"]


def test_hilfsfunktionen() -> None:
    assert item_text({"a": 1}) == "a: 1" and item_text(3) == "3"
    assert item_text({"empfaenger": "X"}) == "X – Rechtsgrundlage fehlt"
    assert public_findings({"liste": ["kontakt@example.org"], "zahl": 3}) == (
        "dokument.liste[0]: E-Mail-Adresse",
    )
    hints = duplicate_hints(
        [
            {"id": "a", "name": "A", "hausverzeichnis_referenz": "HV-1"},
            {"id": "b", "name": "B", "hausverzeichnis_referenz": "HV-1"},
        ]
    )
    assert hints == ("b verweist auf denselben Hausverzeichniseintrag wie a.",)
    axes = kat().workspace  # Konstruktion ohne Fehler
    assert axes.catalog.version
    assert set(StatusAxes.__dataclass_fields__) == {
        "documentation",
        "necessity",
        "dpia_work",
        "consultation",
        "transfer",
        "operation",
    }
