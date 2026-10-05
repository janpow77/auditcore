"""Plugin ``auditcore-office``: Manifest, Skills und Agenten sind vollständig beschrieben."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "auditcore-office"
SKILLS = {
    "office-projekt-start",
    "office-vm-einrichten",
    "office-vm-lauf",
    "mcp-vorlauf",
    "sollwerte-abnahme",
    "lieferpaket",
    "qchess-dienst",
    "office-mac-probelauf",
}
AGENTS = {
    "office-integration",
    "office-fach",
    "office-sollwerte",
    "office-mcp-vorlauf",
    "office-texte",
    "office-namensabgleich",
}
FRONTMATTER = re.compile(r"\A---\nname: (?P<name>[a-z0-9-]+)\ndescription: (?P<desc>.+)\n---\n")


def _frontmatter(path: Path) -> tuple[str, str]:
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    assert match, f"{path.relative_to(ROOT)}: Frontmatter mit name/description fehlt"
    return match["name"], match["desc"]


def test_manifest() -> None:
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "auditcore-office"
    assert re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"])
    assert manifest["license"] == "MIT"


def test_skills_match_plan() -> None:
    found = {path.parent.name for path in PLUGIN.glob("skills/*/SKILL.md")}
    assert found == SKILLS
    for name in SKILLS:
        assert _frontmatter(PLUGIN / "skills" / name / "SKILL.md")[0] == name


def test_agents_match_plan() -> None:
    assert {path.stem for path in PLUGIN.glob("agents/*.md")} == AGENTS
    for name in AGENTS:
        assert _frontmatter(PLUGIN / "agents" / f"{name}.md")[0] == name


def test_plugin_names_no_hosts_or_private_paths() -> None:
    forbidden = re.compile(
        r"(/Users/|/home/|~/(?!\.config/auditcore-officebank)|\b\d{1,3}(\.\d{1,3}){3}\b)"
    )
    for path in PLUGIN.rglob("*"):
        if path.is_file():
            assert not forbidden.search(path.read_text(encoding="utf-8")), path.name
