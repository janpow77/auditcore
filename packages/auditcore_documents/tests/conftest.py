"""Gemeinsame Test-Hilfen: Fixtures, aufgezeichnete PDF-Seiten, feste Zeitzone."""

from __future__ import annotations

import json
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
# Der Renderer formatiert Zeitangaben in der lokalen Zeitzone (wie das Original);
# die Charakterisierung lief mit Europe/Berlin.
os.environ["TZ"] = "Europe/Berlin"
time.tzset()


@lru_cache(maxsize=1)
def observed() -> dict[str, Any]:
    return json.loads((FIXTURES / "legacy_observed.json").read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def fixture_path(name: str) -> Path:
    return FIXTURES / name


def recorded_pages(extractor: str = "pdftotext") -> dict[str, list[str]]:
    """PDF-Seiten, wie sie in der Referenzumgebung extrahiert wurden."""
    return {
        Path(entry["file"]).name: entry["pages"]
        for entry in observed()["pdf_pages"]
        if entry["extractor"] == extractor
    }


def recorded_page_source(path: Path) -> list[str]:
    """Seitenquelle für Wiederholungen: aufgezeichnete Seiten, sonst echte Extraktion."""
    pages = recorded_pages()
    if path.name in pages and path.parent.name == "public":
        return list(pages[path.name])
    from auditcore_documents import legacy_pdf_pages

    return legacy_pdf_pages(path)


@pytest.fixture
def legacy_data() -> dict[str, Any]:
    return observed()
