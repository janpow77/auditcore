"""Profile: mitgelieferte Kataloge aus dem Rechtstext, eigene Profile, Auswahl je Diagramm."""

from __future__ import annotations

import copy
import json
from importlib import resources

import pytest

from auditcore_bpmn.errors import CatalogError
from auditcore_bpmn.extensions import DiagramInfo
from auditcore_bpmn.profiles import (
    STANDARD_PROFILE,
    ProfileRegistry,
    available_profiles,
    load_profile,
    load_template,
    profile_from_dict,
)


def _raw(profile_id: str = STANDARD_PROFILE) -> dict:  # type: ignore[type-arg]
    name = next(f"{i}-{v}.json" for i, v in available_profiles() if i == profile_id)
    return json.loads(resources.files("auditcore_bpmn.profiles.data").joinpath(name).read_text(encoding="utf-8"))


def test_2021_2027_catalogue_from_annex_xi() -> None:
    profile = load_profile()
    assert profile.id == STANDARD_PROFILE and profile.programming_period == "2021-2027"
    assert profile.key_requirement_numbers == tuple(range(1, 16))
    first = profile.key_requirement(1)
    assert first is not None and first.title["de"].startswith("Angemessene Aufgabentrennung")
    assert first.title["en"].startswith("Appropriate separation of functions")
    ten = profile.key_requirement("10")
    assert ten is not None and "Rechnungsführung" in ten.bodies["de"]
    two = profile.key_requirement(2)
    assert two is not None and two.footnote is not None and "Artikel 29 Absatz 3" in two.footnote["de"]
    assert profile.key_requirement_source["celex"] == "32021R1060"
    assert profile.assessment_criteria_note is not None
    assert all(not k.assessment_criteria for k in profile.key_requirements)
    assert "rfs" in profile.roles and "bb" not in profile.roles
    assert profile.funds == ("efre", "esf_plus", "kf", "jtf", "emfaf", "amif", "isf", "bmvi", "interreg")


def test_2014_2020_catalogue_from_annex_iv() -> None:
    profile = load_profile("foerderperiode-2014-2020")
    assert profile.key_requirement_numbers == tuple(range(1, 19))
    thirteen = profile.key_requirement(13)
    assert thirteen is not None and thirteen.bodies["de"] == "Bescheinigungsbehörde"
    assert thirteen.scope is not None
    assert "bb" in profile.roles and "rfs" not in profile.roles and profile.templates == ()


def test_legal_bases_and_templates_of_standard_profile() -> None:
    profile = load_profile()
    articles = {entry.article: entry for entry in profile.legal_bases if entry.article}
    assert articles["74"].short_title["de"] == "Programmverwaltung durch die Verwaltungsbehörde"
    assert articles["76"].short_title["en"] == "The accounting function"
    assert any(entry.annex == "XIII" for entry in profile.legal_bases)
    assert [t.id for t in profile.templates] == [
        "antragsverfahren",
        "verwaltungskontrolle",
        "zahlungsantrag",
        "rechnungslegung",
        "unregelmaessigkeiten",
        "vorhabenpruefung",
        "systempruefung",
    ]
    assert "<bpmn:definitions" in load_template(profile, "systempruefung")
    with pytest.raises(CatalogError):
        load_template(profile, "fehlt")


def test_roles_aliases_and_criteria() -> None:
    profile = load_profile()
    assert profile.role_from_text("Beispielbank (Zwischengeschaltete Stelle)") == "zgs"
    assert profile.role_from_text("Antragstellende") == "beg"
    assert profile.role_from_text("") is None and profile.role_from_text("Unbekannt") is None
    assert profile.role("bb") is not None and not profile.role_provided("bb")
    assert profile.criterion_known(2, "2.3") is None
    extended = profile.with_assessment_criteria({2: [("2.3", "Kriterium"), ("2.4", {"de": "K", "en": "C"})]})
    assert extended.criterion_known(2, "2.3") is True and extended.criterion_known(2, "2.9") is False
    with pytest.raises(CatalogError):
        profile.with_assessment_criteria({99: [("99.1", "x")]})
    with pytest.raises(CatalogError):
        profile.with_assessment_criteria({2: [("3.1", "falsch")]})


def test_custom_profile_and_registry_selection() -> None:
    data = _raw()
    data.update(id="eigenes-profil", version="2026.09.1", roles=[*data["roles"], "bewilligungsbank"])
    data["custom_roles"] = {"bewilligungsbank": {"labels": {"de": "Bewilligungsbank"}}}
    custom = profile_from_dict(data)
    assert custom.role("bewilligungsbank") is not None and custom.role_provided("bewilligungsbank")
    registry = ProfileRegistry([custom])
    assert registry.for_diagram(DiagramInfo(profile="eigenes-profil"))[1] == "profile"
    assert registry.for_diagram(DiagramInfo(profile="gibt-es-nicht"))[1] == "standard-unknown"
    chosen, origin = registry.for_diagram(DiagramInfo(programming_period="2014-2020"))
    assert (chosen.id, origin) == ("foerderperiode-2014-2020", "period")
    assert registry.for_diagram(None) == (registry.get(STANDARD_PROFILE), "standard")
    assert "eigenes-profil" in registry.ids


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d.update(schema="anders/1"),
        lambda d: d.update(roles=["unbekannt"]),
        lambda d: d["key_requirements"]["entries"].append(copy.deepcopy(d["key_requirements"]["entries"][0])),
        lambda d: d["key_requirements"]["entries"][0].update(assessment_criteria=[{"code": "9.1"}]),
        lambda d: d.pop("title"),
    ],
)
def test_invalid_profiles_are_rejected(change) -> None:  # type: ignore[no-untyped-def]
    data = _raw()
    change(data)
    with pytest.raises(CatalogError):
        profile_from_dict(data)


def test_unknown_profile_or_version() -> None:
    with pytest.raises(CatalogError):
        load_profile("gibt-es-nicht")
    with pytest.raises(CatalogError):
        load_profile(STANDARD_PROFILE, "1999.01.1")
    with pytest.raises(CatalogError):
        ProfileRegistry(standard="gibt-es-nicht")
