"""Write the packaged profiles from the characterized constants of the sources.

Values that the capture tool read from the executed originals come from
``tests/fixtures/legacy_observed.json`` (``constants``); the remaining values
are literal transcriptions of the pinned source lines named in each profile.
Run after ``tools/capture_legacy.py``::

    python tools/build_profiles.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src" / "auditcore_registry_sources" / "profile_data"
OBSERVED = json.loads((ROOT / "tests" / "fixtures" / "legacy_observed.json").read_text())
SCHEMA = "auditcore_registry_sources.profile/1"
VERSION = "2026.09.1"
LEGAL = (
    "Aus der Quellanwendung übernommenes, charakterisiertes Softwareverhalten; "
    "keine fachliche Freigabe der Schwellen, Gewichte oder Urteile."
)

DESIGNER = {
    "repository": "janpow77/audit_designer",
    "commit": "1254591156d3bdf6ccdf4050dec7713a61ad4a20",
    "path": "backend/app/core/shared/research/register/sanctions.py",
    "git_blob": "5c064ddecb473b3f1a4341a0dc6513268d106295",
    "rights": "USER_AUTHORIZED_MIT",
}
WORKSHOP = {
    "repository": "janpow77/flowworkshop",
    "commit": "3d1cb40221645935c323392d70d84102d05ac7bb",
    "path": "auditworkshop/backend/services/sanctions_service.py",
    "git_blob": "5b9de79484373428f45ddeb879a497b671a29e1c",
    "rights": "USER_AUTHORIZED_MIT",
}
FI = "backend/app/services/fraud_detection/"
FLOWINVOICE = {
    "repository": "janpow77/flowinvoice",
    "commit": "fb2d18568d2eaf64574d131ceae51a936b9aac02",
    "rights": "USER_AUTHORIZED_MIT",
}
FLOWSEARCH = {
    "repository": "janpow77/flowsearch",
    "commit": "10cb2a3ead3892cbf9fa94f2ed18763187d3e0e4",
    "rights": "USER_AUTHORIZED_MIT",
}
OPENSANCTIONS_TERMS = (
    "OpenSanctions-Massendaten stehen unter CC BY-NC 4.0 (nicht kommerziell; "
    "kommerzielle Nutzung nur mit Lizenz). Geprüft am 2026-09-23 auf "
    "opensanctions.org/licensing. Die in der Quellanwendung genannte Lizenz "
    "bezieht sich auf die Ursprungsliste, nicht auf den Bezug über OpenSanctions."
)


def un(value: Any) -> Any:
    """Inverse of the capture tool's type-preserving JSON form."""
    if isinstance(value, dict):
        if "$dict" in value:
            return {un(k): un(v) for k, v in value["$dict"]}
        if "$float" in value:
            return float(value["$float"])
        if "$tuple" in value:
            return [un(v) for v in value["$tuple"]]
        return {k: un(v) for k, v in value.items()}
    if isinstance(value, list):
        return [un(v) for v in value]
    return value


CONSTANTS = un(OBSERVED["constants"])


def write(
    profile_id: str,
    kind: str,
    status: str,
    source: dict[str, Any],
    settings: Any,
    decisions: list[dict[str, Any]] | None = None,
) -> None:
    document = {
        "schema": SCHEMA,
        "id": profile_id,
        "version": VERSION,
        "kind": kind,
        "status": status,
        "legal_status": LEGAL,
        "source": source,
        "settings": settings,
        "decisions": decisions or [],
    }
    path = OUT / f"{profile_id}-{VERSION}.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def lists() -> None:
    designer_lists = []
    for item in CONSTANTS["audit_designer"]["lists"]:
        designer_lists.append(
            {
                "key": item["key"],
                "source_key": item["quelle"],
                "name": item["name"],
                "issuer": item["herausgeber"],
                "url": item["download_url"],
                "format": "opensanctions_targets_simple_csv",
                "provider": "OpenSanctions",
                "licence_claimed_in_source": item["lizenz"],
                "data_licence": {"status": "REVIEW_REQUIRED", "note": OPENSANCTIONS_TERMS},
            }
        )
    write(
        "audit_designer.sanctions_lists",
        "list_catalog",
        "SOURCE_CHARACTERIZED",
        {**DESIGNER, "symbols": ["Sanktionsliste", "SANKTIONSLISTEN"]},
        {"lists": designer_lists},
    )
    workshop_lists = []
    for item in CONSTANTS["flowworkshop"]["lists"]:
        workshop_lists.append(
            {
                "key": item["key"],
                "source_key": item["key"],
                "name": item["display_name"],
                "issuer": item["issuer"],
                "url": item["download_url"],
                "format": "opensanctions_targets_simple_csv",
                "provider": "OpenSanctions",
                "licence_claimed_in_source": item["license"],
                "data_licence": {"status": "REVIEW_REQUIRED", "note": OPENSANCTIONS_TERMS},
            }
        )
    write(
        "flowworkshop.sanctions_lists",
        "list_catalog",
        "SOURCE_CHARACTERIZED",
        {**WORKSHOP, "symbols": ["SanctionsSource", "DEFAULT_SANCTIONS_SOURCES"]},
        {"lists": workshop_lists},
    )
    urls = CONSTANTS["flowinvoice"]["urls"]
    official = [
        {
            "key": "eu_fsf",
            "source_key": "eu_fsf",
            "name": "Konsolidierte Finanzsanktionsliste der Union (FSF), XML 1.1",
            "issuer": "Europäische Kommission (FPI)",
            "url": urls["eu_fsf"],
            "format": "eu_fsf_xml",
            "provider": "Europäische Kommission",
            "licence_claimed_in_source": None,
            "data_licence": {
                "status": "REVIEW_REQUIRED",
                "note": "Weiterverwendung von Kommissionsdokumenten (Beschluss 2011/833/EU); "
                "Bedingungen der FSF-Datei und des Abruf-Tokens nicht geprüft.",
            },
        },
        {
            "key": "ofac_sdn",
            "source_key": "ofac_sdn",
            "name": "Specially Designated Nationals List (SDN), XML",
            "issuer": "US-Finanzministerium, OFAC",
            "url": urls["ofac_sdn"],
            "format": "ofac_sdn_xml",
            "provider": "OFAC Sanctions List Service",
            "licence_claimed_in_source": None,
            "data_licence": {
                "status": "REVIEW_REQUIRED",
                "note": "Werk einer US-Bundesbehörde, in den USA gemeinfrei; nicht geprüft.",
            },
        },
        {
            "key": "un_sc",
            "source_key": "un_sc",
            "name": "Konsolidierte Liste des UN-Sicherheitsrats, XML",
            "issuer": "Sicherheitsrat der Vereinten Nationen",
            "url": urls["un_sc"],
            "format": "un_sc_xml",
            "provider": "Vereinte Nationen",
            "licence_claimed_in_source": None,
            "data_licence": {
                "status": "REVIEW_REQUIRED",
                "note": "Nutzungsbedingungen der Vereinten Nationen nicht geprüft.",
            },
        },
    ]
    write(
        "official.sanctions_lists",
        "list_catalog",
        "SOURCE_CHARACTERIZED",
        {
            **FLOWINVOICE,
            "path": FI + "sanctions_downloader.py",
            "git_blob": "54b2bf7352c6bf68ce12cc68e5df57df081ba2d5",
            "symbols": ["SanctionsDownloader.EU_FSF_URL", "OFAC_SDN_URL", "UN_SC_URL"],
            "also": "audit-portal@ac1ccc7 app/services/fraud_detection/sanctions_downloader.py "
            "(gleiche Adressen, Parser nach audit_prep/sanctions_xml.py ausgelagert)",
        },
        {"lists": official},
    )


def screening() -> None:
    designer = CONSTANTS["audit_designer"]
    method = un(next(c for c in OBSERVED["cases"] if c["name"] == "designer-method")["output"])
    write(
        "audit_designer.sanctions_screening",
        "screening",
        "SOURCE_CHARACTERIZED",
        {
            **DESIGNER,
            "symbols": [
                "STANDARD_MINDESTWERT",
                "_BONUS_GEBURTSJAHR",
                "_MALUS_GEBURTSJAHR",
                "_BONUS_LAND",
                "_MALUS_LAND",
                "_beruecksichtige_geburtsdatum_und_land",
                "Listenindex.suche",
                "SanktionslistenDienst.suche",
                "SanctionsScreeningProvider._name/_mindestwert/_entity_schema",
            ],
        },
        {
            "algorithm": "rapidfuzz_token_set",
            "normalization": {"id": "audit_designer.sanctions", "version": "2026.09.2"},
            "lists": {"id": "audit_designer.sanctions_lists", "version": VERSION},
            "default_min_score": designer["minimum_score"],
            "min_score_range": [50.0, 100.0],
            "min_query_length": 3,
            "per_list_limit": {"floor": None, "factor": 1},
            "extract_limit": {"floor": 5, "factor": 8},
            "alias_output_cap": 8,
            "date_of_birth": {
                "compare": "year",
                "bonus": designer["dob_bonus"],
                "malus": designer["dob_malus"],
            },
            "country": {"bonus": designer["country_bonus"], "malus": designer["country_malus"]},
            "score_range": [0.0, 100.0],
            "entity_schemas": ["Person", "Organization"],
            "rows_without_id_or_name": "skip",
            "empty_list": "not_searched",
            "stored_comparison_form": "recompute",
            "notice": designer["hint"],
            "limitations": [designer["limitations_extra"], *method["grenzen"][2:]],
            "method_title": method["titel"],
        },
        [
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "Methodenbeschreibung",
                "text": "Der Werkzeugeintrag (registry.py) beschreibt „phonetische und unscharfe "
                "Varianten“, der Dienst selbst sagt „Ein phonetisches Verfahren ist nicht im "
                "Einsatz“. Diese Bibliothek übernimmt nur die zweite, zutreffende Aussage.",
            }
        ],
    )
    workshop = CONSTANTS["flowworkshop"]
    write(
        "flowworkshop.sanctions_screening",
        "screening",
        "SOURCE_CHARACTERIZED",
        {
            **WORKSHOP,
            "symbols": [
                "_DOB_MATCH_BONUS",
                "_DOB_CONFLICT_MALUS",
                "_COUNTRY_MATCH_BONUS",
                "_COUNTRY_CONFLICT_MALUS",
                "_adjust_score_for_dob_country",
                "SanctionsListIndex.search",
                "MultiSanctionsService.search",
                "routers/sanctions.py:SANCTIONS_DEFAULT_MIN_SCORE",
            ],
        },
        {
            "algorithm": "rapidfuzz_token_set",
            "normalization": {"id": "flowworkshop.sanctions", "version": "2026.09.2"},
            "lists": {"id": "flowworkshop.sanctions_lists", "version": VERSION},
            "default_min_score": workshop["router_default_min_score"],
            "service_default_min_score": workshop["service_default_min_score"],
            "min_score_range": [40.0, 100.0],
            "min_query_length": 2,
            "per_list_limit": {"floor": 5, "factor": 2},
            "extract_limit": {"floor": None, "factor": 8},
            "alias_output_cap": 8,
            "date_of_birth": {
                "compare": "year",
                "bonus": workshop["dob_bonus"],
                "malus": workshop["dob_malus"],
            },
            "country": {"bonus": workshop["country_bonus"], "malus": workshop["country_malus"]},
            "score_range": [0.0, 100.0],
            "entity_schemas": ["Person", "Organization"],
            "rows_without_id_or_name": "index",
            "empty_list": "skipped_silently",
            "stored_comparison_form": "stored_if_present",
            "notice": "Ein Treffer ist ein Prüfhinweis, keine Feststellung.",
            "limitations": [designer["limitations_extra"]],
            "method_title": "Wie der Abgleich arbeitet",
        },
        [
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "Mindestwert",
                "text": "Dienst-Voreinstellung 65, Router und Oberfläche 70; die Bibliothek "
                "übernimmt 70 als Profilwert und führt 65 nur als Beleg.",
            }
        ],
    )
    write(
        "flowinvoice.sanctions_local",
        "screening",
        "SOURCE_CHARACTERIZED",
        {
            **FLOWINVOICE,
            "path": FI + "sanctions_checker.py",
            "git_blob": "f003318086914f9d8ea53a566f40289e8e278c39",
            "symbols": ["SanctionsChecker.check_entity_local"],
        },
        {
            "algorithm": "difflib_ratio",
            "query_form": "lower_strip",
            "default_min_score": 0.75,
            "exact_from": 0.99,
            "score_digits": 3,
            "lists": {"id": "official.sanctions_lists", "version": VERSION},
        },
        [
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "Abweichende Screening-Variante",
                "text": "difflib-Ähnlichkeit 0–1 ohne Normalisierung und Rechtsformbehandlung, "
                "Schwelle 0,75; widerspricht den rapidfuzz-Profilen (0–100, Schwelle 70) des "
                "Designers und von flowworkshop.",
            }
        ],
    )
    write(
        "flowinvoice.pep_bulk",
        "screening",
        "SOURCE_CHARACTERIZED",
        {
            **FLOWINVOICE,
            "path": FI + "pep_checker.py",
            "git_blob": "58d1849a626faa00509718287f7a5b793b0d7da1",
            "symbols": ["PEPChecker.check_entity", "_match_name", "_download_and_parse"],
        },
        {
            "algorithm": "token_f1",
            "normalization": {"id": "flowinvoice.pep", "version": "2026.09.1"},
            "dataset_url": CONSTANTS["flowinvoice"]["urls"]["pep_csv"],
            "default_min_score": 0.8,
            "substring_bonus": 0.1,
            "country_bonus": 0.05,
            "country_rule": "substring_of_countries_field",
            "exact_from": 0.99,
            "score_digits": 3,
            "max_hits": 20,
            "data_licence": {"status": "REVIEW_REQUIRED", "note": OPENSANCTIONS_TERMS},
        },
        [
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "Normalisierung",
                "text": "flowinvoice.pep verliert ß, ø, ł und nicht-lateinische Schriften und "
                "widerspricht der Umschrift-Entscheidung vom 23.09.2026.",
            }
        ],
    )
    write(
        "flowinvoice.sanctions_network",
        "match_api",
        "LEGACY_ONLY",
        {
            **FLOWINVOICE,
            "path": FI + "sanctions_checker.py",
            "git_blob": "f003318086914f9d8ea53a566f40289e8e278c39",
            "symbols": ["SanctionsChecker.check_entity", "_check_sanctions_network"],
        },
        {
            "endpoint": CONSTANTS["flowinvoice"]["urls"]["sanctions_network"],
            "min_score": 0.8,
            "exact_from": 0.99,
            "rate_limit": CONSTANTS["flowinvoice"]["rate_limits"]["sanctions_network"],
            "live_check": "2026-09-23: Hostname search.sanctions.network nicht auflösbar",
        },
    )


def match_api() -> None:
    write(
        "flowsearch.opensanctions_match",
        "match_api",
        "SOURCE_CHARACTERIZED",
        {
            **FLOWSEARCH,
            "path": "backend/app/services/api_clients/sanctions.py",
            "git_blob": "ddb377633153cfa0b936bec7d709d322e079fb2f",
            "symbols": ["SanctionsAPIClient.check_sanctions", "PEPScreeningAPIClient.check_person"],
        },
        {
            "endpoint": "https://api.opensanctions.org/match/{dataset}",
            "dataset": "default",
            "local_threshold": 0.7,
            "sanctions_topic_substring": "sanction",
            "pep_topics": ["role.pep", "role.rca"],
            "sanctions_query_schema": "LegalEntity",
            "pep_query_schema": "Person",
            "default_country": "DE",
            "auth_header": "ApiKey",
            "legacy_auth": {"sanctions": None, "pep": "Bearer"},
            "response_shape": "yente 5.5.0: results[] sind Entitäten mit score (kein Feld entity)",
            "data_licence": {"status": "REVIEW_REQUIRED", "note": OPENSANCTIONS_TERMS},
        },
    )
    write(
        "flowsearch.pep_risk",
        "match_api",
        "SOURCE_CHARACTERIZED",
        {
            **FLOWSEARCH,
            "path": "backend/app/services/api_clients/pep_screening.py",
            "git_blob": "2337f4ce14804c4102e9cbf46868e5413e9a4957",
            "symbols": ["_determine_pep_type", "_assess_risk", "_categorize_pep"],
        },
        {
            "local_threshold": 0.7,
            "active_high_above": 0.9,
            "senior_keywords": ["minister", "präsident", "senator", "direktor"],
            "senior_high_above": 0.85,
            "medium_band": [0.7, 0.85],
            "low_below": 0.8,
            "labels": {
                "active": "PEP (aktiv)",
                "former": "Former PEP",
                "rca": "RCA (Relative/Close Associate)",
                "unknown": "Unknown",
            },
        },
        [
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "Risikostufen",
                "text": "Die Stufen sind Softwareregeln ohne belegte fachliche Quelle; „Former "
                "PEP“ gilt für jeden PEP ohne laufende Position, unabhängig von der Frist "
                "nach § 1 Abs. 12 ff. GwG.",
            }
        ],
    )


def ownership() -> None:
    write(
        "flowsearch.ubo",
        "ownership",
        "HUMAN_DECISION_REQUIRED",
        {
            **FLOWSEARCH,
            "path": "backend/app/services/ubo_engine.py",
            "git_blob": "15de1235fe57088aac874e3b14c4b0f36d6cb431",
            "symbols": [
                "UBOEngine.UBO_THRESHOLD",
                "MAX_DEPTH",
                "traverse_ownership",
                "identify_ubos",
                "build_ownership_chain",
            ],
        },
        {
            "share_threshold": CONSTANTS["flowsearch"]["ubo_threshold"],
            "share_comparison": "greater_than",
            "voting_threshold": 50.0,
            "voting_comparison": "greater_than",
            "max_depth": CONSTANTS["flowsearch"]["max_depth"],
            "missing_type": "person",
            "indirect_rule": "multiply_shares",
        },
        [
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "Stimmrechte",
                "text": "Quelle: Kontrolle erst ab mehr als 50 % Stimmrechten; § 3 Abs. 2 GwG "
                "nennt mehr als 25 % der Stimmrechte.",
            },
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "Mittelbare Beteiligung",
                "text": "Quelle multipliziert Anteile entlang der Kette; § 3 Abs. 2 GwG stellt "
                "bei mittelbarer Beteiligung auf Kontrolle der Zwischengesellschaft ab.",
            },
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "Fehlender Typ",
                "text": "Anteilseigner ohne Typangabe gelten in der Quelle als natürliche Person.",
            },
        ],
    )
    write(
        "flowsearch.kmu",
        "sme",
        "HUMAN_DECISION_REQUIRED",
        {
            **FLOWSEARCH,
            "path": "backend/app/services/ubo_engine.py",
            "git_blob": "15de1235fe57088aac874e3b14c4b0f36d6cb431",
            "symbols": ["UBOEngine.calculate_kmu_status"],
        },
        {
            "sme": {
                "employees_below": 250,
                "turnover_max": 50_000_000,
                "balance_sheet_max": 43_000_000,
            },
            "micro": {"employees_below": 10, "turnover_max": 2_000_000},
            "small": {"employees_below": 50, "turnover_max": 10_000_000},
            "aggregation": "none",
        },
        [
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "KMU-Schwellen",
                "text": "Die Quelle ordnet Kleinst- und Kleinunternehmen nur nach Umsatz ein; "
                "Anhang I AGVO lässt Umsatz oder Bilanzsumme genügen. Partner- und verbundene "
                "Unternehmen werden nicht zusammengerechnet (TODO der Quelle).",
            }
        ],
    )


def company_verification() -> None:
    write(
        "flowinvoice.company_verification",
        "company_verification",
        "SOURCE_CHARACTERIZED",
        {
            **FLOWINVOICE,
            "path": FI + "company_verifier.py",
            "git_blob": "a34ee1a077afbb1173210ad08bcee91db55498a0",
            "symbols": [
                "CompanyVerifier.verify_company",
                "validate_vat_id",
                "search_offene_register",
                "_names_match",
                "_normalize_company_name",
            ],
        },
        {
            "critical": ["INVALID_VAT_ID", "COMPANY_DISSOLVED"],
            "warning": ["VAT_NAME_MISMATCH", "COMPANY_INACTIVE", "NOT_IN_REGISTER"],
            "deduction": {"critical": 0.3, "warning": 0.1, "other": 0.05},
            "score_digits": 2,
            "register_countries": ["DE"],
            "name_match": {"threshold": 0.7, "leading_words": 3},
            "legal_forms": [
                "gmbh",
                "ag",
                "kg",
                "ohg",
                "ug",
                "e.k.",
                "gbr",
                "gmbh & co. kg",
                "gmbh & co kg",
                "& co. kg",
                "& co kg",
                "limited",
                "ltd",
                "inc",
                "corp",
                "llc",
            ],
            "register_status": {
                "dissolved": ["dissolved", "liquidation"],
                "active": ["registered"],
            },
            "register_query": {"max_length": 100, "limit": 5},
            "vies_endpoint": CONSTANTS["flowinvoice"]["urls"]["vies"],
            "register_endpoint": CONSTANTS["flowinvoice"]["urls"]["offeneregister"],
            "rate_limits": {
                "vies": CONSTANTS["flowinvoice"]["rate_limits"]["vies"],
                "offeneregister": CONSTANTS["flowinvoice"]["rate_limits"]["offeneregister"],
            },
        },
        [
            {
                "status": "HUMAN_DECISION_REQUIRED",
                "subject": "Gewichte",
                "text": "Abzüge 0,3/0,1/0,05 und „verifiziert = kein kritischer Indikator“ "
                "sind Softwareregeln ohne belegte fachliche Quelle.",
            }
        ],
    )


DECIDED_VERSION = "2026.09.2"
DECISION = {"status": "DECIDED", "date": "2026-09-23", "quote": "alle empfehlungen"}
DECIDED_LEGAL = (
    "Nutzerentscheidung vom 23.09.2026 („alle empfehlungen“), abgeleitet aus dem "
    "gebundenen Quellprofil; keine Rechtsauskunft, keine Freigabe einzelner Ergebnisse."
)


def decided_profile(
    base_id: str,
    purpose: str | None,
    decisions: list[dict[str, Any]],
    change: Any = None,
    legal_basis: str | None = None,
) -> None:
    """New version of a source profile as recommended profile; the source file stays as is."""
    base = json.loads((OUT / f"{base_id}-{VERSION}.json").read_text())
    document = dict(base)
    document["version"] = DECIDED_VERSION
    document["status"] = "USER_DECIDED"
    document["legal_status"] = DECIDED_LEGAL
    document["decisions"] = [{**DECISION, **d} for d in decisions]
    document["derived_from"] = {"id": base_id, "version": VERSION}
    if purpose:
        document["recommended_for"] = [purpose]
    if legal_basis:
        document["legal_basis"] = legal_basis
    settings = json.loads(json.dumps(base["settings"]))
    if change:
        change(settings)
    document["settings"] = settings
    path = OUT / f"{base_id}-{DECIDED_VERSION}.json"
    path.write_text(json.dumps(document, ensure_ascii=False, indent=1, sort_keys=True) + "\n")


def decided() -> None:
    def designer(settings: dict[str, Any]) -> None:
        settings["normalization"] = {"id": "audit_designer.sanctions", "version": "2026.09.3"}
        settings["rows_without_id_or_name"] = "skip_and_block_delisting"

    decided_profile(
        "audit_designer.sanctions_screening",
        "sanctions_screening",
        [
            {"id": "R1", "text": "Designer-Screening-Profil und -Schwellen maßgeblich."},
            {"id": "R2", "text": "Zerlegt geschriebene Umlaute werden per NFC zusammengeführt."},
            {"id": "R8", "text": "Kein Auslisten, wenn eine Lieferung fehlerhafte Zeilen hat."},
            {
                "id": "R9",
                "text": "Der Designer-Werkzeugeintrag („phonetische Varianten“) wird bei der "
                "Consumer-Migration korrigiert; es gibt kein phonetisches Verfahren.",
            },
        ],
        designer,
    )

    def workshop(settings: dict[str, Any]) -> None:
        settings["normalization"] = {"id": "flowworkshop.sanctions", "version": "2026.09.3"}

    decided_profile(
        "flowworkshop.sanctions_screening",
        None,
        [
            {
                "id": "R1",
                "text": "Maßgeblich ist das Designer-Profil; dieses Profil bleibt für "
                "flowworkshop wählbar (Mindestwert 70 wie Router und Oberfläche).",
            },
            {"id": "R2", "text": "Zerlegt geschriebene Umlaute werden per NFC zusammengeführt."},
        ],
        workshop,
    )

    def pep(settings: dict[str, Any]) -> None:
        settings["normalization"] = {"id": "flowinvoice.pep", "version": "2026.09.2"}

    decided_profile(
        "flowinvoice.pep_bulk",
        "pep_bulk",
        [
            {"id": "R3", "text": "PEP-Abgleich nach der mueller-Regel (Umschrift, NFC)."},
            {
                "id": "A2",
                "text": "OpenSanctions-Datennutzung: „abgedeckt durch Nutzung“; Lizenz "
                "CC BY-NC 4.0 bleibt genannt, Verantwortung beim Betreiber.",
            },
        ],
        pep,
    )
    decided_profile(
        "flowsearch.pep_risk",
        "pep_risk",
        [{"id": "R6", "text": "PEP-Risikostufen wie bisher (Legacy-Regeln als empfohlen)."}],
    )
    decided_profile(
        "flowinvoice.company_verification",
        "company_verification",
        [{"id": "R7", "text": "Gewichte der Firmenprüfung wie bisher (0,3/0,1/0,05)."}],
    )

    def ubo(settings: dict[str, Any]) -> None:
        settings["voting_threshold"] = 25.0
        settings["missing_type"] = "unknown"

    decided_profile(
        "flowsearch.ubo",
        "ubo",
        [
            {
                "id": "R4",
                "text": "Wirtschaftlich Berechtigte nach GwG: mehr als 25 % der Kapitalanteile "
                "oder mehr als 25 % der Stimmrechte; mittelbare Anteile werden entlang der "
                "Kette eingerechnet. Anteilseigner ohne Typ gelten nicht als natürliche "
                "Person, sondern werden zur Klärung ausgewiesen.",
            }
        ],
        ubo,
        legal_basis="§ 3 Abs. 2 GwG (mehr als 25 % der Kapitalanteile oder Stimmrechte)",
    )

    def sme(settings: dict[str, Any]) -> None:
        settings.clear()
        settings.update(
            {
                "method": "agvo_annex_i",
                "micro": {
                    "employees_below": 10,
                    "turnover_max": 2_000_000,
                    "balance_sheet_max": 2_000_000,
                },
                "small": {
                    "employees_below": 50,
                    "turnover_max": 10_000_000,
                    "balance_sheet_max": 10_000_000,
                },
                "medium": {
                    "employees_below": 250,
                    "turnover_max": 50_000_000,
                    "balance_sheet_max": 43_000_000,
                },
                "aggregation": {"linked": "full", "partner": "proportional_share"},
                "not_evaluated": [
                    "Art. 3 Abs. 4 Anhang I (Kontrolle durch öffentliche Stellen)",
                    "Art. 4 Abs. 2 Anhang I (Überschreiten in zwei aufeinanderfolgenden Jahren)",
                ],
            }
        )

    decided_profile(
        "flowsearch.kmu",
        "sme",
        [
            {
                "id": "R5",
                "text": "KMU-Einstufung nach Anhang I AGVO: Mitarbeiterzahl und Umsatz ODER "
                "Bilanzsumme je Klasse; verbundene Unternehmen voll, Partnerunternehmen "
                "anteilig zusammengerechnet.",
            }
        ],
        sme,
        legal_basis="Anhang I VO (EU) Nr. 651/2014 (AGVO), Art. 2 bis 6",
    )


def main() -> None:
    for old in OUT.glob("*.json"):
        old.unlink()
    lists()
    screening()
    match_api()
    ownership()
    company_verification()
    decided()
    print(sorted(p.name for p in OUT.glob("*.json")))


if __name__ == "__main__":
    main()
