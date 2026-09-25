"""Measure the binding Python code-quality metrics of one package.

Every metric is a plain count so that the ratchet can compare it against the
baseline: complexity violations (ruff C901, McCabe > 10), oversized modules and
functions, ``Any`` usages, mypy ``--strict`` errors and non-English identifiers.
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess  # nosec B404
import sys
import tempfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

MAX_COMPLEXITY = 10
MAX_MODULE_LINES = 400
MAX_FUNCTION_LINES = 60
PYTHON_METRICS = (
    "complexity_over_10",
    "modules_over_400_lines",
    "functions_over_60_lines",
    "any_usages",
    "mypy_strict_errors",
    "non_english_identifiers",
)


def _words(text: str) -> tuple[str, ...]:
    return tuple(text.split())


#: German word stems that must not appear in def/class names (heuristic).
#: Both umlaut and ASCII-substitute spellings are listed on purpose.
GERMAN_STEMS = _words(
    """
    pruef prüf antrag antraeg anträg beleg rechnung betrag betraeg beträg foerder
    förder zahlung vorhaben feststellung bescheid behoerde behörde stichprob ergebnis
    bericht erstell berechn ermittl erzeug verarbeit speicher aktualisier loesch lösch
    hinzufueg hinzufüg gesamt kosten ausgabe einnahme zuwendung beguenstig begünstig
    empfaeng empfäng auftrag vergabe angebot schluessel schlüssel tabelle spalte zeile
    nummer anzahl steuer umsatz brutto gemeinde unternehmen pruefung kennzahl zeitraum
    stamm vorgang verfahren einstell auswert uebersicht übersicht zusammenfass abgleich
    bewert gueltig gültig fehler hinweis eintrag eintraeg einträg
    """
)
#: Short German words that are only flagged as complete name tokens.
GERMAN_TOKENS = frozenset(
    _words(
        """
    und oder fuer für von nach bei aus ist hat hole lade wert werte jahr liste
    datei daten summe frist neu alle keine nicht pruefe prüfe zeige setze suche finde
    baue mache lese schreibe erstelle berechne
    """
    )
)
_CAMEL = re.compile(r"(?<=[a-zäöüß0-9])(?=[A-ZÄÖÜ])")


class ToolError(RuntimeError):
    """A required measuring tool could not be executed."""


@dataclass(frozen=True)
class Finding:
    """One concrete violation behind a metric count."""

    metric: str
    path: str
    line: int
    detail: str

    def to_dict(self) -> dict[str, object]:
        """Serialize for the machine-readable report."""
        return {"metric": self.metric, "path": self.path, "line": self.line, "detail": self.detail}


@dataclass
class PackageMeasurement:
    """Counts and findings of one package."""

    name: str
    kind: str
    metrics: dict[str, int] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    def add(self, finding: Finding) -> None:
        """Record a finding and increment its metric."""
        self.findings.append(finding)
        self.metrics[finding.metric] = self.metrics.get(finding.metric, 0) + 1


def python_files(source: Path) -> list[Path]:
    """Return all measured Python modules below a source directory."""
    skipped = {"__pycache__", ".mypy_cache", ".ruff_cache"}
    return sorted(path for path in source.rglob("*.py") if not skipped.intersection(path.parts))


def name_tokens(name: str) -> list[str]:
    """Split snake_case and CamelCase names into lower-case tokens."""
    tokens: list[str] = []
    for part in name.strip("_").split("_"):
        tokens.extend(token.lower() for token in _CAMEL.split(part) if token)
    return tokens


def is_non_english(name: str) -> bool:
    """Heuristically detect German def/class names (umlauts or German stems)."""
    if not name.isascii():
        return True
    for token in name_tokens(name):
        if token in GERMAN_TOKENS or token.startswith(GERMAN_STEMS):
            return True
    return False


def _is_any(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "Any"
    return isinstance(node, ast.Attribute) and node.attr == "Any"


def _ast_findings(tree: ast.Module, relative: str) -> Iterator[Finding]:
    for node in ast.walk(tree):
        if _is_any(node):
            yield Finding("any_usages", relative, getattr(node, "lineno", 0), "typing.Any")
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if not isinstance(node, ast.ClassDef):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > MAX_FUNCTION_LINES:
                detail = f"{node.name}: {length} > {MAX_FUNCTION_LINES} lines"
                yield Finding("functions_over_60_lines", relative, node.lineno, detail)
        dunder = node.name.startswith("__") and node.name.endswith("__")
        if not dunder and is_non_english(node.name):
            yield Finding("non_english_identifiers", relative, node.lineno, node.name)


def measure_source_files(source: Path, root: Path, measurement: PackageMeasurement) -> None:
    """Add all AST- and size-based findings of a source tree."""
    for path in python_files(source):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        lines = len(text.splitlines())
        if lines > MAX_MODULE_LINES:
            detail = f"{lines} > {MAX_MODULE_LINES} lines"
            measurement.add(Finding("modules_over_400_lines", relative, 1, detail))
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as error:
            raise ToolError(f"Cannot parse {relative}: {error.msg}") from error
        for finding in _ast_findings(tree, relative):
            measurement.add(finding)


@cache
def _tool_command(module: str) -> tuple[str, ...]:
    """Prefer the tool of the running interpreter, fall back to PATH."""
    probe = subprocess.run(  # nosec B603
        [sys.executable, "-m", module, "--version"], capture_output=True, text=True, check=False
    )
    if probe.returncode == 0:
        return (sys.executable, "-m", module)
    executable = shutil.which(module)
    if executable is None:
        raise ToolError(f"{module} is required for the code-quality gate but not installed")
    return (executable,)


def tool_command(module: str) -> list[str]:
    """Return the command prefix of a measuring tool."""
    return list(_tool_command(module))


def tool_version(module: str) -> str:
    """Return the version string of a measuring tool."""
    process = subprocess.run(  # nosec B603
        [*tool_command(module), "--version"], capture_output=True, text=True, check=False
    )
    match = re.search(r"\d+\.\d+(?:\.\d+)?", process.stdout)
    return match.group(0) if match else "unknown"


def complexity_findings(sources: Iterable[Path], root: Path) -> list[Finding]:
    """Run ruff C901 (McCabe > 10) isolated from project config and noqa comments."""
    targets = [str(path) for path in sources]
    if not targets:
        return []
    command = [
        *tool_command("ruff"),
        "check",
        "--isolated",
        "--ignore-noqa",
        "--exit-zero",
        "--select",
        "C901",
        "--config",
        f"lint.mccabe.max-complexity = {MAX_COMPLEXITY}",
        "--target-version",
        "py311",
        "--output-format",
        "json",
        *targets,
    ]
    process = subprocess.run(  # nosec B603
        command, capture_output=True, text=True, check=False
    )
    if process.returncode != 0:
        raise ToolError(f"ruff failed: {process.stderr.strip()[:500]}")
    findings = []
    for row in json.loads(process.stdout or "[]"):
        path = Path(row["filename"]).resolve().relative_to(root).as_posix()
        line = int(row["location"]["row"])
        findings.append(Finding("complexity_over_10", path, line, str(row["message"])))
    return findings


_MYPY_ERROR = re.compile(r"^(?P<path>[^:\n]+):(?P<line>\d+):(?:\d+:)? error: (?P<msg>.*)$")


def mypy_findings(source: Path, root: Path, search_path: list[Path]) -> list[Finding]:
    """Run ``mypy --strict`` deterministically: no site-packages, no project config."""
    modules = sorted(child for child in source.iterdir() if (child / "__init__.py").is_file())
    if not modules:
        return []
    environment = dict(os.environ)
    environment["MYPYPATH"] = os.pathsep.join(str(path) for path in search_path)
    with tempfile.TemporaryDirectory(prefix="auditcore-codegate-mypy-") as cache:
        command = [
            *tool_command("mypy"),
            "--strict",
            "--config-file",
            "",
            "--no-site-packages",
            "--ignore-missing-imports",
            "--follow-imports",
            "silent",
            "--python-version",
            "3.11",
            "--no-pretty",
            "--no-error-summary",
            "--show-absolute-path",
            "--cache-dir",
            cache,
            *(str(module) for module in modules),
        ]
        process = subprocess.run(  # nosec B603
            command, capture_output=True, text=True, check=False, env=environment, cwd=root
        )
    if process.returncode not in (0, 1):
        raise ToolError(f"mypy failed: {(process.stderr or process.stdout).strip()[:500]}")
    findings = []
    for line in process.stdout.splitlines():
        match = _MYPY_ERROR.match(line)
        if match:
            path = Path(match["path"]).resolve()
            relative = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
            findings.append(
                Finding("mypy_strict_errors", relative, int(match["line"]), match["msg"])
            )
    return findings
