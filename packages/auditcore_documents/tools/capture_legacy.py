"""Führt den Original-Dokumentvergleich aus audit_designer tatsächlich aus.

Aufruf (Referenzumgebung wie die Produktion: Python 3.11, lxml 5.1.0,
python-docx 1.1.0, pypdf 6.16.2, rapidfuzz 3.14.5, pdftotext 22.12.0)::

    python tools/capture_legacy.py --source <audit_designer-Checkout@030a71e0> \
        --output tests/fixtures/legacy_observed.json

Das Werkzeug prüft zuerst die Git-Blobs der Quelldateien, importiert dann die
unveränderten Module ``app.modules.document_compare.*`` und zeichnet Eingaben
und Ausgaben auf. Anwendungsgrenzen (FlowAgent/MCP, Celery, Datenbank,
Research-PDF) werden durch aufzeichnende Stellvertreter ersetzt; die
Fachlogik läuft unverändert. Zeitstempel (``created_at``) und Datei-mtimes
hängen vom Lauf ab und werden nur als vorhanden vermerkt.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import enum
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import types
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
REPOSITORY = "janpow77/audit_designer"
COMMIT = "030a71e083ef0feddc14545b095a4945bc0bbd7a"
_DC = "backend/app/modules/document_compare/"
BLOBS = {
    _DC + "__init__.py": None,
    _DC + "types.py": "295ed31cd6b0bf73af2fe9aa844d9f819c68b7a8",
    _DC + "parsing.py": "bb0904344c0bf77b8587e23f3f8debf43423c810",
    _DC + "matching.py": "1344667a7b85b809fd9a0477fa7c448b988b3ad1",
    _DC + "article_law.py": "9156134ae74a79d65f4c7d161a54fc855b62c240",
    _DC + "service.py": "265948ea3ac493c3f754d7ef88c7de4667ee9976",
    _DC + "rendering.py": "e706e91e526f48c40bc9f8490700bddb60b7a57a",
    _DC + "configuration.py": "3c324de7073d2cfbfff370c0624d07c27cd2bca2",
    _DC + "cli.py": "ead8b5402f28b6a364841c8396edc12f787df0b1",
    _DC + "tasks.py": "5f7d1b1c54fb30b2366c2d09dc80d8e1fcbeb69e",
    "backend/app/modules/ecohesion/services/research_pdf.py": (
        "3ca2a3fca8975f8ba7523d84c01e251acbdd7e80"
    ),
    "backend/app/core/shared/research/contracts.py": ("1eef9877cd06bc8f5afd32d5077707df9e7abea4"),
    "backend/app/modules/ecohesion/comparisons/worker.py": (
        "f8300bea36d09ef7964fff4a1e5d8e4a9e04c2a6"
    ),
}
VOLATILE_METADATA = ("old_modified_at", "new_modified_at")


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # noqa: S324 - Git-Objektkennung


def fixture(name: str) -> Path:
    path = FIXTURES / name
    if not path.exists() and not name.startswith("fehlt/"):
        raise FileNotFoundError(name)
    return path


def sha(name: str) -> str | None:
    path = FIXTURES / name
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def error(exc: BaseException) -> dict[str, str]:
    return {"error": type(exc).__name__, "message": str(exc)}


def result_dict(result: Any) -> dict[str, Any]:
    data = result.to_dict()
    data.pop("created_at")
    metadata = data["metadata"]
    data["volatile_metadata"] = sorted(k for k in VOLATILE_METADATA if k in metadata)
    for key in VOLATILE_METADATA:
        metadata.pop(key, None)
    return data


@contextlib.contextmanager
def scorer(variant: str):
    """``rapidfuzz`` = Produktionsumgebung; ``difflib`` = Rückfall ohne rapidfuzz."""
    if variant == "rapidfuzz":
        yield
        return
    saved = {k: v for k, v in sys.modules.items() if k == "rapidfuzz" or k.startswith("rapidfuzz.")}
    for key in saved:
        del sys.modules[key]
    sys.modules["rapidfuzz"] = None  # type: ignore[assignment]  # ImportError erzwingen
    try:
        yield
    finally:
        del sys.modules["rapidfuzz"]
        sys.modules.update(saved)


@contextlib.contextmanager
def without_pdftotext():
    previous = os.environ.get("PATH", "")
    os.environ["PATH"] = "/nonexistent"
    try:
        yield
    finally:
        os.environ["PATH"] = previous


OCR_TEXT = (
    "§ 1 Musterregel\n"
    "Diese Seite wurde durch eine OCR-Stelle gelesen und enthält genügend Text.\n"
    "Ein zweiter Satz folgt hier.\n"
)


def ocr_callback(kind: str):
    if kind == "none":
        return None
    if kind == "short":
        return lambda _path: "zu kurz"
    return lambda _path: OCR_TEXT


# --------------------------------------------------------------------------- Fälle

NORMALISE_TEXTS = [
    "",
    "   ",
    "1. Erste Frage",
    "1.2.3) Tiefe Nummer",
    "a) Buchstabe",
    "B) Großbuchstabe",
    "– Gedankenstrich",
    "- Bindestrich-Aufzählung",
    "12 Zwölf ohne Punkt",
    "2024 ist ein Jahr",
    "§ 5 Absatz 1, Satz 2!",
    "Mehrfache   Leer-\nzeichen\tund Tabs",
    "ÄÖÜ äöü ß ẞ",
    "Straße STRASSE",
    "Text mit „Anführungszeichen“ und (Klammern).",
    "Art. 74 Abs. 2 lit. a VO (EU) 2021/1060",
    "e) f) g) doppelte Buchstaben",
    "10.5 % Quote",
    "ﬁ Ligatur",
]

WORD_DIFF_PAIRS = [
    ("", ""),
    ("gleich", "gleich"),
    ("a b c", "a x c"),
    ("", "neu hinzu"),
    ("weg", ""),
    ("Die Prüfbehörde prüft.", "Die Prüfbehörde prüft sorgfältig."),
    ("a  b", "a b"),
]

READ_CASES: list[tuple[str, str, str]] = [
    *(
        (f"synthetic/{name}", mode, "none")
        for name in (
            "cl_basis_alt.docx",
            "cl_basis_neu.docx",
            "cl_rich_alt.docx",
            "cl_rich_neu.docx",
            "cl_tracked_alt.docx",
            "cl_tracked_neu.docx",
            "cl_symbole_alt.docx",
            "cl_symbole_neu.docx",
            "cl_leer.docx",
            "mix_tabelle.docx",
            "tx_struktur_alt.docx",
            "tx_struktur_neu.docx",
            "tx_leer.docx",
            "al_befehle.docx",
        )
        for mode in ("auto", "checklist", "text")
    ),
    ("synthetic/cl_rich_alt.docx", "unbekannt", "none"),
    ("public/KassenSichV_2025-06-01.docx", "auto", "none"),
    ("public/KassenSichV_2026-05-06.docx", "auto", "none"),
    ("public/BGBl-2025-I-301-Art15.docx", "auto", "none"),
    ("public/KassenSichV_2023-06-10.pdf", "auto", "none"),
    ("public/KassenSichV_2026-08-27.pdf", "checklist", "none"),
    ("public/bgbl-2025-I-301-seite55.pdf", "auto", "none"),
    ("errors/kaputt.docx", "auto", "none"),
    ("errors/kaputt.docx", "text", "none"),
    ("errors/ohne_document.docx", "auto", "none"),
    ("errors/xml_fehler.docx", "text", "none"),
    ("errors/notiz.txt", "auto", "none"),
    ("errors/kaputt.pdf", "auto", "none"),
    ("errors/leer.pdf", "auto", "none"),
    ("errors/leer.pdf", "auto", "short"),
    ("errors/leer.pdf", "auto", "text"),
    ("errors/entitaet_intern.docx", "text", "none"),
    ("fehlt/nicht_da.docx", "auto", "none"),
    ("fehlt/nicht_da.pdf", "auto", "none"),
]

PDF_FILES = [
    "public/KassenSichV_2023-06-10.pdf",
    "public/KassenSichV_2026-08-27.pdf",
    "public/bgbl-2025-I-301-seite55.pdf",
]

PAGE_CASES: list[list[str]] = [
    [],
    [""],
    ["Kopf\nText eins.\nSeite 1 von 2", "Kopf\nText zwei.\nSeite 2 von 2"],
    ["A\nB\nC\nInhalt eins.\nX\nY\nZ", "A\nB\nC\nInhalt zwei.\nX\nY\nZ", "A\nInhalt drei.\nZ"],
    ["§ 1 Überschrift\nEin Absatz, der über\nzwei Zeilen geht.\nNoch ein Satz ohne Ende"],
    ["Trenn-\nung im Wort und Ab-\n satz.", "Artikel 3 Kurz\n„Zitat“"],
    ["Seite 3\n12\nText mit Zahl 12 am Ende:\nweiter"],
]

STANDARD_CASES: list[dict[str, Any]] = [
    {
        "old": "synthetic/cl_basis_alt.docx",
        "new": "synthetic/cl_basis_neu.docx",
        "kwargs": {"mode": "checklist", "threshold": 70},
    },
    {
        "old": "synthetic/cl_basis_alt.docx",
        "new": "synthetic/cl_basis_neu.docx",
        "kwargs": {"mode": "checklist"},
    },
    {
        "old": "synthetic/cl_basis_alt.docx",
        "new": "synthetic/cl_basis_neu.docx",
        "kwargs": {"mode": "auto", "threshold": 100},
    },
    {
        "old": "synthetic/cl_100_alt.docx",
        "new": "synthetic/cl_100_neu.docx",
        "kwargs": {"mode": "checklist", "threshold": 70},
    },
    {
        "old": "synthetic/cl_publizitaet_alt.docx",
        "new": "synthetic/cl_publizitaet_neu.docx",
        "kwargs": {"mode": "checklist", "threshold": 70},
    },
    {"old": "synthetic/cl_rich_alt.docx", "new": "synthetic/cl_rich_neu.docx", "kwargs": {}},
    {
        "old": "synthetic/cl_rich_alt.docx",
        "new": "synthetic/cl_rich_neu.docx",
        "kwargs": {"include_answers": False, "include_notes": False},
    },
    {
        "old": "synthetic/cl_rich_alt.docx",
        "new": "synthetic/cl_rich_neu.docx",
        "kwargs": {"include_editorial": True, "output_sections": ["changed", "unchanged"]},
    },
    {
        "old": "synthetic/cl_tracked_alt.docx",
        "new": "synthetic/cl_tracked_neu.docx",
        "kwargs": {"mode": "checklist", "threshold": 70},
    },
    {
        "old": "synthetic/cl_symbole_alt.docx",
        "new": "synthetic/cl_symbole_neu.docx",
        "kwargs": {"mode": "checklist"},
    },
    {
        "old": "synthetic/tx_verschoben_alt.docx",
        "new": "synthetic/tx_verschoben_neu.docx",
        "kwargs": {"mode": "text"},
    },
    {
        "old": "synthetic/tx_streichung_alt.docx",
        "new": "synthetic/tx_streichung_neu.docx",
        "kwargs": {"mode": "text"},
    },
    {
        "old": "synthetic/tx_struktur_alt.docx",
        "new": "synthetic/tx_struktur_neu.docx",
        "kwargs": {},
    },
    {
        "old": "synthetic/tx_struktur_alt.docx",
        "new": "synthetic/tx_struktur_neu.docx",
        "kwargs": {"include_editorial": True},
    },
    {
        "old": "synthetic/tx_struktur_alt.docx",
        "new": "synthetic/tx_struktur_neu.docx",
        "kwargs": {"threshold": 95, "highlight_words": False},
    },
    {
        "old": "synthetic/tx_block_alt.docx",
        "new": "synthetic/tx_block_neu.docx",
        "kwargs": {"mode": "text"},
    },
    {
        "old": "synthetic/tx_block_alt.docx",
        "new": "synthetic/tx_block_neu.docx",
        "kwargs": {"mode": "text", "threshold": 100},
    },
    {
        "old": "synthetic/tx_block_alt.docx",
        "new": "synthetic/tx_block_neu.docx",
        "kwargs": {"mode": "text", "threshold": 70},
    },
    {
        "old": "public/KassenSichV_2025-06-01.docx",
        "new": "public/KassenSichV_2026-05-06.docx",
        "kwargs": {},
    },
    {
        "old": "public/KassenSichV_2025-06-01.docx",
        "new": "public/KassenSichV_2026-05-06.docx",
        "kwargs": {"include_editorial": True, "threshold": 90},
    },
    {
        "old": "public/KassenSichV_2023-06-10.pdf",
        "new": "public/KassenSichV_2026-08-27.pdf",
        "kwargs": {},
    },
    {
        "old": "public/KassenSichV_2023-06-10.pdf",
        "new": "public/KassenSichV_2026-08-27.pdf",
        "kwargs": {"threshold": 75},
    },
    {
        "old": "public/KassenSichV_2025-06-01.docx",
        "new": "public/KassenSichV_2026-08-27.pdf",
        "kwargs": {},
    },
    {
        "old": "public/KassenSichV_2025-06-01.docx",
        "new": "public/KassenSichV_2025-06-01.docx",
        "kwargs": {},
    },
    {"old": "synthetic/mix_tabelle.docx", "new": "synthetic/cl_basis_neu.docx", "kwargs": {}},
    {"old": "synthetic/tx_struktur_alt.docx", "new": "synthetic/cl_basis_neu.docx", "kwargs": {}},
    {
        "old": "synthetic/tx_leer.docx",
        "new": "synthetic/tx_struktur_neu.docx",
        "kwargs": {"mode": "text"},
    },
    {
        "old": "synthetic/cl_basis_alt.docx",
        "new": "synthetic/cl_basis_neu.docx",
        "kwargs": {"threshold": 69},
    },
    {
        "old": "synthetic/cl_basis_alt.docx",
        "new": "synthetic/cl_basis_neu.docx",
        "kwargs": {"threshold": 101},
    },
    {
        "old": "synthetic/cl_basis_alt.docx",
        "new": "synthetic/cl_basis_neu.docx",
        "kwargs": {"comparison_type": "xyz"},
    },
    {"old": "errors/leer.pdf", "new": "errors/leer.pdf", "kwargs": {}, "ocr": "text"},
]

ARTICLE_CASES: list[dict[str, Any]] = [
    {"old": "synthetic/al_stamm.docx", "new": "synthetic/al_befehle.docx"},
    {"old": "public/KassenSichV_2025-06-01.docx", "new": "public/BGBl-2025-I-301-Art15.docx"},
    {"old": "public/KassenSichV_2025-06-01.docx", "new": "public/bgbl-2025-I-301-seite55.pdf"},
    {"old": "public/KassenSichV_2023-06-10.pdf", "new": "public/bgbl-2025-I-301-seite55.pdf"},
    {"old": "synthetic/al_stamm.docx", "new": "synthetic/al_befehle_letzter_ohne_text.docx"},
    {"old": "synthetic/al_stamm_ohne_paragrafen.docx", "new": "synthetic/al_befehle.docx"},
    {"old": "synthetic/al_stamm.docx", "new": "errors/kaputt.docx"},
]

SIMILARITY_PAIRS = [
    ("Frage wird geändert", "Frage wird deutlich geändert"),
    ("Frage entfällt", "Neue Frage"),
    ("1. Gleich", "2. gleich"),
    ("", ""),
    ("", "Text"),
    ("Die Prüfbehörde prüft das Vorhaben.", "Das Vorhaben prüft die Prüfbehörde."),
    ("a b c d", "d c b a e"),
]

SETTINGS_INPUTS: list[Any] = [
    None,
    [],
    "text",
    {},
    {"unbekannt": 1, "threshold": 90},
    {"threshold": 10},
    {"threshold": 1000},
    {"threshold": "85"},
    {"threshold": "abc"},
    {"threshold": 85.9},
    {"retention_days": 0},
    {"retention_days": "99999"},
    {"output_profile": "pdf"},
    {"output_profile": "text"},
    {"mode": "tabelle"},
    {"mode": "checklist"},
    {"comparison_type": "article_law"},
    {"comparison_type": "anders"},
    {
        "generate_reasons": "ja",
        "include_answers": 0,
        "include_notes": [],
        "include_editorial": 1,
        "highlight_words": None,
    },
    {"output_sections": "changed"},
    {"output_sections": ["moved", "moved", "unchanged", "falsch", 1]},
    {"output_sections": ["falsch"]},
    {"model": "  qwen\x00-3  " + "x" * 200},
    {"memo_layout": "kein dict"},
    {"memo_layout": {}},
    {
        "memo_layout": {
            "header_text": "",
            "font_family": "",
            "body_font_size_pt": "groß",
            "heading_font_size_pt": 3,
            "line_spacing": 9,
            "page_margin_cm": "2,5",
            "accent_color": "005ea8",
            "footer_text": None,
            "show_page_numbers": 0,
            "show_file_metadata": "nein",
            "outline": "Anlass\nBewertung",
        }
    },
    {"memo_layout": {"accent_color": "#zzzzzz", "outline": []}},
    {"memo_layout": {"accent_color": "#abcdef1", "outline": ["A {{vergleich}}", "", "B"]}},
    {"memo_layout": {"outline": 5}},
    {"memo_layout": {"outline": [f"Punkt {i}" for i in range(25)]}},
    {"text_layout": {"header_text": "", "outline": ["ignoriert"], "accent_color": "123ABC"}},
]

MERGE_CASES: list[tuple[Any, Any, Any]] = [
    ({}, {}, {}),
    (
        {"memo_layout": {"font_family": "Hessen Gellix"}},
        {
            "output_profile": "memo",
            "memo_layout": {
                "header_text": "Mein\nBriefkopf",
                "font_family": "Arial",
                "body_font_size_pt": 99,
                "accent_color": "005EA8",
                "outline": ["Anlass", "Bewertung"],
            },
        },
        {},
    ),
    ({"threshold": 90}, {"threshold": 80}, {"threshold": 75, "mode": "text"}),
    (None, "kaputt", {"output_sections": ["added"]}),
    (
        {"memo_layout": {"font_family": "A"}},
        {"memo_layout": "x"},
        {"memo_layout": {"footer_text": "F"}},
    ),
]

REASON_PAYLOADS: list[tuple[str, str, str | None, Any]] = [
    (
        "Frist 3 Monate nach § 5 Abs. 1.",
        "Frist 6 Monate nach § 5 Abs. 1.",
        None,
        {
            "begruendung": "Die Frist wurde nach § 5 Abs. 1 verlängert.",
            "rechtsgrundlage": "",
            "provider": "flowagent",
            "prompt_version": "v1",
            "temperature": 0.0,
            "seed": 7,
            "quantization": "q8",
            "extra": "ignoriert",
        },
    ),
    (
        "Art. 74 VO (EU) 2021/1060",
        "Art. 74 Abs. 2 VO (EU) 2021/1060",
        "qwen",
        {"begruendung": "Präzisierung.", "rechtsgrundlage": "Art. 74 Abs. 2, Art. 77, § 44 BHO"},
    ),
    ("alt", "neu", None, {"begruendung": "  ", "rechtsgrundlage": "Artikel 9a"}),
    ("alt", "neu", None, {}),
    ("alt", "neu", None, "kein json"),
    ("alt", "neu", None, {"begruendung": 5, "rechtsgrundlage": None}),
]

VERIFY_CASES = [
    ("", "", "", ""),
    ("Nach § 5 Abs. 1", "", "§ 5 Absatz 1 gilt", ""),
    ("Nach § 5 Abs. 1", "", "", "§5 Abs.1"),
    ("§§ 3 und Art. 12a", "VO (EU) 2021/1060", "Art 12a der (EU)2021/1060", "§§ 3"),
    ("Artikel 7 und Art.8", "", "Art. 7", ""),
]


# --------------------------------------------------------------------------- Stellvertreter


class ScriptedMcp:
    """Ersetzt app.modules.standards.mcp_tools; zeichnet Aufrufe auf."""

    def __init__(self) -> None:
        self.responses: list[Any] = []
        self.calls: list[dict[str, Any]] = []

    def ausfuehren(self, name: str, arguments: dict[str, Any]) -> str:
        self.calls.append({"name": name, "arguments": copy.deepcopy(arguments)})
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)


def install_mcp_stub() -> ScriptedMcp:
    stub = ScriptedMcp()
    module = types.ModuleType("app.modules.standards.mcp_tools")
    module.ausfuehren = stub.ausfuehren  # type: ignore[attr-defined]
    package = types.ModuleType("app.modules.standards")
    package.mcp_tools = module  # type: ignore[attr-defined]
    sys.modules["app.modules.standards"] = package
    sys.modules["app.modules.standards.mcp_tools"] = module
    return stub


class FakeComparison:
    def __init__(self, options: dict[str, Any], old: Path, new: Path) -> None:
        self.options_json = options
        self.old_path = str(old)
        self.new_path = str(new)
        self.status: Any = None
        self.progress = 0
        self.result_json: Any = None
        self.error_message: Any = None
        self.finished_at: Any = None


class FakeDb:
    def __init__(self, store: dict[str, FakeComparison]) -> None:
        self.store = store

    def get(self, _model: Any, key: str) -> FakeComparison | None:
        return self.store.get(key)


def install_task_stubs(store: dict[str, FakeComparison]) -> None:
    class Status(enum.StrEnum):
        QUEUED = "queued"
        RUNNING = "running"
        PREVIEW = "preview"
        FAILED = "failed"
        DELETED = "deleted"

    celery = types.ModuleType("app.celery_app")

    class _Celery:
        def task(self, *args: Any, **kwargs: Any):
            def decorate(function: Any) -> Any:
                return function

            return decorate

    celery.celery_app = _Celery()  # type: ignore[attr-defined]
    database = types.ModuleType("app.core.database")

    @contextlib.contextmanager
    def get_db_session():
        yield FakeDb(store)

    database.get_db_session = get_db_session  # type: ignore[attr-defined]
    models = types.ModuleType("app.models.document_comparison")
    models.DocumentComparison = object  # type: ignore[attr-defined]
    models.DocumentComparisonStatus = Status  # type: ignore[attr-defined]
    router = types.ModuleType("app.utils.ai_router_client")
    router.call_ocr = lambda *_a, **_k: types.SimpleNamespace(text=OCR_TEXT)  # type: ignore[attr-defined]
    for name, module in {
        "app.celery_app": celery,
        "app.core.database": database,
        "app.models.document_comparison": models,
        "app.utils.ai_router_client": router,
    }.items():
        sys.modules[name] = module


class FakeTask:
    def __init__(self) -> None:
        self.states: list[dict[str, Any]] = []

    def update_state(self, **kwargs: Any) -> None:
        self.states.append(kwargs)


# --------------------------------------------------------------------------- Rendering


def docx_parts(path: Path) -> dict[str, str]:
    """Inhaltsteile vollständig, die große Formatvorlage nur als SHA-256."""
    with zipfile.ZipFile(path) as archive:
        parts = {
            name: archive.read(name).decode("utf-8")
            for name in sorted(archive.namelist())
            if name in {"word/document.xml", "word/header1.xml", "word/footer1.xml"}
        }
        parts["word/styles.xml#sha256"] = hashlib.sha256(
            archive.read("word/styles.xml")
        ).hexdigest()
    return parts


FIXED_METADATA = {"old_modified_at": 1735732800.0, "new_modified_at": 1767268800.5}
FIXED_CREATED = "2026-09-23T08:15:00+00:00"

RENDER_CASES: list[dict[str, Any]] = [
    {
        "compare": 0,
        "render": {"user": "Test"},
        "labels": {"old_label": "Stand 2025", "new_label": "Stand 2026"},
    },
    {
        "compare": 5,
        "render": {
            "user": "Erika Muster",
            "profile": "memo",
            "layout": {
                "header_text": "Dienststelle\nVermerk",
                "font_family": "Arial",
                "body_font_size_pt": 11,
                "heading_font_size_pt": 16,
                "line_spacing": 1.2,
                "page_margin_cm": 2.5,
                "accent_color": "#005EA8",
                "footer_text": "Nur für den Dienstgebrauch",
                "show_page_numbers": False,
                "show_file_metadata": False,
                "outline": ["Anlass", "Feststellungen {{vergleich}}", "Bewertung"],
            },
        },
    },
    {
        "compare": 12,
        "render": {
            "title": "Probe",
            "profile": "text",
            "header": "ECOHESION · Dokumentenvergleich",
        },
    },
    {
        "compare": 13,
        "render": {"profile": "memo", "layout": {"body_font_size_pt": "x"}},
        "expect_error": True,
    },
    {
        "compare": 7,
        "render": {
            "layout": {"accent_color": "GGGGGG", "outline": ["{{vergleich}}", "Schluss"]},
            "profile": "memo",
        },
        "reasons": True,
    },
    {"compare": 10, "render": {}},
    {"article": 0, "render": {"user": "Prüfer"}},
    {"article": 1, "render": {"profile": "text"}, "metadata": {"include_consolidated_text": False}},
]


# --------------------------------------------------------------------------- Ablauf


def capture(source: Path) -> dict[str, Any]:  # noqa: C901, PLR0915 - bewusst linear
    blobs = {}
    for relative, expected in BLOBS.items():
        actual = git_blob(source / relative)
        if expected is not None and actual != expected:
            raise SystemExit(f"Blob-Abweichung {relative}: {actual} != {expected}")
        blobs[relative] = actual
    head = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    sys.path.insert(0, str(source / "backend"))
    mcp = install_mcp_stub()
    parsing = importlib.import_module("app.modules.document_compare.parsing")
    matching = importlib.import_module("app.modules.document_compare.matching")
    service_module = importlib.import_module("app.modules.document_compare.service")
    configuration = importlib.import_module("app.modules.document_compare.configuration")
    article_law = importlib.import_module("app.modules.document_compare.article_law")
    types_module = importlib.import_module("app.modules.document_compare.types")
    cli = importlib.import_module("app.modules.document_compare.cli")
    Service = service_module.DocumentCompareService

    out: dict[str, Any] = {
        "schema_version": 1,
        "source": {
            "repository": REPOSITORY,
            "commit": COMMIT,
            "checkout_head": head,
            "blobs": blobs,
        },
        "environment": {
            "python": platform.python_version(),
            "timezone": os.environ.get("TZ", ""),
            "packages": {
                name: importlib.metadata.version(name)
                for name in ("lxml", "python-docx", "pypdf", "rapidfuzz")
            },
            "pdftotext": subprocess.run(
                ["pdftotext", "-v"], capture_output=True, text=True, check=False
            ).stderr.splitlines()[0],
        },
        "fixtures": {},
    }

    def note(name: str) -> None:
        out["fixtures"][name] = sha(name)

    out["constants"] = {
        "VERSION": Service.VERSION,
        "ALLOWED_EXTENSIONS": sorted(Service.ALLOWED_EXTENSIONS),
        "DEFAULT_SETTINGS": configuration.DEFAULT_SETTINGS,
        "DEFAULT_MEMO_OUTLINE": configuration.DEFAULT_MEMO_OUTLINE,
        "ALLOWED_SECTIONS": sorted(configuration.ALLOWED_SECTIONS),
        "HEADING_RE": parsing.HEADING_RE.pattern,
        "PAGE_NUMBER_RE": parsing.PAGE_NUMBER_RE.pattern,
        "LEGAL_REFERENCE_RE": service_module.LEGAL_REFERENCE_RE.pattern,
        "COMMAND_PATTERNS": [[k, p.pattern] for k, p in article_law.COMMAND_PATTERNS],
    }

    out["normalise"] = [
        {
            "text": text,
            "for_match": parsing.normalise_for_match(text),
            "semantic": parsing.normalise_semantic(text),
            "verbatim": parsing.normalise_verbatim(text),
        }
        for text in NORMALISE_TEXTS
    ]
    out["word_diff"] = [
        {"old": old, "new": new, "diff": parsing.word_diff(old, new)}
        for old, new in WORD_DIFF_PAIRS
    ]

    item = types_module.CompareItem
    out["similarity"] = []
    for variant in ("rapidfuzz", "difflib"):
        with scorer(variant):
            for left, right in SIMILARITY_PAIRS:
                out["similarity"].append(
                    {
                        "scorer": variant,
                        "left": left,
                        "right": right,
                        "score": matching.similarity(item("a", text=left), item("b", text=right)),
                    }
                )

    out["read"] = []
    for name, mode, ocr in READ_CASES:
        note(name)
        entry: dict[str, Any] = {"file": name, "mode": mode, "ocr": ocr}
        try:
            resolved, items = parsing.read_document(
                fixture(name), mode, ocr_callback=ocr_callback(ocr)
            )
            entry.update({"resolved_mode": resolved, "items": [asdict(i) for i in items]})
        except Exception as exc:  # noqa: BLE001 - Fehlervertrag wird aufgezeichnet
            entry.update(error(exc))
        out["read"].append(entry)

    # Externe Entität: Inhalt hängt vom Rechner ab, daher nur das Verhalten.
    note("errors/entitaet_extern.docx")
    try:
        _mode, items = parsing.read_document(fixture("errors/entitaet_extern.docx"), "text")
        hostname = Path("/etc/hostname").read_text().strip()
        out["xxe_external"] = {
            "resolved": any(hostname and hostname in i.text for i in items),
            "items": len(items),
        }
    except Exception as exc:  # noqa: BLE001
        out["xxe_external"] = error(exc)

    out["detect_mode"] = []
    for name in sorted({case[0] for case in READ_CASES}):
        try:
            out["detect_mode"].append({"file": name, "mode": parsing.detect_mode(fixture(name))})
        except Exception as exc:  # noqa: BLE001
            out["detect_mode"].append({"file": name, **error(exc)})

    out["pdf_pages"] = []
    for name in PDF_FILES:
        note(name)
        pages = parsing._extract_pdf_pages(fixture(name))
        with without_pdftotext():
            fallback = parsing._extract_pdf_pages(fixture(name))
        out["pdf_pages"].append({"file": name, "extractor": "pdftotext", "pages": pages})
        out["pdf_pages"].append({"file": name, "extractor": "pypdf", "pages": fallback})
        for extractor, extracted in (("pdftotext", pages), ("pypdf", fallback)):
            out["pdf_pages"][-1 if extractor == "pypdf" else -2]["paragraphs"] = [
                list(p) for p in parsing._paragraphs_from_pdf_pages(extracted)
            ]
    with without_pdftotext():
        try:
            parsing._extract_pdf_pages(fixture("errors/kaputt.pdf"))
            out["pypdf_error"] = None
        except Exception as exc:  # noqa: BLE001
            out["pypdf_error"] = error(exc)
    out["page_paragraphs"] = [
        {
            "pages": pages,
            "margins": parsing._remove_repeating_margins(pages),
            "paragraphs": [list(p) for p in parsing._paragraphs_from_pdf_pages(pages)],
        }
        for pages in PAGE_CASES
    ]

    results: list[Any] = []
    out["compare"] = []
    for index, case in enumerate(STANDARD_CASES):
        for variant in ("rapidfuzz", "difflib"):
            note(case["old"])
            note(case["new"])
            entry = {"case": index, "scorer": variant, **copy.deepcopy(case)}
            try:
                with scorer(variant):
                    result = Service.compare(
                        fixture(case["old"]),
                        fixture(case["new"]),
                        ocr_callback=ocr_callback(case.get("ocr", "none")),
                        **case["kwargs"],
                    )
                entry["result"] = result_dict(result)
                if variant == "rapidfuzz":
                    results.append(result)
            except Exception as exc:  # noqa: BLE001
                entry.update(error(exc))
                if variant == "rapidfuzz":
                    results.append(None)
            out["compare"].append(entry)

    articles: list[Any] = []
    out["article_law"] = []
    for index, case in enumerate(ARTICLE_CASES):
        note(case["old"])
        note(case["new"])
        entry = {"case": index, **copy.deepcopy(case)}
        try:
            result = Service.compare(
                fixture(case["old"]), fixture(case["new"]), comparison_type="article_law"
            )
            entry["result"] = result_dict(result)
            articles.append(result)
        except Exception as exc:  # noqa: BLE001
            entry.update(error(exc))
            articles.append(None)
        out["article_law"].append(entry)

    out["settings"] = {"sanitise": [], "merge": [], "load": [], "save": None}
    for value in SETTINGS_INPUTS:
        try:
            out["settings"]["sanitise"].append(
                {"input": value, "output": configuration.sanitise_settings(copy.deepcopy(value))}
            )
        except Exception as exc:  # noqa: BLE001
            out["settings"]["sanitise"].append({"input": value, **error(exc)})
    for department, personal, run_values in MERGE_CASES:
        effective, sources = configuration.merge_settings(department, personal, run_values)
        out["settings"]["merge"].append(
            {
                "department": department,
                "personal": personal,
                "run": run_values,
                "effective": effective,
                "sources": sources,
            }
        )
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        files = {
            "fehlt.json": None,
            "gueltig.json": json.dumps(
                {"threshold": 91, "memo_layout": {"font_family": "Arial"}, "fremd": 1}
            ),
            "kaputt.json": "{kein json",
            "liste.json": "[1, 2]",
        }
        for name, content in files.items():
            if content is not None:
                (base / name).write_text(content, encoding="utf-8")
            try:
                loaded = configuration.load_settings(base / name)
                out["settings"]["load"].append({"file": name, "content": content, "output": loaded})
            except Exception as exc:  # noqa: BLE001
                out["settings"]["load"].append({"file": name, "content": content, **error(exc)})
        saved = configuration.save_settings(
            {"threshold": 72, "mode": "falsch"}, base / "neu" / "s.json"
        )
        out["settings"]["save"] = {
            "input": {"threshold": 72, "mode": "falsch"},
            "returned": saved,
            "file": (base / "neu" / "s.json").read_text(encoding="utf-8"),
        }

    out["verify_references"] = [
        {
            "reason": reason,
            "legal_basis": basis,
            "old": old,
            "new": new,
            "result": list(service_module._verify_legal_references(reason, basis, old, new)),
        }
        for reason, basis, old, new in VERIFY_CASES
    ]
    out["generate_reason"] = []
    for old, new, model, payload in REASON_PAYLOADS:
        mcp.responses = [payload]
        mcp.calls.clear()
        entry = {
            "old": old,
            "new": new,
            "model": model,
            "raw": payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False),
        }
        try:
            reason, metadata = Service.generate_reason(old, new, model)
            entry.update({"reason": reason, "metadata": metadata})
        except Exception as exc:  # noqa: BLE001
            entry.update(error(exc))
        entry["calls"] = copy.deepcopy(mcp.calls)
        out["generate_reason"].append(entry)

    # Rendering mit festen Zeitangaben (Zeitzone aus TZ, hier Europe/Berlin).
    out["render"] = []
    with tempfile.TemporaryDirectory() as temporary:
        for index, case in enumerate(RENDER_CASES):
            source_result = (
                results[case["compare"]] if "compare" in case else articles[case["article"]]
            )
            result = copy.deepcopy(source_result)
            result.created_at = FIXED_CREATED
            result.metadata.update(FIXED_METADATA)
            result.metadata.update(case.get("labels", {}))
            result.metadata.update(case.get("metadata", {}))
            if case.get("reasons"):
                for position, row in enumerate(result.rows):
                    if position == 0:
                        row.reason, row.reason_source = "Präzisiert.", "flowagent"
                        row.reason_warning = "Nicht belegt: § 9"
                    elif position == 1:
                        row.selected = False
                    elif position == 2:
                        row.reason = "Von Hand"
            target = Path(temporary) / f"render-{index}.docx"
            entry = {"case": index, **copy.deepcopy(case), "input": result.to_dict()}
            try:
                Service.render_docx(result, target, **case["render"])
                entry["parts"] = docx_parts(target)
            except Exception as exc:  # noqa: BLE001
                entry.update(error(exc))
            out["render"].append(entry)

    # CLI-/Jupyter-Einstieg compare_documents mit Konfigurationsdatei.
    out["cli"] = []
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        config = base / "department.json"
        configuration.save_settings(
            {
                "threshold": 80,
                "output_profile": "text",
                "text_layout": {"header_text": "Abteilung"},
            },
            config,
        )
        for index, (overrides, responses) in enumerate(
            [
                ({"mode": "checklist", "user": "Prüfer", "title": "CLI"}, []),
                (
                    {"generate_reasons": True, "user": "Prüfer", "model": "m1"},
                    [
                        {"begruendung": "Präzisiert nach § 3 Abs. 2.", "rechtsgrundlage": ""},
                        {"begruendung": "Anders.", "rechtsgrundlage": "Art. 99"},
                        {"begruendung": "Dritte.", "rechtsgrundlage": ""},
                        {"begruendung": "Vierte.", "rechtsgrundlage": ""},
                    ],
                ),
                ({"comparison_type": "article_law", "user": "Prüfer", "header_text": "Kopf"}, []),
            ]
        ):
            mcp.responses = list(responses)
            mcp.calls.clear()
            old, new = (
                ("synthetic/al_stamm.docx", "synthetic/al_befehle.docx")
                if overrides.get("comparison_type") == "article_law"
                else ("synthetic/cl_rich_alt.docx", "synthetic/cl_rich_neu.docx")
            )
            output = base / f"cli-{index}.docx"
            returned = cli.compare_documents(
                fixture(old), fixture(new), output=output, config=config, **overrides
            )
            returned.pop("created_at")
            returned["output"] = Path(returned["output"]).name
            for key in VOLATILE_METADATA:
                returned["metadata"].pop(key, None)
            out["cli"].append(
                {
                    "old": old,
                    "new": new,
                    "config": json.loads(config.read_text()),
                    "overrides": overrides,
                    "responses": responses,
                    "returned": returned,
                    "calls": copy.deepcopy(mcp.calls),
                    "remaining_responses": len(mcp.responses),
                }
            )

    # Celery-Aufgabe mit Stellvertretern für DB/Celery; KI über den MCP-Stellvertreter.
    store: dict[str, FakeComparison] = {}
    install_task_stubs(store)
    tasks = importlib.import_module("app.modules.document_compare.tasks")
    out["task"] = []
    task_cases = [
        (
            {"mode": "checklist", "threshold": 70},
            "synthetic/cl_rich_alt.docx",
            "synthetic/cl_rich_neu.docx",
            [],
        ),
        (
            {"generate_reasons": True, "model": "m2", "old_label": "Alt 2025"},
            "synthetic/cl_rich_alt.docx",
            "synthetic/cl_rich_neu.docx",
            [
                {
                    "begruendung": "Ergänzt nach Art. 63.",
                    "rechtsgrundlage": "VO (EU) 2021/1060",
                    "provider": "flowagent",
                    "temperature": 0,
                },
                RuntimeError("Zeitüberschreitung"),
                {"begruendung": "Dritte.", "rechtsgrundlage": ""},
                {"begruendung": "Vierte.", "rechtsgrundlage": ""},
            ],
        ),
        (
            {"comparison_type": "article_law", "generate_reasons": True},
            "synthetic/al_stamm.docx",
            "synthetic/al_befehle.docx",
            [],
        ),
        ({"mode": "text"}, "synthetic/tx_leer.docx", "synthetic/tx_struktur_neu.docx", []),
        ({}, "errors/leer.pdf", "errors/leer.pdf", []),
    ]
    for index, (options, old, new, responses) in enumerate(task_cases):
        key = f"cmp-{index}"
        store[key] = FakeComparison(copy.deepcopy(options), fixture(old), fixture(new))
        mcp.responses = list(responses)
        mcp.calls.clear()
        task = FakeTask()
        entry: dict[str, Any] = {
            "options": options,
            "old": old,
            "new": new,
            "responses": [
                r if not isinstance(r, BaseException) else {"raise": repr(r)} for r in responses
            ],
        }
        try:
            entry["returned"] = tasks.run_document_comparison(task, key)
        except Exception as exc:  # noqa: BLE001
            entry.update(error(exc))
        comparison = store[key]
        result_json = copy.deepcopy(comparison.result_json)
        if result_json:
            result_json.pop("created_at")
            for volatile in VOLATILE_METADATA:
                result_json["metadata"].pop(volatile, None)
        entry.update(
            {
                "status": getattr(comparison.status, "value", comparison.status),
                "progress": comparison.progress,
                "error_message": comparison.error_message,
                "result_json": result_json,
                "states": task.states,
                "calls": copy.deepcopy(mcp.calls),
            }
        )
        out["task"].append(entry)
    out["task_missing"] = tasks.run_document_comparison(FakeTask(), "gibt-es-nicht")
    out["missing_source_hint"] = tasks._missing_source_hint(
        Path("/ablage/x/alt.docx"), Path("/ablage/x/neu.docx")
    )

    out["worker"] = capture_worker(source)
    return out


WORKER_RUNNER = r"""
import dataclasses, hashlib, importlib.util, io, json, re, sys, types
from pathlib import Path
sys.path.insert(0, sys.argv[1])
recorded = {}
# Paket-__init__ von core.shared und ecohesion importieren FastAPI/DB; nur die
# Namensräume bereitstellen, damit die unveränderten Module selbst laden.
import app.modules
import app.core
for name in (
    "app.core.shared",
    "app.core.shared.research",
    "app.modules.ecohesion",
    "app.modules.ecohesion.services",
    "app.modules.ecohesion.comparisons",
):
    namespace = types.ModuleType(name)
    namespace.__path__ = [str(Path(sys.argv[1], *name.split(".")))]
    sys.modules[name] = namespace
from app.core.shared.research import contracts
real_result = contracts.ResearchResult
class RecordingResult(real_result):
    def __init__(self, **kwargs):
        recorded["research_result"] = kwargs
        super().__init__(**kwargs)
contracts.ResearchResult = RecordingResult
from app.modules.ecohesion.services import research_pdf
real_render = research_pdf.render_pdf
def render_pdf(title, result, options):
    recorded["render_pdf"] = {"title": title, "options": options}
    data = real_render(title, result, options)
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    recorded["pdf"] = {
        "pages": [page.extract_text() for page in reader.pages],
        "title": reader.metadata.get("/Title"),
        "author": reader.metadata.get("/Author"),
        "sha256_without_dates": hashlib.sha256(
            re.sub(rb"/(CreationDate|ModDate) \\(D:[^)]*\\)|/ID\\s*\\[[^\\]]*\\]", b"", data)
        ).hexdigest(),
    }
    return data
research_pdf.render_pdf = render_pdf
from app.modules.ecohesion.comparisons import worker
code = worker.main(Path(sys.argv[2]))
payload = json.dumps({"code": code, **recorded}, ensure_ascii=False, default=str)
(Path(sys.argv[2]) / "recorded.json").write_text(payload)
"""


def capture_worker(source: Path) -> list[dict[str, Any]]:
    """ecohesion-Worker in eigenem Prozess (er setzt RLIMIT_CPU/RLIMIT_AS)."""
    cases = [
        ("synthetic/cl_rich_alt.docx", "synthetic/cl_rich_neu.docx", "auto", 85, False),
        (
            "public/KassenSichV_2023-06-10.pdf",
            "public/KassenSichV_2026-08-27.pdf",
            "auto",
            85,
            False,
        ),
        ("synthetic/tx_struktur_alt.docx", "synthetic/cl_basis_neu.docx", "auto", 85, False),
        ("synthetic/tx_verschoben_alt.docx", "synthetic/tx_verschoben_neu.docx", "text", 85, False),
        (
            "public/KassenSichV_2025-06-01.docx",
            "public/KassenSichV_2026-05-06.docx",
            "auto",
            90,
            True,
        ),
    ]
    entries = []
    for old, new, mode, threshold, editorial in cases:
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder / "old.bin").write_bytes(fixture(old).read_bytes())
            (folder / "new.bin").write_bytes(fixture(new).read_bytes())
            # Der Worker erhält umbenannte Dateien; die Endung bleibt maßgeblich.
            old_name, new_name = f"alt{Path(old).suffix}", f"neu{Path(new).suffix}"
            (folder / "old.bin").rename(folder / old_name)
            (folder / "new.bin").rename(folder / new_name)
            spec = {
                "old_path": old_name,
                "new_path": new_name,
                "old_filename": Path(old).name,
                "new_filename": Path(new).name,
                "mode": mode,
                "threshold": threshold,
                "include_editorial": editorial,
                "title": "Vergleich ECOHESION",
            }
            (folder / "input.json").write_text(json.dumps(spec))
            runner = folder / "runner.py"
            runner.write_text(WORKER_RUNNER)
            completed = subprocess.run(
                [sys.executable, str(runner), str(source / "backend"), str(folder)],
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, "PYTHONHASHSEED": "0"},
            )
            recorded = (
                json.loads((folder / "recorded.json").read_text())
                if (folder / "recorded.json").exists()
                else {}
            )
            result = (
                json.loads((folder / "result.json").read_text())
                if (folder / "result.json").exists()
                else None
            )
            if result:
                result.pop("created_at")
            entries.append(
                {
                    "old": old,
                    "new": new,
                    "spec": spec,
                    "returncode": completed.returncode,
                    "stderr_tail": completed.stderr[-400:] if completed.returncode else "",
                    "recorded": recorded,
                    "result": result,
                    "error": json.loads((folder / "error.json").read_text())
                    if (folder / "error.json").exists()
                    else None,
                    "docx_written": (folder / "comparison.docx").is_file(),
                    "pdf_written": (folder / "comparison.pdf").is_file(),
                }
            )
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=FIXTURES / "legacy_observed.json")
    args = parser.parse_args()
    if os.environ.get("TZ") != "Europe/Berlin":
        raise SystemExit("TZ=Europe/Berlin erforderlich (Zeitformat im Renderer)")
    time.tzset()
    first = capture(args.source.resolve())
    args.output.write_text(
        json.dumps(first, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    counts = {
        key: len(value) if isinstance(value, list) else None
        for key, value in first.items()
        if isinstance(value, list)
    }
    print(json.dumps({"written": str(args.output), "counts": counts}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
