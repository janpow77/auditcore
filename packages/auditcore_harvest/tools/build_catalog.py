"""Build ``catalogs/sources.json`` from verified checkouts.

For every origin the tool checks that the checkout is clean, that its HEAD
equals the GitHub default-branch head (``git ls-remote``), that the file
exists and that every named symbol occurs in it. Anything that cannot be
verified is written as ``UNKNOWN`` instead of being guessed. Licence/access
review stays ``REVIEW_REQUIRED`` until a documented review exists; live tests
stay ``NOT_EXECUTED``/``NOT_CONFIGURED``.

    python tools/build_catalog.py <repositories-dir> src/auditcore_harvest/catalogs/sources.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

VERSION = "2026.09.1"

# (source_id, title, family, target_package, auth, [(repo, path, [symbols])], consumers, note)
SPEC: list[tuple[str, str, str, str, str, list[tuple[str, str, list[str]]], list[str], str]] = [
    (
        "legal.dip_bundestag",
        "Bundestag DIP",
        "legal",
        "auditcore_legal_sources",
        "api_key",
        [
            ("auditdatabase", "backend/app/harvester/dip.py", ["DIPHarvester"]),
            ("audit_designer", "backend/app/modules/vp_ai/harvester/bundestag_dip.py", []),
        ],
        ["auditdatabase services/scheduler_service.py", "audit_designer harvester/scheduler.py"],
        "Code enthält einen fest eingetragenen öffentlichen DIP-Schlüssel; nicht übernehmen, "
        "über Credential-Provider beziehen.",
    ),
    (
        "legal.eurlex",
        "EUR-Lex",
        "legal",
        "auditcore_legal_sources",
        "unknown",
        [
            ("auditdatabase", "backend/app/harvester/eurlex.py", ["EURLexHarvester"]),
            ("audit_designer", "backend/app/modules/vp_ai/harvester/eurlex.py", []),
        ],
        ["auditdatabase services/scheduler_service.py", "audit_designer harvester/scheduler.py"],
        "",
    ),
    (
        "legal.curia",
        "CURIA (EuGH)",
        "legal",
        "auditcore_legal_sources",
        "unknown",
        [
            ("auditdatabase", "backend/app/harvester/rss.py", ["CURIAHarvester"]),
            ("audit_designer", "backend/app/modules/vp_ai/harvester/curia.py", []),
        ],
        ["auditdatabase services/scheduler_service.py"],
        "",
    ),
    (
        "legal.eca",
        "Europäischer Rechnungshof (ECA)",
        "legal",
        "auditcore_legal_sources",
        "unknown",
        [
            ("auditdatabase", "backend/app/harvester/rss.py", ["ECAHarvester"]),
            ("audit_designer", "backend/app/modules/vp_ai/harvester/eca.py", []),
        ],
        ["auditdatabase services/scheduler_service.py"],
        "",
    ),
    (
        "legal.olaf",
        "OLAF",
        "legal",
        "auditcore_legal_sources",
        "unknown",
        [
            ("auditdatabase", "backend/app/harvester/international.py", ["OLAFHarvester"]),
            ("audit_designer", "backend/app/modules/vp_ai/harvester/olaf.py", []),
        ],
        ["auditdatabase services/scheduler_service.py"],
        "",
    ),
    (
        "legal.gesetze_im_internet",
        "Gesetze im Internet",
        "legal",
        "auditcore_legal_sources",
        "unknown",
        [("audit_designer", "backend/app/modules/vp_ai/harvester/gesetze_im_internet.py", [])],
        ["audit_designer harvester/scheduler.py"],
        "",
    ),
    (
        "legal.hessenrecht",
        "Hessenrecht",
        "legal",
        "auditcore_legal_sources",
        "unknown",
        [("audit_designer", "backend/app/modules/vp_ai/harvester/hessenrecht.py", [])],
        ["audit_designer harvester/scheduler.py"],
        "",
    ),
    (
        "legal.brh",
        "Bundesrechnungshof",
        "legal",
        "auditcore_legal_sources",
        "unknown",
        [
            ("auditdatabase", "backend/app/harvester/rechnungshoefe.py", ["BRHHarvester"]),
            ("audit_designer", "backend/app/modules/vp_ai/harvester/brh.py", []),
        ],
        ["auditdatabase services/scheduler_service.py"],
        "",
    ),
    (
        "legal.landesrechnungshoefe",
        "Landesrechnungshöfe (16 Profile)",
        "legal",
        "auditcore_legal_sources",
        "unknown",
        [
            (
                "auditdatabase",
                "backend/app/harvester/landesrechnungshoefe.py",
                ["LRHHessenHarvester"],
            ),
            ("audit_designer", "backend/app/modules/vp_ai/harvester/landesrechnungshoefe.py", []),
        ],
        ["auditdatabase services/scheduler_service.py"],
        "Je Landesrechnungshof ein eigenes Quellenprofil anzulegen.",
    ),
    (
        "legal.pruefverbaende",
        "Prüfverbände (IIA, IDW, DIIR)",
        "legal",
        "auditcore_legal_sources",
        "unknown",
        [
            ("audit_designer", "backend/app/modules/vp_ai/harvester/iia.py", []),
            ("audit_designer", "backend/app/modules/vp_ai/harvester/idw.py", []),
            ("audit_designer", "backend/app/modules/vp_ai/harvester/diir.py", []),
        ],
        ["audit_designer harvester/scheduler.py"],
        "",
    ),
    (
        "legal.rss_profile",
        "Vorhandene RSS-Profile (u. a. BaFin)",
        "legal",
        "auditcore_legal_sources",
        "none",
        [("auditdatabase", "backend/app/harvester/rss.py", ["BaFinHarvester"])],
        ["auditdatabase services/scheduler_service.py"],
        "",
    ),
    (
        "procurement.ted",
        "TED (Tenders Electronic Daily)",
        "procurement",
        "auditcore_procurement",
        "unknown",
        [
            ("audit-portal", "backend/app/services/ted_harvester_service.py", ["build_ted_query"]),
            ("audit-portal", "backend/audit_prep/ted_normalize.py", []),
            ("flowinvoice", "company_records.py", ["_TEDClient"]),
            ("audit_designer", "backend/app/modules/vp_ai/services/company/company_records.py", []),
        ],
        ["audit-portal api/external_data.py"],
        "Zuschlags-/Gewinnerfilter ist keine TED-Vollabdeckung.",
    ),
    (
        "procurement.had",
        "HAD (Hessische Ausschreibungsdatenbank)",
        "procurement",
        "auditcore_procurement",
        "unknown",
        [
            ("flowinvoice", "company_records.py", ["_HADClient", "HADNotice"]),
            (
                "audit_designer",
                "backend/app/modules/vp_ai/services/company/company_records.py",
                ["_HADClient"],
            ),
        ],
        ["flowinvoice company_records.py"],
        "Unterschiedliche Suchpfade in Flowinvoice und Designer.",
    ),
    (
        "funding.eu_beneficiaries",
        "EU-Begünstigtendaten (Kohäsion/FTS)",
        "funding",
        "auditcore_funding_sources",
        "unknown",
        [
            (
                "flowsearch",
                "backend/app/services/eu_beneficiary_harvester_v2.py",
                ["EUBeneficiaryHarvesterV2"],
            ),
            (
                "flowworkshop",
                "auditworkshop/backend/services/beneficiary_harvester.py",
                ["parse_xlsx_or_csv", "compute_record_hash"],
            ),
            ("audit_designer", "backend/app/core/shared/research/register/beneficiaries.py", []),
        ],
        ["flowsearch harvest_eu_beneficiaries_v2.py", "flowworkshop routers/beneficiaries.py"],
        "smart/full-refresh/force/snapshot bleiben getrennte Profile.",
    ),
    (
        "funding.state_aid",
        "State Aid Transparency",
        "funding",
        "auditcore_funding_sources",
        "unknown",
        [
            ("flowsearch", "backend/app/services/state_aid_harvester.py", ["StateAidHarvester"]),
            (
                "flowworkshop",
                "auditworkshop/backend/services/state_aid_service.py",
                ["parse_amount", "parse_date"],
            ),
            ("audit_designer", "backend/app/core/shared/research/register/state_aid.py", []),
        ],
        ["flowsearch harvest_state_aid.py"],
        "",
    ),
    (
        "funding.de_minimis_eaid",
        "De-minimis / eAidRegister",
        "funding",
        "auditcore_funding_sources",
        "unknown",
        [
            (
                "audit_designer",
                "backend/app/core/shared/research/register/de_minimis.py",
                ["EAidRegisterClient", "berechne_kumulierung"],
            ),
            (
                "audit_designer",
                "backend/app/core/shared/research/register/de_minimis_ernte.py",
                ["ernte"],
            ),
        ],
        ["audit_designer register/de_minimis_ernte.py"],
        "Eigenes Profil neben State Aid; Kumulierung ist ein getrennter Fachvertrag.",
    ),
    (
        "registry.openregister",
        "OpenRegister",
        "registry",
        "auditcore_registry_sources",
        "unknown",
        [
            (
                "flowsearch",
                "backend/app/services/api_clients/openregister.py",
                ["OpenRegisterAPIClient"],
            )
        ],
        ["flowsearch services/recherche_orchestrator.py"],
        "",
    ),
    (
        "registry.handelsregister",
        "Handelsregister",
        "registry",
        "auditcore_registry_sources",
        "unknown",
        [
            (
                "flowsearch",
                "backend/app/services/api_clients/handelsregister.py",
                ["HandelsregisterAPIClient"],
            ),
            ("regulierung", "backend/app/services/external_apis/handelsregister.py", []),
            ("audit-portal", "backend/app/services/handelsregister_service.py", []),
        ],
        ["flowsearch services/recherche_orchestrator.py"],
        "Tatsächlichen Provider je Profil prüfen.",
    ),
    (
        "registry.sanctions",
        "Sanktionslisten",
        "registry",
        "auditcore_registry_sources",
        "unknown",
        [("flowsearch", "backend/app/services/api_clients/sanctions.py", ["SanctionsAPIClient"])],
        ["flowsearch api/screening.py"],
        "",
    ),
    (
        "registry.pep",
        "PEP-Screening",
        "registry",
        "auditcore_registry_sources",
        "unknown",
        [
            (
                "flowsearch",
                "backend/app/services/api_clients/pep_screening.py",
                ["PEPScreeningAPIClient"],
            )
        ],
        ["flowsearch api/screening.py"],
        "",
    ),
    (
        "price.bundesbank",
        "Deutsche Bundesbank",
        "price",
        "auditcore_price_sources",
        "unknown",
        [("regulierung", "backend/app/services/external_apis/bundesbank.py", [])],
        ["regulierung api/admin/external_apis.py"],
        "",
    ),
    (
        "price.destatis_genesis",
        "Destatis GENESIS",
        "price",
        "auditcore_price_sources",
        "token",
        [
            (
                "regulierung",
                "backend/app/services/external_apis/destatis_genesis.py",
                ["DestatisGenesisConnector"],
            )
        ],
        ["regulierung api/admin/external_apis.py"],
        "Consumer-Integration über auditcore_harvest in regulierung (anwendungseigener Adapter).",
    ),
    (
        "price.eia_brent",
        "EIA Brent",
        "price",
        "auditcore_price_sources",
        "unknown",
        [("regulierung", "backend/app/services/external_apis/eia_brent.py", [])],
        ["regulierung api/admin/external_apis.py"],
        "",
    ),
    (
        "price.eu_oil_bulletin",
        "EU Oil Bulletin",
        "price",
        "auditcore_price_sources",
        "unknown",
        [("regulierung", "backend/app/services/external_apis/eu_oil_bulletin.py", [])],
        ["regulierung api/admin/external_apis.py"],
        "",
    ),
    (
        "price.tankerkoenig",
        "Tankerkönig",
        "price",
        "auditcore_price_sources",
        "api_key",
        [("regulierung", "backend/app/services/external_apis/tankerkoenig.py", [])],
        ["regulierung api/admin/external_apis.py"],
        "Quellkommentar nennt CC-BY; ungeprüft.",
    ),
    (
        "price.mtsk",
        "MTS-K",
        "price",
        "auditcore_price_sources",
        "unknown",
        [("regulierung", "backend/app/services/external_apis/mtsk.py", [])],
        ["regulierung api/admin/external_apis.py"],
        "",
    ),
    (
        "geo.overpass",
        "Overpass (OpenStreetMap)",
        "geo",
        "auditcore_geo",
        "none",
        [("regulierung", "backend/app/services/external_apis/overpass.py", ["OverpassConnector"])],
        ["regulierung api/admin/external_apis.py"],
        "Quellkommentar nennt ODbL; ungeprüft.",
    ),
    (
        "geo.natura2000",
        "Natura 2000",
        "geo",
        "auditcore_geo",
        "unknown",
        [("flowsearch", "backend/app/services/natura2000_service.py", [])],
        ["flowsearch api/natura2000.py"],
        "",
    ),
    (
        "geo.geocoding",
        "Geocoding (vorhandene Anbindungen)",
        "geo",
        "auditcore_geo",
        "unknown",
        [
            ("flowsearch", "backend/app/services/geocoding_service.py", []),
            ("osint", "ortsdienst/dienst.py", ["haversine_km"]),
        ],
        ["flowsearch", "osint"],
        "Geocoder-Budgets bleiben beim Consumer.",
    ),
    (
        "property.bienici",
        "Bien'ici",
        "property",
        "auditcore_property_sources",
        "unknown",
        [("wohnungsmonitor", "bienici_export.py", [])],
        ["wohnungsmonitor"],
        "Zugangs-/Nutzungsrechte vor Übernahme prüfen.",
    ),
    (
        "property.citya",
        "Citya",
        "property",
        "auditcore_property_sources",
        "unknown",
        [("wohnungsmonitor", "citya_export.py", [])],
        ["wohnungsmonitor"],
        "",
    ),
    (
        "property.paruvendu",
        "ParuVendu",
        "property",
        "auditcore_property_sources",
        "unknown",
        [("wohnungsmonitor", "paruvendu_export.py", [])],
        ["wohnungsmonitor"],
        "",
    ),
    (
        "property.kleinanzeigen",
        "Kleinanzeigen",
        "property",
        "auditcore_property_sources",
        "unknown",
        [("wohnungsmonitor", "kleinanzeigen_export.py", [])],
        ["wohnungsmonitor"],
        "",
    ),
    (
        "property.inberlinwohnen",
        "inberlinwohnen",
        "property",
        "auditcore_property_sources",
        "unknown",
        [("wohnungsmonitor", "inberlinwohnen_export.py", [])],
        ["wohnungsmonitor"],
        "",
    ),
    (
        "property.zvg",
        "ZVG-Portal (Zwangsversteigerungen)",
        "property",
        "auditcore_property_sources",
        "unknown",
        [("versteigerung", "backend/app/crawler/zvg_crawler.py", ["ZvgPortal"])],
        ["versteigerung"],
        "",
    ),
]


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repositories", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    heads: dict[str, str] = {}
    for repo in sorted({o[0] for spec in SPEC for o in spec[5]}):
        checkout = args.repositories / f"janpow77__{repo}"
        head = git(checkout, "rev-parse", "HEAD")
        remote = git(checkout, "ls-remote", "origin", "HEAD").split()[0]
        clean = not git(checkout, "status", "--porcelain")
        heads[repo] = head if head == remote and clean else "UNKNOWN"
    sources: list[dict[str, Any]] = []
    for source_id, title, family, package, auth, origins, consumers, note in SPEC:
        rows = []
        for repo, path, symbols in origins:
            file = args.repositories / f"janpow77__{repo}" / path
            text = file.read_text(encoding="utf-8", errors="replace") if file.is_file() else ""
            found = [s for s in symbols if re.search(rf"\b{re.escape(s)}\b", text)]
            rows.append(
                {
                    "repository": f"janpow77/{repo}",
                    "commit": heads[repo] if file.is_file() else "UNKNOWN",
                    "path": path,
                    "symbols": found,
                    "verified": file.is_file() and len(found) == len(symbols),
                }
            )
        properties: dict[str, Any] = {"url": {"type": "string", "description": "Basisadresse"}}
        if auth in ("api_key", "token", "basic"):
            properties["credential_name"] = {
                "type": "string",
                "description": "Name des Geheimnisses beim Credential-Provider (kein Wert)",
            }
        sources.append(
            {
                "source_id": source_id,
                "title": title,
                "family": family,
                "target_package": package,
                "origins": rows,
                "consumers": consumers,
                "profile": {"version": "UNKNOWN", "snapshot_semantics": "unknown"},
                "auth": auth,
                "licence_access": {
                    "status": "REVIEW_REQUIRED",
                    "note": "Nutzungsbedingungen und Datenlizenz nicht geprüft.",
                },
                "config_schema": {"type": "object", "properties": properties},
                "fixtures": [],
                "implementation": {"status": "PLANNED", "adapter": None},
                "live_test": {"status": "NOT_EXECUTED", "date": None},
                "note": note,
            }
        )
    document = {"schema": "auditcore_harvest.catalog/1", "version": VERSION, "sources": sources}
    args.output.write_text(
        json.dumps(document, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    unverified = [s["source_id"] for s in sources if not all(o["verified"] for o in s["origins"])]
    print(
        json.dumps({"sources": len(sources), "unverified_origins": unverified}, ensure_ascii=False)
    )


if __name__ == "__main__":
    main()
