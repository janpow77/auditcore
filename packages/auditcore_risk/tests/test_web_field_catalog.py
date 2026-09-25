"""``src/auditcore_risk/web/field_catalog.json`` bleibt mit den Profilen synchron.

Die Datei ist die JSON-Fassung von ``docs/eingabefelder.md`` für die
Weboberfläche; ``python tools/export_field_catalog.py`` erzeugt sie neu.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]


def _tool() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "export_field_catalog", ROOT / "tools" / "export_field_catalog.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_catalog_is_current() -> None:
    tool = _tool()
    actual = (ROOT / "src" / "auditcore_risk" / "web" / "field_catalog.json").read_text("utf-8")
    assert actual == tool.render(), "field_catalog.json veraltet: tools/export_field_catalog.py"
    assert tool.main(["--check"]) == 0


def test_catalog_matches_markdown_profiles() -> None:
    data = json.loads(_tool().render())
    text = (ROOT / "docs" / "eingabefelder.md").read_text(encoding="utf-8")
    for key, entry in data["profiles"].items():
        profile_id, version = key.split("@")
        assert f"\n## {profile_id} {version}\n" in text
        assert f"Fingerabdruck `{entry['fingerprint']}`" in text
        for field in entry["fields"]:
            assert field["requirement"] in {"optional", "required", "value_required"}
            assert field["uses"]
