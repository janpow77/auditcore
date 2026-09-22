"""Capture actual regulierung VVT/DSFA behavior before extraction.

Run with the interpreter of the legacy application (it provides SQLAlchemy,
aiosqlite, openpyxl and optionally WeasyPrint)::

    <regulierung>/backend/.venv/bin/python -I tools/capture_regulierung_legacy.py \
        <checkout>/backend tests/fixtures/regulierung_legacy_observed.json

The tool never imports ``auditcore_dataprotection``. It verifies the Git blob
of every executed source file against the pinned commit, redirects the
application settings to an in-memory SQLite database before any application
import and refuses to run if the application engine is not SQLite. Only
synthetic inputs are used; no application database, server or network access.
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import io
import json
import os
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SOURCE_REPOSITORY = "janpow77/regulierung"
SOURCE_COMMIT = "a5d48ea4b90a410210ec25e707781ef9e21ad743"
#: Git blobs verified against the GitHub contents API for SOURCE_COMMIT.
SOURCE_BLOBS = {
    "app/services/dsfa/bewertung.py": "2a34de1d708e3bd83bdd366b0f7dbf09be177a5a",
    "app/services/dsfa/katalog.py": "8be23a5163342f0f69b32f2d40b2ef2d60ba8783",
    "app/services/dsfa/verwaltung.py": "eba4ffd8965980736b8bb325c027f34faf4542ac",
    "app/services/dsfa/export.py": "e2a14999a49823813cf790843595fdbec0449801",
    "app/services/mandant_dsgvo_service.py": "992aeadc70b8f289aaf996263f93c9fe1375cc1a",
}


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


class FixedClock:
    """Deterministic replacement for ``datetime`` inside the legacy modules."""

    def __init__(self) -> None:
        self.current = datetime(2026, 9, 1, 8, 0, tzinfo=UTC)

    def tick(self) -> datetime:
        self.current += timedelta(minutes=1)
        return self.current


CLOCK = FixedClock()


class _AcceptsRealDatetimes(type):
    """Keep ``isinstance(value, datetime)`` true for values read back from the database.

    The legacy export formats dates only for ``isinstance(wert, datetime)``;
    replacing the module attribute must not turn real datetimes into "–".
    """

    def __instancecheck__(cls, instance: Any) -> bool:
        return isinstance(instance, datetime)


class FakeDatetime(datetime, metaclass=_AcceptsRealDatetimes):
    @classmethod
    def now(cls, tz: Any = None) -> datetime:  # type: ignore[override]
        value = CLOCK.tick()
        return value if tz is not None else value.replace(tzinfo=None)


def jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return {"$datetime": value.isoformat()}
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(jsonable(v) for v in value)
    return value


def error(exc: BaseException) -> dict[str, Any]:
    return {"type": type(exc).__name__, "message": str(exc)}


def workbook_cells(workbook: Any) -> dict[str, Any]:
    sheets = []
    for sheet in workbook.worksheets:
        cells = []
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None:
                    continue
                cells.append(
                    {
                        "ref": cell.coordinate,
                        "value": jsonable(cell.value),
                        "type": cell.data_type,
                        "bold": bool(cell.font and cell.font.bold),
                    }
                )
        sheets.append(
            {
                "title": sheet.title,
                "cells": cells,
                "merged": sorted(str(r) for r in sheet.merged_cells.ranges),
                "freeze_panes": sheet.freeze_panes,
                "auto_filter": sheet.auto_filter.ref,
            }
        )
    return {"sheets": sheets}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backend", type=Path, help="regulierung/backend at the pinned commit")
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--migrated",
        action="store_true",
        help="Consumer after migration: record actual blobs instead of requiring the pinned ones",
    )
    args = parser.parse_args()
    backend = args.backend.resolve()
    files = []
    for relative, expected in SOURCE_BLOBS.items():
        observed = git_blob(backend / relative)
        if observed != expected and not args.migrated:
            raise SystemExit(f"{relative} does not match the pinned GitHub blob")
        files.append(
            {
                "path": f"backend/{relative}",
                "git_blob": observed,
                "sha256": hashlib.sha256((backend / relative).read_bytes()).hexdigest(),
            }
        )
    head = subprocess.run(
        ["git", "-C", str(backend), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(backend), "status", "--porcelain", "--", "app"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if not args.migrated and (head != SOURCE_COMMIT or dirty):
        raise SystemExit("Checkout is not the clean pinned source commit")

    # Settings redirection must precede every application import.
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["HARVEST_NULLPOOL"] = "true"
    os.environ.pop("PYTHONPATH", None)
    sys.path.insert(0, str(backend))

    import app.database as database

    if not database.engine.url.drivername.startswith("sqlite"):
        raise SystemExit("Refusing to run: application engine is not an in-memory SQLite engine")

    import app.models.mandant_dsfa as dsfa_model
    import app.models.mandant_dsgvo as dsgvo_model
    from app.services import mandant_dsgvo_service as vvt
    from app.services.dsfa import bewertung as bw
    from app.services.dsfa import export as ausgabe
    from app.services.dsfa import katalog as kat
    from app.services.dsfa import verwaltung as dienst

    for module in (vvt, dienst, ausgabe, dsfa_model, dsgvo_model):
        module.datetime = FakeDatetime  # type: ignore[attr-defined]

    cases: list[dict[str, Any]] = []

    def observe(name: str, operation: str, inputs: Any, call: Any) -> None:
        before = copy.deepcopy(inputs)
        try:
            output = jsonable(call())
            exception = None
        except Exception as exc:  # noqa: BLE001 - characterization records every error
            output = None
            exception = error(exc)
        if inputs != before:
            raise AssertionError(f"{name}: legacy call mutated its input")
        cases.append(
            {
                "name": name,
                "operation": operation,
                "inputs": jsonable(inputs),
                "output": output,
                "exception": exception,
            }
        )

    def answer(key: str, ja: Any = True) -> dict[str, Any]:
        return {"schluessel": key, "ja": ja, "begruendung": "Synthetische Characterization"}

    def scenario(**values: Any) -> dict[str, Any]:
        return {
            "dimension": "vertraulichkeit",
            "beschreibung": "Synthetische Characterization",
            "schwere": 4,
            "wahrscheinlichkeit": 4,
            **values,
        }

    def threshold(inputs: dict[str, Any]) -> Any:
        return asdict(
            bw.werte_schwellwert_aus(
                [bw.Antwort(**v) for v in inputs["answers"]],
                inputs.get("regime", kat.REGIME_DSGVO),
            )
        )

    def suggestion(inputs: dict[str, Any]) -> Any:
        return bw.vorschlag_als_json(
            bw.erstelle_vorschlag(
                [bw.Antwort(**v) for v in inputs["answers"]],
                [bw.Szenario(**v) for v in inputs.get("scenarios", [])],
                inputs.get("regime", kat.REGIME_DSGVO),
            )
        )

    def risk(inputs: dict[str, Any]) -> Any:
        return asdict(bw.werte_risiko_aus([bw.Szenario(**v) for v in inputs["scenarios"]]))

    # ---------------------------------------------------------- pure core
    for regime in (kat.REGIME_DSGVO, kat.REGIME_JI):
        for name, answers in (
            ("missing-all", []),
            ("all-false", [answer(q.schluessel, False) for q in kat.KATALOG]),
            ("two-distinct-points", [answer("edsa_01_bewerten"), answer("edsa_05_umfang")]),
            ("one-point", [answer("edsa_01_bewerten")]),
            ("duplicate-one-point", [answer("edsa_01_bewerten"), answer("edsa_01_bewerten")]),
            (
                "conflicting-duplicate",
                [answer("edsa_01_bewerten"), answer("edsa_01_bewerten", False)],
            ),
            ("two-hard", [answer("art35_3_a"), answer("dsk_03_biometrie")]),
            ("hard-and-fria", [answer("art35_3_b"), answer("ki_01_hochrisiko")]),
            ("fria-only", [answer("ki_01_hochrisiko")]),
        ):
            inputs = {"answers": answers, "regime": regime}
            observe(
                f"threshold-{regime}-{name}", "threshold", inputs, lambda i=inputs: threshold(i)
            )
        for frage in kat.KATALOG:
            inputs = {"answers": [answer(frage.schluessel)], "regime": regime}
            observe(
                f"threshold-{regime}-single-{frage.schluessel}",
                "threshold",
                inputs,
                lambda i=inputs: threshold(i),
            )
        for index, scenarios in enumerate(
            (
                [],
                [scenario(schwere=1, wahrscheinlichkeit=1)],
                [scenario(schwere=2, wahrscheinlichkeit=2)],
                [scenario(schwere=1, wahrscheinlichkeit=4)],
                [scenario(schwere=1, wahrscheinlichkeit=5)],
                [scenario(schwere=3, wahrscheinlichkeit=3)],
                [scenario(schwere=2, wahrscheinlichkeit=5)],
                [scenario()],
                [scenario(), scenario(schwere=1, wahrscheinlichkeit=1, dimension="integritaet")],
            )
        ):
            for trigger in ("art35_3_a", "edsa_01_bewerten"):
                inputs = {"answers": [answer(trigger)], "scenarios": scenarios, "regime": regime}
                observe(
                    f"suggestion-{regime}-{trigger}-{index}",
                    "suggestion",
                    inputs,
                    lambda i=inputs: suggestion(i),
                )
        inputs = {"answers": [], "scenarios": [scenario()], "regime": regime}
        observe(
            f"suggestion-{regime}-empty-answers",
            "suggestion",
            inputs,
            lambda i=inputs: suggestion(i),
        )
    for name, answers in (
        ("unknown-question", [answer("UNKNOWN")]),
        ("string-false-is-truthy", [answer("art35_3_a", "false")]),
        ("null-answer", [answer("art35_3_a", None)]),
        ("zero-answer", [answer("art35_3_a", 0)]),
    ):
        inputs = {"answers": answers}
        observe(name, "threshold", inputs, lambda i=inputs: threshold(i))
    for regime in ("UNKNOWN", "", None, "DSGVO"):
        inputs = {"answers": [answer("art35_3_a")], "scenarios": [scenario()], "regime": regime}
        observe(f"unknown-regime-{regime}", "suggestion", inputs, lambda i=inputs: suggestion(i))
    for value in (-1, 0, 1, 4, 5, 9, 10, 16, 17):
        inputs = {"value": value}
        observe(
            f"risk-level-{value}", "risk_level", inputs, lambda i=inputs: bw.risikostufe(i["value"])
        )
    for severity in (-1, 0, 1, 4, 5):
        for probability in (-1, 0, 1, 4, 5):
            inputs = {"scenarios": [scenario(schwere=severity, wahrscheinlichkeit=probability)]}
            observe(
                f"risk-values-{severity}-{probability}", "risk", inputs, lambda i=inputs: risk(i)
            )
    for index, measures in enumerate(
        (
            [],
            ["UNKNOWN"],
            ["protokollierung"],
            ["protokollierung"] * 2,
            ["protokollierung"] * 3,
            ["verschluesselung", "zugriffskontrolle", "protokollierung"],
            ["pseudonymisierung", "menschliche_aufsicht", "loeschkonzept"],
            ["menschliche_aufsicht"],
            list(kat.MASSNAHMEN_JE_SCHLUESSEL),
        )
    ):
        for severity, probability in ((4, 4), (2, 2), (1, 1)):
            inputs = {
                "scenarios": [
                    scenario(massnahmen=measures, schwere=severity, wahrscheinlichkeit=probability)
                ]
            }
            observe(
                f"measures-{index}-{severity}{probability}",
                "risk",
                inputs,
                lambda i=inputs: risk(i),
            )
    for severity, probability in (
        (0, 0),
        (-1, 1),
        (1, 0),
        (5, 5),
        (4, 4),
        (None, 1),
        (1, None),
        (2, 2),
    ):
        inputs = {
            "answers": [answer("art35_3_a")],
            "scenarios": [
                scenario(
                    massnahmen=["verschluesselung"],
                    netto_schwere=severity,
                    netto_wahrscheinlichkeit=probability,
                )
            ],
        }
        observe(
            f"explicit-net-{severity}-{probability}",
            "suggestion",
            inputs,
            lambda i=inputs: suggestion(i),
        )
    for count in (None, "", "UNKNOWN", -1, 0, 9999, 10000, 10001, "10000", "1e4", True, 2.5):
        inputs = {"besondere_kategorien": True, "anzahl_betroffene": count}
        observe(
            f"prefill-count-{count!r}",
            "prefill",
            inputs,
            lambda i=inputs: bw.vorbelegung_aus_taetigkeit(i),
        )
    for value in (False, "false", None, [], ["sample"]):
        inputs = {"besondere_kategorien": value, "anzahl_betroffene": 10000}
        observe(
            f"prefill-special-{value!r}",
            "prefill",
            inputs,
            lambda i=inputs: bw.vorbelegung_aus_taetigkeit(i),
        )
    for name, inputs in (
        ("prefill-empty", {}),
        ("prefill-transfer", {"drittlandtransfer": True}),
        ("prefill-art10-large", {"daten_art10": True, "anzahl_betroffene": 50000}),
        ("prefill-large-only", {"anzahl_betroffene": 12000}),
    ):
        observe(name, "prefill", inputs, lambda i=inputs: bw.vorbelegung_aus_taetigkeit(i))
    observe("risk-empty", "risk", {"scenarios": []}, lambda: risk({"scenarios": []}))
    inputs = {"scenarios": [scenario(dimension="UNKNOWN")]}
    observe("unknown-dimension", "risk", inputs, lambda i=inputs: risk(i))

    # ------------------------------------------- administration adapter (pure)
    for name, inputs in (
        ("dict-answers", {"art35_3_a": {"ja": True, "begruendung": "B"}, "erfunden": {"ja": True}}),
        ("bool-answers", {"edsa_01_bewerten": True, "edsa_05_umfang": False}),
        ("string-false", {"art35_3_a": "false"}),
        ("dict-string-false", {"art35_3_a": {"ja": "false"}}),
        ("null", {"art35_3_a": None}),
        ("empty", {}),
    ):
        observe(
            f"answers-json-{name}",
            "answers_from_json",
            inputs,
            lambda i=inputs: [asdict(a) for a in dienst._antworten_aus_json(i)],
        )
    for name, inputs in (
        ("valid", [scenario(massnahmen=["verschluesselung"])]),
        ("string-numbers", [scenario(schwere="3", wahrscheinlichkeit="2")]),
        ("out-of-scale", [scenario(schwere=9, wahrscheinlichkeit=2)]),
        ("zero", [scenario(schwere=0, wahrscheinlichkeit=2)]),
        ("missing-values", [{"dimension": "vertraulichkeit"}]),
        ("not-a-number", [scenario(schwere="hoch")]),
        ("net-empty-string", [scenario(netto_schwere="", netto_wahrscheinlichkeit=None)]),
        ("net-out-of-scale", [scenario(netto_schwere=9, netto_wahrscheinlichkeit=0)]),
        ("non-dict-entry", ["x", scenario()]),
        ("float", [scenario(schwere=2.9, wahrscheinlichkeit=1)]),
    ):
        observe(
            f"scenarios-json-{name}",
            "scenarios_from_json",
            inputs,
            lambda i=inputs: [asdict(s) for s in dienst._szenarien_aus_json(i)],
        )
    for regime in (None, "", " dsgvo ", "dsgvo", "hdsig_ji", "DSGVO", "unbekannt"):
        observe(
            f"check-regime-{regime!r}",
            "check_regime",
            {"value": regime},
            lambda r=regime: dienst.pruefe_regime(r),
        )
    for name, inputs in (
        ("kpang", {"name": "Vollzug", "referat": "KPAnG"}),
        ("bussgeld", {"zweck": "Bußgeldverfahren"}),
        ("owi-substring", {"name": "Download-Statistik"}),
        ("markt", {"name": "Marktbeobachtung", "zweck": "Preisvergleich"}),
        ("rechtsgrundlage-field", {"rechtsgrundlage": "OWiG"}),
        ("empty", {}),
    ):
        observe(
            f"regime-suggestion-{name}",
            "regime_suggestion",
            inputs,
            lambda i=inputs: dienst.regime_vorschlag(i),
        )
    for name, before, after in (
        (
            "name-only",
            {"name": "Alt", "zweck": "Z", "ansprechperson": "A"},
            {"name": "Neu", "zweck": "Z", "ansprechperson": "B"},
        ),
        ("none-vs-empty", {"zweck": None}, {"zweck": ""}),
        ("false-vs-missing", {"drittlandtransfer": False}, {}),
        ("zero-vs-missing", {"anzahl_betroffene": 0}, {}),
        ("count-change", {"anzahl_betroffene": 10}, {"anzahl_betroffene": 11}),
        (
            "all-fields",
            {k: "a" for k in dienst.WESENTLICHE_FELDER},
            {k: "b" for k in dienst.WESENTLICHE_FELDER},
        ),
    ):
        inputs = {"before": before, "after": after}
        observe(
            f"compare-{name}",
            "compare_activity",
            inputs,
            lambda i=inputs: dienst.vergleiche_taetigkeit(i["before"], i["after"]),
        )
    for regime in (kat.REGIME_DSGVO, kat.REGIME_JI, "falsch"):
        inputs = {
            "antworten": {"art35_3_a": {"ja": True}},
            "szenarien": [
                scenario(schwere="3", wahrscheinlichkeit=4, massnahmen=["zugriffskontrolle"])
            ],
            "regime": regime,
        }
        observe(
            f"preview-{regime}",
            "preview",
            inputs,
            lambda i=inputs: dienst.berechne_vorschlag(i["antworten"], i["szenarien"], i["regime"]),
        )
    for name, inputs in (
        ("simple", {"name": "Preisaufsicht", "position": 1}),
        ("second", {"name": "Preisaufsicht", "position": 2}),
        ("case-space", {"name": "  PREISAUFSICHT ", "position": 1}),
        ("empty", {"name": "", "position": 1}),
        ("umlaut", {"name": "Überwachung", "position": 3}),
    ):
        observe(
            f"identifier-{name}",
            "activity_identifier",
            inputs,
            lambda i=inputs: vvt.taetigkeit_kennung(i["name"], i["position"]),
        )
    for name, inputs in (
        (
            "mixed",
            [
                {"name": "A"},
                {"name": "A"},
                {"name": "B", "id": "fest"},
                "kein-dict",
                {"name": "A"},
                {},
            ],
        ),
        ("empty-id", [{"name": "A", "id": ""}]),
        ("none", None),
    ):
        observe(
            f"identifiers-{name}",
            "activities_with_identifiers",
            {"activities": inputs},
            lambda i=inputs: vvt.taetigkeiten_mit_kennung(i),
        )
    werte = {"bezeichnung": "Behörde", "dsb_name": "", "plz": "", "dsb_titel": ""}
    for name, inputs in (
        ("nested", {"a": ["{{mandant:bezeichnung}}", {"b": "{{mandant:dsb_name}}"}], "c": 1}),
        ("exempt-empty", ["{{mandant:plz}}", "{{mandant:dsb_titel}}", "{{mandant:fehlt}}"]),
        ("plain", "{{mandant:bezeichnung}} und mehr"),
    ):
        observe(
            f"placeholders-{name}",
            "placeholders",
            {"value": inputs, "values": werte},
            lambda i=inputs: vvt.fuelle_platzhalter(i, werte),
        )

    # ------------------------------------------ workflow against SQLite
    transcript = asyncio.run(run_workflow(database, vvt, dienst, bw, ausgabe))

    report = {
        "status": "OBSERVED",
        "scope": "LOCAL_LEGACY_CHARACTERIZATION_NOT_LEGAL_VALIDATION",
        "source": {
            "repository": SOURCE_REPOSITORY,
            "commit": SOURCE_COMMIT,
            "files": files,
            "checkout_clean": not dirty,
            "head": head,
            "migrated": args.migrated,
            "library": _library_origin() if args.migrated else None,
        },
        "environment": {
            "python": platform.python_version(),
            "sqlalchemy": __import__("sqlalchemy").__version__,
            "openpyxl": __import__("openpyxl").__version__,
            "database": "sqlite+aiosqlite:///:memory: (isolated, created by this tool)",
            "clock": "fixed, one minute per datetime.now() call from 2026-09-01T08:00Z",
        },
        "catalog": catalog_snapshot(kat, bw, dienst, vvt),
        "cases": cases,
        "workflow": transcript,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "status": "OBSERVED",
                "cases": len(cases),
                "exceptions": sum(c["exception"] is not None for c in cases),
                "workflow_steps": len(transcript["steps"]),
                "workflow_errors": sum(s["exception"] is not None for s in transcript["steps"]),
            }
        )
    )


def _library_origin() -> dict[str, Any]:
    from importlib.metadata import distribution

    import auditcore_dataprotection

    return {
        "module": auditcore_dataprotection.__file__,
        "version": distribution("auditcore_dataprotection").version,
    }


def catalog_snapshot(kat: Any, bw: Any, dienst: Any, vvt: Any) -> dict[str, Any]:
    """Every rule constant the extraction uses, recorded from the executed source."""
    return jsonable(
        {
            "katalog_als_json": kat.katalog_als_json(),
            "fragen": [asdict(f) for f in kat.KATALOG],
            "massnahmen": [asdict(m) for m in kat.MASSNAHMEN],
            "block_titel": kat.BLOCK_TITEL,
            "regime_titel": kat.REGIME_TITEL,
            "regime_erlaeuterung": kat.REGIME_ERLAEUTERUNG,
            "regime_hinweis_ji": kat.REGIME_HINWEIS_JI,
            "normen": kat.NORMEN,
            "schwelle_punkte": kat.SCHWELLE_PUNKTE,
            "dimensionen": kat.DIMENSIONEN,
            "sdm_dimensionen": sorted(kat.SDM_DIMENSIONEN),
            "standpunkt_begruendungen": list(kat.STANDPUNKT_BEGRUENDUNGEN),
            "schwere": kat.SCHWERE,
            "wahrscheinlichkeit": kat.WAHRSCHEINLICHKEIT,
            "vorschlag_text": bw.VORSCHLAG_TEXT,
            "vorschlag_text_ji": bw.VORSCHLAG_TEXT_JI,
            "umfang_schwelle": bw.UMFANG_SCHWELLE,
            "mindestlaenge_begruendung": dienst.MINDESTLAENGE_BEGRUENDUNG,
            "wesentliche_felder": dienst.WESENTLICHE_FELDER,
            "standard_referat": dienst.STANDARD_REFERAT,
            "verzeichnis_spalten": vvt._VERZEICHNIS_SPALTEN,
            "verzeichnis_fundstellen": vvt.VERZEICHNIS_FUNDSTELLEN,
            "status_text": __import__("app.services.dsfa.export", fromlist=["x"]).STATUS_TEXT,
            "votum_text": __import__("app.services.dsfa.export", fromlist=["x"]).VOTUM_TEXT,
        }
    )


async def run_workflow(
    database: Any, vvt: Any, dienst: Any, bw: Any, ausgabe: Any
) -> dict[str, Any]:
    """Execute the real service functions on a private in-memory SQLite database."""
    from app.models.mandant import Mandant
    from app.models.mandant_dsfa import MandantDsfa
    from app.models.mandant_dsgvo import MandantDsgvoDokument
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(
            database.Base.metadata.create_all,
            tables=[Mandant.__table__, MandantDsgvoDokument.__table__, MandantDsfa.__table__],
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    steps: list[dict[str, Any]] = []
    exports: dict[str, Any] = {}

    def dsfa_state(eintrag: Any) -> dict[str, Any]:
        return jsonable(
            {**dienst.als_json(eintrag), "taetigkeit_abbild": eintrag.taetigkeit_abbild}
        )

    def document_state(dokument: Any) -> dict[str, Any]:
        return jsonable(
            {
                "id": dokument.id,
                "mandant_id": dokument.mandant_id,
                "typ": dokument.typ,
                "version": dokument.version,
                "status": dokument.status,
                "ersteller": dokument.ersteller,
                "freigeber": dokument.freigeber,
                "erstellt_am": dokument.erstellt_am,
                "freigegeben_am": dokument.freigegeben_am,
                "vorgaenger_id": dokument.vorgaenger_id,
                "inhalt": dokument.inhalt,
            }
        )

    async with factory() as session:

        async def step(name: str, call: Any, render: Any = None) -> Any:
            try:
                result = await call()
                await session.commit()
                output = render(result) if render else jsonable(result)
                steps.append({"name": name, "output": output, "exception": None})
                return result
            except Exception as exc:  # noqa: BLE001 - characterization records every error
                await session.rollback()
                steps.append({"name": name, "output": None, "exception": error(exc)})
                return None

        mandant = Mandant(bezeichnung="Synthetische Testbehörde", dienststelle="Prüfstelle")
        fremd = Mandant(bezeichnung="Fremde Testbehörde")
        session.add_all([mandant, fremd])
        await session.commit()
        mid, fid = mandant.id, fremd.id
        steps.append(
            {"name": "tenants", "output": {"mandant": mid, "fremd": fid}, "exception": None}
        )

        taetigkeiten = [
            {
                "name": "Preisaufsicht",
                "referat": "Referat III – KPAnG-Vollzug",
                "zweck": "Vollzug des Kraftstoffpreisanpassungsgesetzes",
                "ermaechtigungsgrundlage": "KPAnG",
                "kategorien_betroffene": "Betreiber",
                "kategorien_daten": "Preisdaten",
                "besondere_kategorien": False,
                "anzahl_betroffene": 250,
                "drittlandtransfer": False,
                "ansprechperson": "Sachbearbeitung A",
            },
            {"name": "Preisaufsicht", "referat": "Referat Z", "zweck": "Zweitnennung"},
            {"name": "Benutzerverwaltung", "id": "fest-1", "referat": "", "zweck": "Konten"},
            {"name": "Formel", "referat": "Referat Z", "zweck": "=1+1", "avv_besteht": True},
        ]
        inhalt = {
            "deckblatt": {
                "verantwortlicher": {
                    "name": "Behörde",
                    "dienststelle": "Prüfstelle",
                    "plz": "1",
                    "ort": "O",
                },
                "dsb": {"anrede": "Frau", "name": "Beauftragte", "email": "dsb@example.invalid"},
            },
            "referate": ["Referat III – KPAnG-Vollzug", "Referat Z"],
            "taetigkeiten": taetigkeiten,
        }
        typ = "verarbeitungsverzeichnis"

        await step("vvt-no-draft", lambda: vvt.lade_entwurf(session, mid, typ), lambda r: r)
        await step(
            "dsfa-without-register",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id="egal",
                bearbeiter="anna",
                antworten={},
                szenarien=[],
            ),
            dsfa_state,
        )
        await step(
            "vvt-save-1",
            lambda: vvt.speichere_entwurf(session, mid, typ, "anna", inhalt),
            document_state,
        )
        await step(
            "vvt-save-1-again",
            lambda: vvt.speichere_entwurf(session, mid, typ, "anna", inhalt),
            document_state,
        )
        await step(
            "vvt-release-self", lambda: vvt.freigeben(session, mid, typ, "anna"), document_state
        )
        await step(
            "vvt-release-1", lambda: vvt.freigeben(session, mid, typ, "bert"), document_state
        )
        await step(
            "vvt-release-no-draft", lambda: vvt.freigeben(session, mid, typ, "bert"), document_state
        )
        await step(
            "activities-default", lambda: dienst.taetigkeiten(session, mid), lambda r: jsonable(r)
        )
        await step(
            "activities-all",
            lambda: dienst.taetigkeiten(session, mid, dienst.ALLE_REFERATE),
            lambda r: jsonable(r),
        )
        await step(
            "activities-referat-z",
            lambda: dienst.taetigkeiten(session, mid, "referat z"),
            lambda r: jsonable(r),
        )
        await step("departments", lambda: dienst.referate(session, mid), lambda r: jsonable(r))
        liste = await dienst.taetigkeiten(session, mid, dienst.ALLE_REFERATE)
        aid = liste[0]["id"]
        bid = liste[1]["id"]
        cid = liste[2]["id"]

        antworten = {
            "art35_3_a": {"ja": True, "begruendung": "Automatisierte Bewertung."},
            "edsa_01_bewerten": {"ja": True, "begruendung": "Einstufung."},
        }
        szenarien = [
            {
                "dimension": "vertraulichkeit",
                "beschreibung": "Unbefugter Zugriff",
                "schwere": 3,
                "wahrscheinlichkeit": 4,
                "massnahmen": ["zugriffskontrolle"],
            }
        ]
        await step(
            "dsfa-unknown-activity",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id="unbekannt",
                bearbeiter="anna",
                antworten={},
                szenarien=[],
            ),
            dsfa_state,
        )
        await step(
            "dsfa-unknown-regime",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id=aid,
                bearbeiter="anna",
                antworten=antworten,
                szenarien=szenarien,
                rechtsregime="falsch",
            ),
            dsfa_state,
        )
        await step(
            "dsfa-invalid-scenario",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id=aid,
                bearbeiter="anna",
                antworten=antworten,
                szenarien=[{"dimension": "x", "schwere": 9, "wahrscheinlichkeit": 1}],
            ),
            dsfa_state,
        )
        eintrag = await step(
            "dsfa-save-1",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id=aid,
                bearbeiter="anna",
                antworten=antworten,
                szenarien=szenarien,
            ),
            dsfa_state,
        )
        did = eintrag.id
        await step(
            "dsfa-release-before-decision",
            lambda: dienst.freigeben(session, dsfa_id=did, freigeber="bert"),
            dsfa_state,
        )
        await step(
            "dsfa-decide-deviation-short",
            lambda: dienst.entscheide(
                session,
                dsfa_id=did,
                bearbeiter="anna",
                entscheidung=bw.VORSCHLAG_FREIGABE,
                begruendung="zu kurz",
            ),
            dsfa_state,
        )
        await step(
            "dsfa-decide-deviation-justified",
            lambda: dienst.entscheide(
                session,
                dsfa_id=did,
                bearbeiter="anna",
                entscheidung=bw.VORSCHLAG_FREIGABE,
                begruendung="x" * 50,
            ),
            dsfa_state,
        )
        await step(
            "dsfa-decide-unknown-value",
            lambda: dienst.entscheide(
                session,
                dsfa_id=did,
                bearbeiter="anna",
                entscheidung="irgendwas",
                begruendung="y" * 50,
            ),
            dsfa_state,
        )
        await step(
            "dsfa-decide-accept",
            lambda: dienst.entscheide(
                session,
                dsfa_id=did,
                bearbeiter="anna",
                entscheidung=bw.VORSCHLAG_FREIGABE_MIT_AUFLAGEN,
            ),
            dsfa_state,
        )
        await step(
            "dsfa-release-before-dsb",
            lambda: dienst.freigeben(session, dsfa_id=did, freigeber="bert"),
            dsfa_state,
        )
        await step(
            "dsfa-conclusion-before-statement",
            lambda: dienst.dsb_folgerung(session, dsfa_id=did, folgerung="Folgerung"),
            dsfa_state,
        )
        await step(
            "dsfa-statement-unknown-vote",
            lambda: dienst.dsb_stellungnahme(
                session, dsfa_id=did, votum="ja", stellungnahme="Text"
            ),
            dsfa_state,
        )
        await step(
            "dsfa-statement-empty",
            lambda: dienst.dsb_stellungnahme(
                session, dsfa_id=did, votum="abgelehnt", stellungnahme="  "
            ),
            dsfa_state,
        )
        await step(
            "dsfa-statement-rejected",
            lambda: dienst.dsb_stellungnahme(
                session,
                dsfa_id=did,
                votum="abgelehnt",
                stellungnahme="Das Risiko ist nicht ausreichend gemindert.",
            ),
            dsfa_state,
        )
        await step(
            "dsfa-release-missing-necessity",
            lambda: dienst.freigeben(session, dsfa_id=did, freigeber="bert"),
            dsfa_state,
        )
        await step(
            "dsfa-save-content-after-statement",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id=aid,
                bearbeiter="anna",
                antworten={**antworten, "edsa_05_umfang": {"ja": True}},
                szenarien=szenarien,
                notwendigkeit="Ohne die Bewertung ist der Vollzug nicht durchführbar.",
                verhaeltnismaessigkeit="Mildere Mittel wurden geprüft und sind ungeeignet.",
                standpunkt_betroffene="Nicht eingeholt; Betroffene sind nicht bestimmbar.",
            ),
            dsfa_state,
        )
        await step(
            "dsfa-release-rejected-without-conclusion",
            lambda: dienst.freigeben(session, dsfa_id=did, freigeber="bert"),
            dsfa_state,
        )
        await step(
            "dsfa-conclusion-short",
            lambda: dienst.dsb_folgerung(session, dsfa_id=did, folgerung="zu kurz"),
            dsfa_state,
        )
        await step(
            "dsfa-conclusion-long",
            lambda: dienst.dsb_folgerung(session, dsfa_id=did, folgerung="f" * 50),
            dsfa_state,
        )
        await step(
            "dsfa-release-without-leadership",
            lambda: dienst.freigeben(session, dsfa_id=did, freigeber="bert"),
            dsfa_state,
        )
        await step(
            "dsfa-conclusion-leadership",
            lambda: dienst.dsb_folgerung(
                session, dsfa_id=did, folgerung="f" * 50, leitung_vorgelegt_an="Behördenleitung"
            ),
            dsfa_state,
        )
        await step(
            "dsfa-release-self",
            lambda: dienst.freigeben(session, dsfa_id=did, freigeber="anna"),
            dsfa_state,
        )
        released = await step(
            "dsfa-release",
            lambda: dienst.freigeben(session, dsfa_id=did, freigeber="bert"),
            dsfa_state,
        )
        await step(
            "dsfa-decide-locked",
            lambda: dienst.entscheide(
                session,
                dsfa_id=did,
                bearbeiter="anna",
                entscheidung=bw.VORSCHLAG_FREIGABE_MIT_AUFLAGEN,
            ),
            dsfa_state,
        )
        await step(
            "dsfa-statement-locked",
            lambda: dienst.dsb_stellungnahme(
                session, dsfa_id=did, votum="zugestimmt", stellungnahme="x"
            ),
            dsfa_state,
        )
        await step(
            "changes-unchanged",
            lambda: dienst.pruefe_auf_aenderungen(session, mid),
            lambda r: jsonable(r),
        )
        await step(
            "dsfa-foreign-tenant-load",
            lambda: dienst.lade(session, did),
            lambda r: {"mandant_id": r.mandant_id, "requested_by_tenant": fid},
        )

        await session.refresh(released)
        exports["report_html"] = ausgabe.baue_bericht_html(released, "Synthetische Testbehörde")
        exports["report_record"] = dsfa_state(released)
        try:
            pdf = ausgabe.baue_bericht_pdf(released, "Synthetische Testbehörde")
            exports["report_pdf"] = {
                "status": "OBSERVED",
                "magic": pdf[:5].decode("latin1"),
                "bytes": len(pdf),
            }
        except Exception as exc:  # noqa: BLE001
            exports["report_pdf"] = {"status": "NOT_EXECUTED", **error(exc)}

        # Minimal-path activity: no criterion, empty answers, released without content.
        leer = await step(
            "dsfa-empty-answers-save",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id=cid,
                bearbeiter="anna",
                antworten={},
                szenarien=[],
            ),
            dsfa_state,
        )
        eid = leer.id
        await step(
            "dsfa-empty-decide",
            lambda: dienst.entscheide(
                session, dsfa_id=eid, bearbeiter="anna", entscheidung=bw.VORSCHLAG_NUR_SCHWELLWERT
            ),
            dsfa_state,
        )
        await step(
            "dsfa-empty-statement",
            lambda: dienst.dsb_stellungnahme(
                session, dsfa_id=eid, votum="zugestimmt", stellungnahme="Keine Einwände."
            ),
            dsfa_state,
        )
        await step(
            "dsfa-empty-release",
            lambda: dienst.freigeben(session, dsfa_id=eid, freigeber="bert"),
            dsfa_state,
        )

        # Pflicht without scenarios: suggestion is consultation; conditional agreement path.
        ohne = await step(
            "dsfa-required-no-scenarios",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id=bid,
                bearbeiter="carl",
                antworten={"art35_3_c": {"ja": True}},
                szenarien=[],
            ),
            dsfa_state,
        )
        oid = ohne.id
        await step(
            "dsfa-conditional-decide",
            lambda: dienst.entscheide(
                session, dsfa_id=oid, bearbeiter="carl", entscheidung=bw.VORSCHLAG_KONSULTATION
            ),
            dsfa_state,
        )
        await step(
            "dsfa-conditional-statement",
            lambda: dienst.dsb_stellungnahme(
                session, dsfa_id=oid, votum="zugestimmt_mit_auflagen", stellungnahme="Auflage."
            ),
            dsfa_state,
        )
        await step(
            "dsfa-conditional-necessity",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id=bid,
                bearbeiter="carl",
                antworten={"art35_3_c": {"ja": True}},
                szenarien=[],
                notwendigkeit="N",
                verhaeltnismaessigkeit="V",
            ),
            dsfa_state,
        )
        await step(
            "dsfa-conditional-release-no-scenario",
            lambda: dienst.freigeben(session, dsfa_id=oid, freigeber="bert"),
            dsfa_state,
        )
        await step(
            "dsfa-conditional-scenario",
            lambda: dienst.speichere(
                session,
                mandant_id=mid,
                taetigkeit_id=bid,
                bearbeiter="carl",
                antworten={"art35_3_c": {"ja": True}},
                szenarien=[
                    {
                        "dimension": "transparenz",
                        "beschreibung": "B",
                        "schwere": 4,
                        "wahrscheinlichkeit": 4,
                    }
                ],
            ),
            dsfa_state,
        )
        await step(
            "dsfa-conditional-release-no-conclusion",
            lambda: dienst.freigeben(session, dsfa_id=oid, freigeber="bert"),
            dsfa_state,
        )
        await step(
            "dsfa-conditional-conclusion",
            lambda: dienst.dsb_folgerung(session, dsfa_id=oid, folgerung="Auflage umgesetzt."),
            dsfa_state,
        )
        await step(
            "dsfa-conditional-release",
            lambda: dienst.freigeben(session, dsfa_id=oid, freigeber="bert"),
            dsfa_state,
        )

        # Register change and reassessment.
        geaendert = copy.deepcopy(inhalt)
        geaendert["taetigkeiten"] = vvt.taetigkeiten_mit_kennung(geaendert["taetigkeiten"])
        geaendert["taetigkeiten"][0]["zweck"] = "Erweiterter Zweck"
        geaendert["taetigkeiten"][0]["ansprechperson"] = "Sachbearbeitung B"
        geaendert["taetigkeiten"][0]["anzahl_betroffene"] = 20000
        del geaendert["taetigkeiten"][2]
        await step(
            "vvt-save-2",
            lambda: vvt.speichere_entwurf(session, mid, typ, "anna", geaendert),
            document_state,
        )
        await step(
            "changes-draft-over-release",
            lambda: dienst.pruefe_auf_aenderungen(session, mid),
            lambda r: jsonable(r),
        )
        await step(
            "vvt-save-2-other-editor",
            lambda: vvt.speichere_entwurf(session, mid, typ, "carl", geaendert),
            document_state,
        )
        await step(
            "vvt-release-2", lambda: vvt.freigeben(session, mid, typ, "bert"), document_state
        )
        await step(
            "vvt-history",
            lambda: vvt.lade_versionen(session, mid, typ),
            lambda r: [document_state(d) for d in r],
        )
        await step(
            "changes-after-release",
            lambda: dienst.pruefe_auf_aenderungen(session, mid),
            lambda r: jsonable(r),
        )
        neu = await step(
            "reassessment",
            lambda: dienst.neubewertung(session, dsfa_id=did, bearbeiter="anna"),
            dsfa_state,
        )
        await step(
            "reassessment-again",
            lambda: dienst.neubewertung(session, dsfa_id=did, bearbeiter="anna"),
            dsfa_state,
        )
        await step(
            "reassessment-removed-activity",
            lambda: dienst.neubewertung(session, dsfa_id=eid, bearbeiter="anna"),
            dsfa_state,
        )
        await step(
            "versions-activity-a",
            lambda: dienst.fassungen(session, mid, aid),
            lambda r: [dsfa_state(e) for e in r],
        )
        await step(
            "open-version-a",
            lambda: dienst.offene_fassung(session, mid, aid),
            lambda r: dsfa_state(r) if r else None,
        )
        await step(
            "activities-final",
            lambda: dienst.taetigkeiten(session, mid, dienst.ALLE_REFERATE),
            lambda r: jsonable(r),
        )
        await step(
            "foreign-tenant-activities",
            lambda: dienst.taetigkeiten(session, fid),
            lambda r: jsonable(r),
        )

        # Exports of the final state.
        final = await dienst.taetigkeiten(session, mid, dienst.ALLE_REFERATE)
        exports["overview_workbook"] = workbook_cells(
            ausgabe.baue_uebersicht_workbook(final, "Synthetische Testbehörde")
        )
        dokument = await vvt.lade_aktuelle_freigegebene(session, mid, typ)
        await session.refresh(mandant)
        exports["register_workbook"] = workbook_cells(
            vvt.baue_verarbeitungsverzeichnis_workbook(dokument, mandant)
        )
        exports["register_workbook_document"] = document_state(dokument)
        exports["overview_rows"] = jsonable(final)
        leer_dokument = MandantDsgvoDokument(
            mandant_id=mid,
            typ=typ,
            inhalt={},
            version=9,
            status="entwurf",
            ersteller="anna",
            erstellt_am=datetime(2026, 9, 2, tzinfo=UTC),
        )
        exports["register_workbook_empty"] = workbook_cells(
            vvt.baue_verarbeitungsverzeichnis_workbook(leer_dokument, mandant)
        )
        buffer = io.BytesIO()
        vvt.baue_verarbeitungsverzeichnis_workbook(dokument, mandant).save(buffer)
        exports["register_workbook_bytes"] = len(buffer.getvalue())
        if neu is not None:
            await session.refresh(neu)
            exports["reassessment_report_html"] = ausgabe.baue_bericht_html(neu, "")
            exports["reassessment_record"] = dsfa_state(neu)
    await engine.dispose()
    return {"steps": steps, "exports": exports}


if __name__ == "__main__":
    main()
