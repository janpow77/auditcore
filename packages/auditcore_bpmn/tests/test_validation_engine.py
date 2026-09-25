"""Prüflauf, Bericht, Sprachen, Deaktivieren und Vollständigkeit des Meldungskatalogs."""

from __future__ import annotations

import re
from datetime import date

import pytest
from helpers import STICHTAG, doc, fixture_text, linear

from auditcore_bpmn import validate
from auditcore_bpmn.validation import MESSAGES, RULES, SEVERITIES, ValidationConfig, rules_for
from auditcore_bpmn.validation.messages import SEVERITY_LABELS

UMLAUT_ASCII = re.compile(r"\b\w*(ae|oe|ue)\w*\b", re.IGNORECASE)
ALLOWED_ASCII = {"Quelle", "neue", "schluesselkontrolle", "true", "Sequenz", "Sequenzfluss"}


def test_report_contents_and_json() -> None:
    report = validate(fixture_text("synthetic/antragsstrecke_altbestand.bpmn"), reference_date=STICHTAG)
    assert report.profile == "foerderperiode-2021-2027@2026.09.1" and report.profile_origin == "standard"
    assert report.reference_date == "2026-09-25" and report.is_valid
    data = report.to_dict("en")
    assert data["schema"] == "auditcore_bpmn.validation-report/1" and data["valid"] is True
    assert data["counts"]["hinweis"] == len(report.notes) and data["issues"][0]["severity_label"] in ("Note", "Warning")
    assert set(report.rule_ids()) >= {"BPMN-F001", "BPMN-F002", "BPMN-F020"}


def test_complete_fixture_is_clean() -> None:
    report = validate(fixture_text("synthetic/flowaudit_1_1_vollstaendig.bpmn"), reference_date=STICHTAG)
    assert report.issues == () and report.profile_origin == "profile"


def test_disabled_rules_groups_and_default_date() -> None:
    xml = doc(linear("T1"))
    assert "BPMN-F001" not in validate(xml, ValidationConfig(disabled=frozenset({"BPMN-F001"}))).rule_ids()
    only_structure = validate(xml, ValidationConfig(groups=("structure",)))
    assert not [i for i in only_structure.rule_ids() if not i.startswith("BPMN-S")]
    assert validate(xml).reference_date == date.today().isoformat()


def test_invalid_report() -> None:
    report = validate(doc('<bpmn:task id="T" name="A"/>'), reference_date=STICHTAG)
    assert not report.is_valid and {i.rule_id for i in report.errors} == {"BPMN-S010", "BPMN-S011"}
    assert report.warnings == () or all(i.severity == "warnung" for i in report.warnings)


def test_every_registered_rule_id_has_a_message_and_vice_versa() -> None:
    registered = {rule_id for r in RULES for rule_id in r.rule_ids if not rule_id.endswith("…")}
    assert registered <= set(MESSAGES)
    catalog = {m for m in MESSAGES if not m.startswith(("BPMN-K", "BPMN-FT-"))}
    assert catalog <= registered
    assert {r.group for r in RULES} == {"structure", "content", "audit_authority", "segregation"}
    assert all(r.name.startswith("check_") for r in rules_for("structure"))


@pytest.mark.parametrize("rule_id", sorted(MESSAGES))
def test_messages_bilingual_german_with_umlauts(rule_id: str) -> None:
    message = MESSAGES[rule_id]
    assert message.severity in SEVERITIES and message.de and message.en and message.de != message.en
    text = re.sub(r"{\w+}", "", message.de)
    words = {m.group(0) for m in UMLAUT_ASCII.finditer(text)} - ALLOWED_ASCII
    assert not words, words
    assert "Findung" not in message.de and "VKO" not in message.de
    placeholders = set(re.findall(r"{(\w+)}", message.de))
    assert placeholders == set(re.findall(r"{(\w+)}", message.en))


def test_severity_labels() -> None:
    assert {k: v["de"] for k, v in SEVERITY_LABELS.items()} == {
        "fehler": "Fehler",
        "warnung": "Warnung",
        "hinweis": "Hinweis",
    }
