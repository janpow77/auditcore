"""Generate the README section „API-Überblick“ of every library package.

Python packages (``packages/*``) are read statically from ``__all__`` (see
``python_api.py``); npm packages (``packages-js/*``) through the TypeScript
compiler API (``js_api.mjs``, needs ``npm ci``). The result replaces the block
between ``<!-- api-overview:start … -->`` and ``<!-- api-overview:end -->``.

    python scripts/docs/api_overview.py --write            # alle Pakete schreiben
    python scripts/docs/api_overview.py --check --python   # CI: Python aktuell?
    python scripts/docs/api_overview.py --check --js       # CI: npm-Pakete aktuell?
    python scripts/docs/api_overview.py --write packages/auditcore_geo
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generated_blocks import ROOT, MarkerError, md_cell, sync_file  # noqa: E402
from python_api import collect, public_modules  # noqa: E402

BLOCK = "api-overview"
COMMAND = "python scripts/docs/api_overview.py --write"


def python_import_name(package_dir: Path) -> str:
    project = tomllib.loads((package_dir / "pyproject.toml").read_text(encoding="utf-8"))
    name = str(project["project"]["name"]).replace("-", "_")
    if (package_dir / "src" / name).is_dir():
        return name
    candidates = [p.name for p in (package_dir / "src").iterdir() if (p / "__init__.py").is_file()]
    return sorted(candidates)[0]


def render_python(package_dir: Path) -> str:
    package = python_import_name(package_dir)
    names, entries = collect(package_dir / "src", package)
    lines: list[str] = []
    if names is None:
        lines.append(f"`{package}` definiert kein `__all__`; die Module sind der Einstieg.")
    else:
        lines += [
            f"Öffentliche Namen aus `{package}.__all__` ({len(entries)}):",
            "",
            "| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |",
            "|---|---|---|---|",
        ]
        lines += [
            f"| `{e.name}` | {e.kind} | {md_cell(e.summary)} | `{e.module}` |" for e in entries
        ]
    modules = public_modules(package_dir / "src" / package)
    if modules:
        lines += ["", "Öffentliche Module:", "", "| Modul | Kurzbeschreibung |", "|---|---|"]
        lines += [f"| `{package}.{m.name}` | {md_cell(m.summary)} |" for m in modules]
    return "\n".join(lines)


def js_data(package_dir: Path) -> dict[str, Any]:
    script = Path(__file__).resolve().parent / "js_api.mjs"
    completed = subprocess.run(
        ["node", str(script), str(package_dir)],
        check=True, capture_output=True, text=True, cwd=ROOT,
    )
    data: dict[str, Any] = json.loads(completed.stdout)
    return data


def _js_exports(data: dict[str, Any]) -> list[str]:
    entries = data["entries"]
    lines = [
        f"Exporte der Einstiegspunkte aus `package.json#exports` ({len(entries)}):",
        "",
        "| Einstieg | Name | Art | Kurzbeschreibung (erste JSDoc-Zeile) | Modul |",
        "|---|---|---|---|---|",
    ]
    for e in entries:
        entry = data["name"] + e["entry"].removeprefix(".")
        lines.append(
            f"| `{entry}` | `{e['name']}` | {e['kind']} | {md_cell(e['summary'])} "
            f"| `{e['module'] or '–'}` |"
        )
    return lines


def _js_elements(data: dict[str, Any]) -> list[str]:
    if not data["elements"]:
        return []
    lines = ["", "Web Components:", ""]
    lines += ["| Element | Vue-Komponente | Definiert in |", "|---|---|---|"]
    lines += [
        f"| `<{e['tag']}>` | `{e['component']}` | `{e['module']}` |" for e in data["elements"]
    ]
    return lines


def _js_component(component: dict[str, Any]) -> list[str]:
    lines = ["", f"#### `{component['name']}`"]
    if component["summary"]:
        lines += ["", component["summary"]]
    if component["props"]:
        lines += ["", "| Prop | Typ | Pflicht | Standard | Beschreibung |", "|---|---|---|---|---|"]
        for p in component["props"]:
            required = "ja" if p["required"] else "nein"
            default = f"`{md_cell(p['default'])}`" if p["default"] else "–"
            lines.append(
                f"| `{p['name']}` | `{md_cell(p['type'])}` | {required} "
                f"| {default} | {md_cell(p['doc'])} |"
            )
    if component["events"]:
        lines += ["", "| Ereignis | Nutzdaten | Beschreibung |", "|---|---|---|"]
        lines += [
            f"| `{e['name']}` | `{md_cell(e['payload'])}` | {md_cell(e['doc'])} |"
            for e in component["events"]
        ]
    if not component["props"] and not component["events"]:
        lines += ["", "Keine Props und keine Ereignisse."]
    return lines


def render_js(package_dir: Path) -> str:
    data = js_data(package_dir)
    lines = _js_exports(data) + _js_elements(data)
    if data["components"]:
        lines += ["", "### Props und Ereignisse der Vue-Komponenten"]
        for component in data["components"]:
            lines += _js_component(component)
    return "\n".join(lines)


def packages(root: Path, *, python: bool, js: bool) -> list[Path]:
    found: list[Path] = []
    if python:
        found += sorted(p.parent for p in root.glob("packages/*/pyproject.toml"))
    if js:
        found += sorted(p.parent for p in root.glob("packages-js/*/package.json"))
    return found


def render(package_dir: Path) -> str:
    if (package_dir / "package.json").is_file():
        return render_js(package_dir)
    return render_python(package_dir)


def run(targets: Iterable[Path], *, write: bool, skip: set[str]) -> list[str]:
    """Synchronise every README; return the problems (empty = all current)."""
    problems = []
    for package_dir in targets:
        readme = package_dir / "README.md"
        label = package_dir.relative_to(ROOT).as_posix()
        try:
            current = sync_file(readme, BLOCK, COMMAND, render(package_dir), write=write)
        except MarkerError as error:
            if package_dir.name not in skip:
                problems.append(f"{label}/README.md: {error}")
            continue
        if not current and not write:
            problems.append(f"{label}/README.md: API-Überblick veraltet – `{COMMAND}` ausführen")
    return problems


def pending_packages() -> set[str]:
    path = ROOT / "docs" / "bibliotheken" / "readme-offen.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(name) for name in data["pakete"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Blöcke neu schreiben")
    mode.add_argument("--check", action="store_true", help="nur prüfen (CI)")
    parser.add_argument("--python", action="store_true", help="nur packages/*")
    parser.add_argument("--js", action="store_true", help="nur packages-js/*")
    parser.add_argument("paths", nargs="*", type=Path, help="einzelne Paketverzeichnisse")
    args = parser.parse_args(argv)
    both = not args.python and not args.js
    targets = [p.resolve() for p in args.paths] or packages(
        ROOT, python=args.python or both, js=args.js or both
    )
    problems = run(targets, write=args.write, skip=pending_packages())
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
