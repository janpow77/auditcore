"""Measure the size and escape-hatch metrics of one TypeScript/Vue package.

ESLint itself enforces ``no-explicit-any`` and ``complexity`` once the shared
configuration exists; this module measures what must never grow meanwhile:
oversized files, file-wide ``eslint-disable`` comments, unjustified line-wise
disables and explicit ``any`` without a justified line-wise exception.
"""

from __future__ import annotations

import re
from pathlib import Path

from auditcore.tools.quality.codegate_python import Finding, PackageMeasurement

MAX_SCRIPT_LINES = 400
MAX_VUE_LINES = 250
JS_METRICS = (
    "files_over_400_lines",
    "vue_sfc_over_250_lines",
    "eslint_file_disables",
    "eslint_unjustified_line_disables",
    "explicit_any",
)
SCRIPT_SUFFIXES = frozenset({".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"})
SKIPPED_DIRECTORIES = frozenset({"node_modules", "dist", "build", "coverage", ".vite", ".turbo"})
#: Additional build outputs such as ``dist-wc`` or ``dist-standalone`` (bpmn-vue).
SKIPPED_DIRECTORY_PREFIX = "dist-"
_FILE_DISABLE = re.compile(r"(?:/\*|<!--)\s*eslint-disable(?![-\w])")
_LINE_DISABLE = re.compile(r"eslint-disable-(?:next-)?line\b(?P<rest>[^\n]*)")
_EXPLICIT_ANY = re.compile(r"(?::\s*any|\bas\s+any|<any>|\bany\s*\[\])(?![\w$])")


def source_files(package: Path) -> list[Path]:
    """Return measured script and SFC files, excluding generated output."""
    files = []
    for path in sorted(package.rglob("*")):
        relative_parts = path.relative_to(package).parts
        if _generated(relative_parts[:-1]) or not path.is_file():
            continue
        if path.name.endswith(".d.ts"):
            continue
        if path.suffix in SCRIPT_SUFFIXES or path.suffix == ".vue":
            files.append(path)
    return files


def _generated(directories: tuple[str, ...]) -> bool:
    """True for files below a build-output or dependency directory."""
    return any(
        part in SKIPPED_DIRECTORIES or part.startswith(SKIPPED_DIRECTORY_PREFIX)
        for part in directories
    )


def _justified(rest: str) -> bool:
    """A line-wise disable needs ``-- reason`` after the rule list."""
    reason = rest.split("--", 1)[1] if "--" in rest else ""
    return bool(reason.strip().rstrip("*/").strip())


def _allows_any(line: str) -> bool:
    match = _LINE_DISABLE.search(line)
    return bool(match and "no-explicit-any" in match["rest"] and _justified(match["rest"]))


def _size_finding(path: Path, relative: str, line_count: int) -> Finding | None:
    if path.suffix == ".vue" and line_count > MAX_VUE_LINES:
        detail = f"{line_count} > {MAX_VUE_LINES} lines"
        return Finding("vue_sfc_over_250_lines", relative, 1, detail)
    if path.suffix != ".vue" and line_count > MAX_SCRIPT_LINES:
        return Finding("files_over_400_lines", relative, 1, f"{line_count} > {MAX_SCRIPT_LINES}")
    return None


def _line_findings(lines: list[str], relative: str) -> list[Finding]:
    findings = []
    previous = ""
    for number, line in enumerate(lines, start=1):
        if _FILE_DISABLE.search(line):
            findings.append(Finding("eslint_file_disables", relative, number, line.strip()))
        disable = _LINE_DISABLE.search(line)
        if disable and not _justified(disable["rest"]):
            detail = line.strip()
            findings.append(Finding("eslint_unjustified_line_disables", relative, number, detail))
        if _EXPLICIT_ANY.search(line) and not (_allows_any(line) or _allows_any(previous)):
            findings.append(Finding("explicit_any", relative, number, line.strip()))
        previous = line
    return findings


def measure_js_package(package: Path, root: Path) -> PackageMeasurement:
    """Measure one package below ``packages-js``."""
    measurement = PackageMeasurement(name=f"js:{package.name}", kind="js")
    measurement.metrics = dict.fromkeys(JS_METRICS, 0)
    for path in source_files(package):
        relative = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        size = _size_finding(path, relative, len(lines))
        if size is not None:
            measurement.add(size)
        for finding in _line_findings(lines, relative):
            measurement.add(finding)
    return measurement
