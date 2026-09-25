"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_dataprotection import (
    Actor,
    AssessmentService,
    FourEyesViolation,
    Permission,
    RegisterService,
    available_profiles,
    finalize_consultation,
    legacy,
    load_profile,
    propose,
)
from auditcore_dataprotection.export import assessment_report, render_assessment_html
from auditcore_dataprotection.memory import (
    FixedClock,
    InMemoryAssessmentRepository,
    InMemoryRegisterRepository,
    ListAuditSink,
    RoleAuthorizer,
    SequentialIds,
)


def main() -> None:
    """Create a register, calculate and release a DPIA, reproduce a legacy result."""
    package = distribution("auditcore_dataprotection")
    assert package.version == "0.4.2"
    assert not [r for r in package.requires or [] if "extra ==" not in r]
    assert find_spec("auditcore") is None
    assert available_profiles() == (
        ("auditcore.dsgvo", "2026.10.1"),
        ("auditcore.dsgvo", "2026.10.2"),
        ("auditcore.dsgvo", "2026.10.3"),
        ("auditcore.hdsig_ji", "2026.10.1"),
        ("auditcore.hdsig_ji", "2026.10.2"),
        ("auditcore.hdsig_ji", "2026.10.3"),
        ("regulierung.dsgvo", "2026.09.1"),
        ("regulierung.hdsig_ji", "2026.09.1"),
    )
    profile = load_profile("regulierung.dsgvo", "2026.09.1")
    assert propose(profile, {}).recommendation == "unvollstaendig"
    assert legacy.legacy_preview({}, [], "dsgvo")["empfehlung"] == "nur_schwellwert"

    everything = frozenset(Permission)
    authorizer = RoleAuthorizer({"all": everything})
    anna = Actor("anna", frozenset({"t1"}), frozenset({"all"}))
    bert = Actor("bert", frozenset({"t1"}), frozenset({"all"}))
    dora = Actor("dora", frozenset({"t1"}), frozenset({"all"}))
    clock, ids, audit = FixedClock(), SequentialIds(), ListAuditSink()
    registers_repo = InMemoryRegisterRepository()
    registers = RegisterService(registers_repo, authorizer, audit, clock, ids, profile)
    activity = {
        "name": "Preisaufsicht",
        "zweck": "Vollzug",
        "ermaechtigungsgrundlage": "Gesetz",
        "kategorien_betroffene": "Betreiber",
        "kategorien_daten": "Preise",
        "kategorien_empfaenger": "keine",
        "speicherdauer": "10 Jahre",
        "tom": "Rollen, Verschlüsselung",
        "drittlandtransfer": False,
        "besondere_kategorien": False,
        "daten_art10": False,
        "anzahl_betroffene": 250,
    }
    content = {
        "deckblatt": {"verantwortlicher": {"name": "Behörde"}, "dsb": {"name": "DSB"}},
        "referate": [],
        "taetigkeiten": [activity],
    }
    draft = registers.save_draft("t1", anna, content)
    try:
        registers.release("t1", anna, expected_revision=draft.revision)
    except FourEyesViolation:
        pass
    else:
        raise AssertionError("Self-release of the register must fail")
    released = registers.release("t1", bert, expected_revision=draft.revision)
    activity_id = released.activities[0]["id"]

    service = AssessmentService(
        InMemoryAssessmentRepository(), registers_repo, authorizer, audit, clock, ids
    )
    dsfa = service.start("t1", anna, activity_id, profile)
    answers = {key: False for key in profile.question_keys} | {"art35_3_a": True}
    scenario = {
        "dimension": "vertraulichkeit",
        "description": "Unbefugter Zugriff",
        "severity": 3,
        "likelihood": 4,
        "measures": ["zugriffskontrolle"],
    }
    dsfa = service.update(
        "t1",
        anna,
        dsfa.assessment_id,
        expected_revision=dsfa.revision,
        answers=answers,
        scenarios=[scenario],
        necessity="Erforderlich für den gesetzlichen Vollzug.",
        proportionality="Mildere Mittel geprüft.",
    )
    assert dsfa.proposal["recommendation"] == "freigabe_mit_auflagen"
    dsfa = service.decide(
        "t1",
        anna,
        dsfa.assessment_id,
        expected_revision=dsfa.revision,
        decision="freigabe_mit_auflagen",
    )
    dsfa = service.record_dpo_statement(
        "t1",
        dora,
        dsfa.assessment_id,
        expected_revision=dsfa.revision,
        vote="zugestimmt",
        statement="Keine Einwände.",
    )
    dsfa = service.release("t1", bert, dsfa.assessment_id, expected_revision=dsfa.revision)
    assert dsfa.locked and dsfa.released_by == "bert"
    html = render_assessment_html(assessment_report(dsfa, profile))
    assert "Datenschutz-Folgenabschätzung" in html and "regulierung.dsgvo" in html
    assert "assessment.released" in audit.actions()

    # DP-C21: profile 2026.10.2 gives only a preliminary consultation notice.
    a5 = load_profile("auditcore.dsgvo", "2026.10.2")
    high = {**scenario, "severity": 4, "likelihood": 4, "measures": []}
    preliminary = propose(a5, {k: False for k in a5.question_keys} | {"art35_3_a": True}, [high])
    assert preliminary.recommendation == "konsultation_aufsichtsbehoerde"
    assert preliminary.consultation_required is False
    assert preliminary.consultation_notice is not None
    assert preliminary.consultation_notice["status"] == "voraussichtlich_erforderlich"
    final = finalize_consultation(a5, preliminary.to_dict(), "konsultation_aufsichtsbehoerde")
    assert final["consultation_required"] is True
    assert final["consultation_notice"]["final"] is True
    print("PASS: installed auditcore_dataprotection register, DPIA release and legacy contract")


if __name__ == "__main__":
    main()
