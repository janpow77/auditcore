"""Generate the package catalog in README.md and docs/bibliotheken/uebersicht.md.

Every row is derived from files in the repository: name, version and
dependencies from ``pyproject.toml`` / ``package.json``, the purpose from the
first paragraph of the README section „Zweck“ (fallback: the manifest
description), the status from ``provenance.json`` („spezifiziert“ only with a
holding ``specification`` block, see ``specification.py``).

    python scripts/docs/catalog.py --write
    python scripts/docs/catalog.py --check      # CI
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generated_blocks import ROOT, md_cell, sync_file  # noqa: E402
from readme_check import catalog_line  # noqa: E402
from specification import specified  # noqa: E402

BLOCK = "paketkatalog"
COMMAND = "python scripts/docs/catalog.py --write"
CROSS_CUTTING = {"common", "auth", "identifiers", "llm_client", "harvest"}
CATEGORIES = (
    "Querschnitt",
    "Fachbibliotheken",
    "Quellen-Adapter",
    "Oberfläche und Frontend-Logik (npm)",
)


@dataclass(frozen=True)
class Package:
    name: str
    path: str
    version: str
    purpose: str
    dependencies: str
    status: str
    category: str


def _short(name: str) -> str:
    return name.removeprefix("auditcore_").removeprefix("auditcore-")


def category(name: str, *, js: bool) -> str:
    if js:
        return CATEGORIES[3]
    short = _short(name.replace("-", "_"))
    if short in CROSS_CUTTING:
        return CATEGORIES[0]
    if short.endswith("_sources"):
        return CATEGORIES[2]
    return CATEGORIES[1]


def status(package_dir: Path) -> str:
    """Status from provenance.json (without one: new).

    A characterised package with a holding ``specification`` block is
    „spezifiziert“; a declared block that does not hold raises.
    """
    path = package_dir / "provenance.json"
    if not path.is_file():
        return "neu"
    data: dict[str, Any] = json.loads(path.read_text("utf-8"))
    classification = str(data.get("classification") or "")
    characterised = bool(data.get("characterization") or data.get("characterization_cases"))
    if classification.startswith("CONSOLIDATION"):
        return "konsolidiert (Gleichheitsnachweis)"
    if classification.startswith("NEW"):
        return "neu, gegen charakterisierte Verträge" if characterised else "neu"
    if not characterised:
        return "neu"
    return "spezifiziert" if specified(package_dir, data) else "charakterisiert"


def _purpose(package_dir: Path, description: str) -> str:
    readme = package_dir / "README.md"
    line = catalog_line(readme.read_text("utf-8")) if readme.is_file() else ""
    return line or description


def _requirements(requirements: list[str]) -> str:
    names = [re.split(r"[<>=!~ \[;]", r, maxsplit=1)[0] + _pin(r) for r in requirements]
    return ", ".join(f"`{n}`" for n in names) or "keine"


def _pin(requirement: str) -> str:
    match = re.search(r"(==|>=|~=|\^)\s*[\w.]+", requirement)
    return match.group(0).replace(" ", "") if match else ""


def python_package(package_dir: Path) -> Package:
    project = tomllib.loads((package_dir / "pyproject.toml").read_text("utf-8"))["project"]
    extras = [e for e in project.get("optional-dependencies", {}) if e != "dev"]
    deps = _requirements(list(project.get("dependencies", [])))
    if extras:
        deps += "; Extras: " + ", ".join(f"`{e}`" for e in extras)
    name = str(project["name"])
    return Package(
        name, package_dir.relative_to(ROOT).as_posix(), str(project["version"]),
        _purpose(package_dir, str(project.get("description", ""))), deps,
        status(package_dir), category(name, js=False),
    )


def js_package(package_dir: Path) -> Package:
    manifest = json.loads((package_dir / "package.json").read_text("utf-8"))
    runtime = manifest.get("dependencies", {})
    peers = manifest.get("peerDependencies", {})
    parts = [f"`{n}@{v}`" for n, v in runtime.items()]
    parts += [f"`{n}@{v}` (peer)" for n, v in peers.items()]
    name = str(manifest["name"])
    return Package(
        name, package_dir.relative_to(ROOT).as_posix(), str(manifest["version"]),
        _purpose(package_dir, str(manifest.get("description", ""))),
        ", ".join(parts) or "keine", status(package_dir), category(name, js=True),
    )


def collect(root: Path = ROOT) -> list[Package]:
    python = [python_package(p.parent) for p in sorted(root.glob("packages/*/pyproject.toml"))]
    js = [js_package(p.parent) for p in sorted(root.glob("packages-js/*/package.json"))]
    return python + js


def _row(package: Package, link_prefix: str) -> str:
    link = f"[`{package.name}`]({link_prefix}{package.path})"
    return (
        f"| {link} | {package.version} | {md_cell(package.purpose)} "
        f"| {package.dependencies} | {package.status} |"
    )


def render_table(packages: list[Package], link_prefix: str) -> list[str]:
    lines = ["| Paket | Version | Zweck | Abhängigkeiten | Status |", "|---|---|---|---|---|"]
    return lines + [_row(p, link_prefix) for p in packages]


def render_readme(packages: list[Package]) -> str:
    lines = [f"{len(packages)} Pakete, gruppiert nach Einordnung "
             "([Übersicht](docs/bibliotheken/uebersicht.md)):"]
    for name in CATEGORIES:
        group = [p for p in packages if p.category == name]
        if group:
            lines += ["", f"**{name}**", "", *render_table(group, "")]
    return "\n".join(lines)


def render_overview(packages: list[Package]) -> str:
    lines: list[str] = []
    for name in CATEGORIES:
        group = [p for p in packages if p.category == name]
        if group:
            lines += [f"### {name}", "", *render_table(group, "../../"), ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    packages = collect()
    targets = (
        (ROOT / "README.md", render_readme(packages)),
        (ROOT / "docs" / "bibliotheken" / "uebersicht.md", render_overview(packages)),
    )
    stale = [
        path for path, content in targets
        if not sync_file(path, BLOCK, COMMAND, content, write=args.write)
    ]
    for path in stale if args.check else []:
        print(f"{path.relative_to(ROOT)}: Paketkatalog veraltet – `{COMMAND}` ausführen",
              file=sys.stderr)
    return 1 if stale and args.check else 0


if __name__ == "__main__":
    raise SystemExit(main())
