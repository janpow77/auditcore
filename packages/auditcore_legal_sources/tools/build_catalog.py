"""Write this family's entries in the ``auditcore_harvest.catalog/1`` format.

SUPPORTED entries are implemented adapters with replay fixtures; the live test
stays NOT_CONFIGURED/NOT_EXECUTED until a permitted, configured smoke test ran.
PLANNED entries are harvesters that exist in the source applications but are
not yet characterized or extracted; LEGACY_ONLY means only the legacy adapter
reproduces them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ADB = (
    "janpow77/auditdatabase",
    "bba911e918e102426d4ca2f88fd377fe8ca585e4",
    "backend/app/harvester",
)
DES = (
    "janpow77/audit_designer",
    "030a71e083ef0feddc14545b095a4945bc0bbd7a",
    "backend/app/modules/vp_ai/harvester",
)
PROFILE_SCHEMA = {
    "type": "object",
    "required": ["profile"],
    "properties": {
        "profile": {
            "type": "object",
            "description": "Profil-ID und -Version, z. B. auditdatabase.esi / 2026.09.1",
        },
    },
}
CONSUMER_ADB = {
    "repository": "janpow77/auditdatabase",
    "path": "backend/app/services/scheduler_service.py",
    "call": "get_harvester(source_id, db=db).harvest()",
}
CONSUMER_DES = {
    "repository": "janpow77/audit_designer",
    "path": "backend/app/modules/vp_ai/harvester/scheduler.py",
    "call": "get_harvester(source_id).harvest()",
}


def origin(base: tuple[str, str, str], file: str, *symbols: str) -> dict[str, object]:
    return {
        "repository": base[0],
        "commit": base[1],
        "path": f"{base[2]}/{file}",
        "symbols": list(symbols),
    }


def supported(
    source_id: str,
    title: str,
    origins: list[dict[str, object]],
    auth: str,
    licence: str,
    fixtures: list[str],
    extra: dict[str, object] | None = None,
    live: str = "NOT_EXECUTED",
    note: str = "",
) -> dict[str, object]:
    schema = json.loads(json.dumps(PROFILE_SCHEMA))
    for name, spec in (extra or {}).items():
        schema["properties"][name] = spec
    return {
        "source_id": source_id,
        "title": title,
        "family": "legal",
        "target_package": "auditcore_legal_sources",
        "origins": origins,
        "consumers": [CONSUMER_ADB, CONSUMER_DES],
        "profile": ["auditdatabase.esi@2026.09.1", "audit_designer.vp_ai@2026.09.1"],
        "auth": auth,
        "licence_access": {"status": "REVIEW_REQUIRED", "note": licence},
        "config_schema": schema,
        "fixtures": fixtures,
        "implementation": {
            "status": "SUPPORTED",
            "adapter": f"auditcore_legal_sources.adapters:{source_id}",
            "characterization": "tests/fixtures/legacy_*_observed.json",
        },
        "live_test": {"status": live, "note": note or "Kein Live-Abruf ausgeführt."},
    }


def planned(
    source_id: str,
    title: str,
    base: tuple[str, str, str],
    file: str,
    symbol: str,
    consumer: dict[str, str],
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "title": title,
        "family": "legal",
        "target_package": "auditcore_legal_sources",
        "origins": [origin(base, file, symbol)],
        "consumers": [consumer],
        "profile": "noch nicht charakterisiert",
        "auth": "unknown",
        "licence_access": {
            "status": "UNKNOWN",
            "note": "Nutzungsbedingungen der Quelle nicht geprüft.",
        },
        "config_schema": {"type": "object", "properties": {}},
        "fixtures": [],
        "implementation": {"status": "PLANNED"},
        "live_test": {"status": "NOT_EXECUTED"},
    }


def main() -> None:
    sources = [
        supported(
            "legal.dip_bundestag",
            "Bundestag DIP – Drucksachen",
            [
                origin(ADB, "dip.py", "DIPHarvester"),
                origin(DES, "bundestag_dip.py", "BundestagDIPHarvester"),
            ],
            "api_key",
            "DIP-API-Nutzungsbedingungen; API-Schlüssel beim Consumer.",
            ["tests/fixtures/replay/dip.json", "tests/fixtures/replay/dip_partial.json"],
            {
                "keywords": {"type": "array", "items": {"type": "string"}},
                "api_key": {
                    "type": "string",
                    "secret": True,
                    "description": "über CredentialProvider, nie in der Konfiguration",
                },
            },
            "NOT_CONFIGURED",
            "Kein DIP-API-Schlüssel konfiguriert; der Schlüssel "
            "im Quellcode wurde bewusst nicht verwendet.",
        ),
        supported(
            "legal.eurlex",
            "EUR-Lex (Cellar SPARQL)",
            [
                origin(ADB, "eurlex.py", "EURLexHarvester"),
                origin(DES, "eurlex.py", "EURLexHarvester"),
            ],
            "none",
            "Weiterverwendung nach Beschluss 2011/833/EU mit Quellenangabe.",
            ["tests/fixtures/replay/eurlex.json", "tests/fixtures/replay/eurlex_update.json"],
        ),
        supported(
            "legal.bafin",
            "BaFin RSS",
            [origin(ADB, "rss.py", "BaFinHarvester")],
            "none",
            "Nutzungsbedingungen der BaFin-Feeds nicht geprüft.",
            ["tests/fixtures/replay/bafin.json"],
            {"relevant_only": {"type": "boolean"}},
        ),
        supported(
            "legal.curia",
            "CURIA RSS (EuGH/EuG)",
            [origin(ADB, "rss.py", "CURIAHarvester")],
            "none",
            "Rechtshinweise curia.europa.eu nicht geprüft.",
            ["tests/fixtures/replay/curia.json"],
            {"relevant_only": {"type": "boolean"}},
        ),
        supported(
            "legal.eca",
            "Europäischer Rechnungshof – Publikationen",
            [origin(ADB, "rss.py", "ECAHarvester")],
            "none",
            "Wiederverwendungsregeln eca.europa.eu nicht geprüft.",
            ["tests/fixtures/replay/eca.json", "tests/fixtures/replay/eca_unavailable.json"],
        ),
    ]
    for key, title, file, symbol in (
        ("bundesrat", "Bundesrat", "bundesrat.py", "BundesratHarvester"),
        ("hessen_landtag", "Hessischer Landtag", "hessen_landtag.py", "HessenLandtagHarvester"),
        ("brh", "Bundesrechnungshof", "rechnungshoefe.py", "BRHHarvester"),
        (
            "landesrechnungshoefe",
            "Landesrechnungshöfe (16)",
            "landesrechnungshoefe.py",
            "LRHHessenHarvester",
        ),
        (
            "international",
            "OECD, OLAF, GRECO, UNODC, FATF, INTOSAI, EC Regio",
            "international.py",
            "OLAFHarvester",
        ),
    ):
        sources.append(
            planned(f"legal.auditdatabase_{key}", title, ADB, file, symbol, CONSUMER_ADB)
        )
    for key, title in (
        ("curia", "CURIA"),
        ("eca", "Europäischer Rechnungshof"),
        ("olaf", "OLAF"),
        ("gesetze_im_internet", "Gesetze im Internet"),
        ("hessenrecht", "Hessenrecht"),
        ("brh", "Bundesrechnungshof"),
        ("landesrechnungshoefe", "Landesrechnungshöfe"),
        ("rechnungshof_at", "Rechnungshof Österreich"),
        ("bundesrat", "Bundesrat"),
        ("hessischer_landtag", "Hessischer Landtag"),
        ("eu_parliament", "Europäisches Parlament"),
        ("eu_council", "Rat der EU"),
        ("kom_guidance", "KOM-Leitlinien"),
        ("kom_swd", "KOM-SWD"),
        ("iia", "IIA"),
        ("idw", "IDW"),
        ("ifac", "IFAC"),
        ("intosai", "INTOSAI"),
        ("eurosai", "EUROSAI"),
        ("diir", "DIIR"),
        ("acfe", "ACFE"),
        ("greco", "GRECO"),
        ("fatf", "FATF"),
        ("oecd", "OECD"),
        ("unodc", "UNODC"),
        ("eucrim", "eucrim"),
    ):
        sources.append(
            planned(f"legal.designer_{key}", title, DES, f"{key}.py", "Harvester", CONSUMER_DES)
        )
    catalog = {
        "schema": "auditcore_harvest.catalog/1",
        "version": "2026.09.1",
        "package": "auditcore_legal_sources",
        "sources": sources,
    }
    Path(sys.argv[1]).write_text(
        json.dumps(catalog, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
