"""Check package READMEs against docs/bibliotheken/readme-vorlage.md.

Structural rules only; the quick-start code runs separately
(``readme_snippets.py`` for Python, ``scripts/js/check-readme-snippets.mjs``
for npm packages) and the API block is compared by ``api_overview.py``.

    python scripts/docs/readme_check.py                 # alle Pakete
    python scripts/docs/readme_check.py packages/auditcore_geo
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generated_blocks import ROOT, has_block  # noqa: E402
from readme_snippets import code_blocks, section  # noqa: E402

INDEX_URL = "https://janpow77.github.io/auditcore/simple/"
PYTHON_SECTIONS = (
    "Zweck",
    "Installation",
    "Schnellstart",
    "API-Überblick",
    "Profile und Konfiguration",
    "Herkunft und Charakterisierung",
    "Bewusste Verhaltensabweichungen",
    "Abhängigkeiten",
    "Sicherheit und Datenschutz",
    "Lizenz und Herkunftsnachweis",
    "Änderungen",
)
JS_SECTIONS = (
    "Zweck",
    "Installation",
    "Schnellstart",
    "Einbindung",
    "API-Überblick",
    "Konfiguration",
    "Herkunft und Charakterisierung",
    "Abhängigkeiten",
    "Sicherheit und Datenschutz",
    "Lizenz und Herkunftsnachweis",
    "Änderungen",
)
MAX_CATALOG_LINE = 240
# ASCII-Ersatz für Umlaute und falsche Fachbegriffe (außerhalb von Code).
FORBIDDEN = re.compile(
    r"\b(fuer|ueber\w*|Ueber\w*|[Pp]ruef\w*|koenn\w*|moeglich\w*|[Aa]ender\w*|gemaess|"
    r"waehrend|[Ss]chluessel\w*|naechst\w*|[Bb]ehoerd\w*|[Ff]oerder\w*|Findung\w*|VKO)\b"
)


def headings(text: str) -> list[str]:
    return re.findall(r"^## (.+?)\s*$", text, re.M)


def prose(text: str) -> str:
    """Text without fenced code, inline code, links targets and HTML comments."""
    text = re.sub(r"^```.*?^```\s*$", "", text, flags=re.S | re.M)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    return re.sub(r"\]\([^)]*\)", "]", text)


def catalog_line(text: str) -> str:
    """First paragraph of „Zweck“ as one line (used by the package catalog)."""
    body = section(text, "Zweck").strip()
    paragraph = body.split("\n\n", 1)[0]
    return " ".join(line.strip() for line in paragraph.splitlines())


def _order_problems(text: str, required: tuple[str, ...]) -> list[str]:
    found = headings(text)
    missing = [title for title in required if title not in found]
    problems = [f"Pflichtabschnitt „## {title}“ fehlt" for title in missing]
    positions = [found.index(title) for title in required if title in found]
    if not missing and positions != sorted(positions):
        problems.append("Pflichtabschnitte stehen nicht in der Reihenfolge der Vorlage")
    for title in required:
        if title in found and not section(text, title).strip():
            problems.append(f"Abschnitt „## {title}“ ist leer")
    return problems


def _common_problems(package_dir: Path, text: str, version: str) -> list[str]:
    problems = []
    line = catalog_line(text)
    if not line or len(line) > MAX_CATALOG_LINE:
        problems.append(
            f"„## Zweck“: erster Absatz ist die Katalogzeile (1–{MAX_CATALOG_LINE} Zeichen)"
        )
    if not has_block(text, "api-overview"):
        problems.append("„## API-Überblick“: Markierungen <!-- api-overview:start/end --> fehlen")
    changes = section(text, "Änderungen")
    changelog = package_dir / "CHANGELOG.md"
    if "CHANGELOG.md" not in changes:
        problems.append("„## Änderungen“: Link auf CHANGELOG.md fehlt")
    if not changelog.is_file():
        problems.append("CHANGELOG.md fehlt")
    elif not re.search(rf"^## \[?{re.escape(version)}\b", changelog.read_text("utf-8"), re.M):
        problems.append(f"CHANGELOG.md: Überschrift „## {version} …“ zur aktuellen Version fehlt")
    if "LICENSE" not in section(text, "Lizenz und Herkunftsnachweis"):
        problems.append("„## Lizenz und Herkunftsnachweis“: Verweis auf LICENSE fehlt")
    for match in sorted(set(FORBIDDEN.findall(prose(text)))):
        problems.append(f"Sprachregel: „{match}“ (echte Umlaute bzw. Fachbegriff verwenden)")
    return problems


def _python_install_problems(text: str, project: dict[str, Any]) -> list[str]:
    install = section(text, "Installation")
    distribution = str(project["name"])
    apt = "python3-" + distribution.replace("_", "-").lower()
    problems = [
        f"„## Installation“: {label} fehlt"
        for label, needle in (
            ("Paketindex (--index-url " + INDEX_URL + ")", INDEX_URL),
            ("--index-url", "--index-url"),
            ("Direkt-URL mit #sha256=", "#sha256="),
            (f"APT-Paket {apt}", apt),
        )
        if needle not in install
    ]
    extras = [name for name in project.get("optional-dependencies", {}) if name != "dev"]
    problems += [
        f"„## Installation“: Extra [{extra}] nicht beschrieben"
        for extra in extras
        if f"[{extra}]" not in install
    ]
    return problems


def _requirement_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
    return match.group(1) if match else requirement


def check_python(package_dir: Path) -> list[str]:
    text = (package_dir / "README.md").read_text("utf-8")
    project = tomllib.loads((package_dir / "pyproject.toml").read_text("utf-8"))["project"]
    problems = _order_problems(text, PYTHON_SECTIONS)
    problems += _common_problems(package_dir, text, str(project["version"]))
    problems += _python_install_problems(text, project)
    quick = [info for info, _ in code_blocks(section(text, "Schnellstart"))]
    if not any(info.split()[:1] in (["python"], ["pycon"]) for info in quick if info):
        problems.append("„## Schnellstart“: ausführbarer ```python- oder ```pycon-Block fehlt")
    behaviour = package_dir / "docs" / "behavior-changes.md"
    if behaviour.is_file() and "docs/behavior-changes.md" not in section(
        text, "Bewusste Verhaltensabweichungen"
    ):
        problems.append("„## Bewusste Verhaltensabweichungen“: Link docs/behavior-changes.md fehlt")
    dependencies = section(text, "Abhängigkeiten")
    for requirement in project.get("dependencies", []):
        name = _requirement_name(requirement)
        if name not in dependencies:
            problems.append(f"„## Abhängigkeiten“: {name} nicht genannt")
    licence = section(text, "Lizenz und Herkunftsnachweis")
    if (package_dir / "provenance.json").is_file() and "provenance.json" not in licence:
        problems.append("„## Lizenz und Herkunftsnachweis“: Verweis auf provenance.json fehlt")
    return problems


def _js_usage_problems(text: str, manifest: dict[str, Any]) -> list[str]:
    usage = section(text, "Einbindung")
    peers = {**manifest.get("dependencies", {}), **manifest.get("peerDependencies", {})}
    needed = []
    if "vue" in peers:
        needed.append("Vue")
    if "./elements" in manifest.get("exports", {}):
        needed.append("Web Component")
    if "react" in peers:
        needed.append("React")
    return [f"„## Einbindung“: Nutzung mit {word} fehlt" for word in needed if word not in usage]


def check_js(package_dir: Path) -> list[str]:
    text = (package_dir / "README.md").read_text("utf-8")
    manifest = json.loads((package_dir / "package.json").read_text("utf-8"))
    problems = _order_problems(text, JS_SECTIONS)
    problems += _common_problems(package_dir, text, str(manifest["version"]))
    if f"npm install {manifest['name']}" not in section(text, "Installation"):
        problems.append(f"„## Installation“: `npm install {manifest['name']}` fehlt")
    quick = [info.split()[:1] for info, _ in code_blocks(section(text, "Schnellstart"))]
    if not any(words in (["ts"], ["tsx"]) for words in quick):
        problems.append("„## Schnellstart“: ```ts- oder ```tsx-Block fehlt")
    problems += _js_usage_problems(text, manifest)
    dependencies = section(text, "Abhängigkeiten")
    for field in ("dependencies", "peerDependencies"):
        for name in manifest.get(field, {}):
            if name not in dependencies:
                problems.append(f"„## Abhängigkeiten“: {name} nicht genannt")
    return problems


def check(package_dir: Path) -> list[str]:
    """All structural problems of one package README (empty = conforming)."""
    if not (package_dir / "README.md").is_file():
        return ["README.md fehlt"]
    if (package_dir / "package.json").is_file():
        return check_js(package_dir)
    return check_python(package_dir)


def all_packages(root: Path = ROOT) -> list[Path]:
    python = sorted(p.parent for p in root.glob("packages/*/pyproject.toml"))
    js = sorted(p.parent for p in root.glob("packages-js/*/package.json"))
    return python + js


def pending(root: Path = ROOT) -> set[str]:
    """Packages whose README is not yet revised (shrinking ratchet list)."""
    path = root / "docs" / "bibliotheken" / "readme-offen.json"
    return {str(name) for name in json.loads(path.read_text("utf-8"))["pakete"]}


def main(argv: list[str]) -> int:
    targets = [Path(arg).resolve() for arg in argv] or all_packages()
    skipped = pending()
    failed = False
    for package_dir in targets:
        problems = check(package_dir)
        marker = " (noch in readme-offen.json)" if package_dir.name in skipped else ""
        for problem in problems:
            print(f"{package_dir.relative_to(ROOT)}{marker}: {problem}")
        failed = failed or bool(problems and not marker)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
