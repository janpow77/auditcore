"""Erzeugt ``src/auditcore_risk/web/field_catalog.json`` aus ``tools/document_fields.py``.

Die Weboberfläche zeigt je Profil die Eingabefelder mit Bedeutung, Beleg,
Pflicht/optional und dem Verhalten bei fehlender Spalte oder leerem Wert. Die
Inhalte stammen unverändert aus derselben Ableitung wie ``docs/eingabefelder.md``
(``profile_entries`` und ``meanings``); dieses Werkzeug schreibt sie nur als JSON,
damit das installierte Paket sie ohne die Werkzeuge ausliefern kann.

Aufruf (im Paketverzeichnis)::

    python tools/export_field_catalog.py          # schreibt die Datei
    python tools/export_field_catalog.py --check  # Exit 1, wenn die Datei veraltet ist

``tests/test_web_field_catalog.py`` prüft, dass die Datei aktuell ist.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "src" / "auditcore_risk" / "web" / "field_catalog.json"
SCHEMA = "auditcore_risk.field-catalog/1"


def _document_fields() -> ModuleType:
    """``tools/document_fields.py`` als Modul (liegt nicht im installierten Paket)."""
    name = "auditcore_risk_document_fields"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / "document_fields.py")
    if spec is None or spec.loader is None:
        raise SystemExit("tools/document_fields.py nicht gefunden.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _requirement(entries: list[Any]) -> str:
    if any(e.value_required for e in entries):
        return "value_required"
    if any(e.required for e in entries):
        return "required"
    return "optional"


def _field(name: str, entries: list[Any], known: Mapping[str, Any]) -> dict[str, Any]:
    meaning = known.get(name)
    return {
        "name": name,
        "meaning": None if meaning is None else meaning.text,
        "meaning_source": None if meaning is None else meaning.source,
        "requirement": _requirement(entries),
        "required_by": [e.code for e in entries if e.required],
        "value_required_by": [e.code for e in entries if e.value_required],
        "uses": [
            {"code": e.code, "label": e.label, "role": e.role, "absent": e.absent, "empty": e.empty}
            for e in entries
        ],
    }


def build() -> dict[str, Any]:
    """Katalog aller Profile: Schlüssel ``<id>@<version>``, Felder in Anzeigereihenfolge."""
    tool = _document_fields()
    profiles: dict[str, Any] = {}
    for data in tool._load():
        entries = tool.profile_entries(data)
        known = tool.meanings(data["id"], data["version"])
        order = sorted(entries, key=lambda n: (n.lstrip("_").casefold(), n))
        profiles[f"{data['id']}@{data['version']}"] = {
            "fingerprint": tool.fingerprint(data),
            "input_contract": data["source"].get("input_contract"),
            "fields": [_field(name, entries[name], known) for name in order],
        }
    return {
        "schema": SCHEMA,
        "generated_by": "tools/export_field_catalog.py",
        "undocumented": tool.UNDOCUMENTED,
        "profiles": profiles,
    }


def render() -> str:
    """Inhalt der Katalogdatei (stabil sortiert, UTF-8 mit echten Umlauten)."""
    return json.dumps(build(), ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Schreibt die Datei oder prüft mit ``--check``, ob sie aktuell ist."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--check", action="store_true", help="nur prüfen, nicht schreiben")
    args = parser.parse_args(argv)
    content = render()
    current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else None
    if args.check:
        if current != content:
            print(f"{OUTPUT} ist veraltet: python tools/export_field_catalog.py", file=sys.stderr)
            return 1
        return 0
    if current != content:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
