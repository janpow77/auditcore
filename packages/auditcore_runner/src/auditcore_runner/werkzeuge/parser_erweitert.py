"""Parsers for the full catalog (PR 2): raw tool output → unified findings.

Pure functions over the tool's own report format. SARIF producers (Opengrep,
osv-scanner, grype, trivy, zizmor) use the generic ``sarif`` parser.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import cast

from .befunde import Finding

Parser = Callable[[str], list[Finding]]

VULTURE = re.compile(r"^(?P<path>[^:\n]+):(?P<line>\d+): (?P<message>.+?) \((?P<confidence>\d+)% confidence\)$")
CODESPELL = re.compile(r"^(?P<path>[^:\n]+):(?P<line>\d+): (?P<wrong>\S+) ==> (?P<fix>.+)$")
TSC = re.compile(
    r"^(?P<path>.+?)\((?P<line>\d+),(?P<col>\d+)\): (?P<level>error|warning) (?P<code>TS\d+): (?P<message>.*)$"
)
IMPORT_EDGE = re.compile(r"^-\s+(?P<source>[\w.]+) -> (?P<target>[\w.]+) \(l\.(?P<line>\d+)\)")
MUTANT = re.compile(r"^\s*(?P<name>[\w.]+)__mutmut_(?P<number>\d+): (?P<status>survived|timeout|suspicious|no tests)$")
AST_GREP_LEVEL = {"error": "fehler", "warning": "warnung", "info": "hinweis", "hint": "hinweis"}


def _dict(value: object) -> dict[str, object]:
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


def _objects(value: object) -> list[dict[str, object]]:
    return [cast(dict[str, object], v) for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def _int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _json(text: str) -> object:
    stripped = text.strip()
    return json.loads(stripped) if stripped else None


def _json_lines(text: str) -> list[dict[str, object]]:
    rows: list[object] = [json.loads(line) for line in text.splitlines() if line.strip().startswith("{")]
    return _objects(rows)


def _module_path(module: str) -> str:
    return module.replace(".", "/") + ".py"


def pyrefly(text: str) -> list[Finding]:
    """``pyrefly check --output-format json``."""
    return [
        Finding(
            tool="pyrefly",
            rule=str(item.get("name", "pyrefly")),
            path=str(item.get("path", "")),
            line=_int(item.get("line")),
            column=_int(item.get("column")),
            message=str(item.get("concise_description") or item.get("description", "")),
            severity="fehler" if item.get("severity") == "error" else "warnung",
        )
        for item in _objects(_dict(_json(text)).get("errors"))
    ]


def vulture(text: str) -> list[Finding]:
    """vulture's text output; the rule is derived from the message (``unused-import`` …)."""
    findings = []
    for line in text.splitlines():
        match = VULTURE.match(line.strip())
        if match:
            words = match["message"].split()
            rule = "-".join(words[:2]) if len(words) > 1 else "vulture"
            findings.append(
                Finding(
                    tool="vulture",
                    rule=rule,
                    path=match["path"],
                    line=int(match["line"]),
                    message=f"{match['message']} ({match['confidence']} %)",
                    severity="warnung",
                )
            )
    return findings


def deptry(text: str) -> list[Finding]:
    """``deptry . --json-output <datei>``."""
    findings = []
    for item in _objects(_json(text)):
        error, location = _dict(item.get("error")), _dict(item.get("location"))
        findings.append(
            Finding(
                tool="deptry",
                rule=str(error.get("code", "deptry")),
                path=str(location.get("file", "")),
                line=_int(location.get("line")),
                column=_int(location.get("column")),
                message=str(error.get("message", "")),
                severity="fehler",
            )
        )
    return findings


def import_linter(text: str) -> list[Finding]:
    """``lint-imports``: every forbidden import edge of a broken contract."""
    findings, contract, lines = [], "", text.splitlines()
    for index, line in enumerate(lines):
        following = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if following and set(following) == {"-"} and line.strip() and not line.startswith("-"):
            contract = line.strip()
            continue
        match = IMPORT_EDGE.match(line.strip())
        if match:
            findings.append(
                Finding(
                    tool="import-linter",
                    rule="vertrag-verletzt",
                    path=_module_path(match["source"]),
                    line=int(match["line"]),
                    message=f"{contract}: {match['source']} importiert {match['target']}",
                    severity="fehler",
                )
            )
    return findings


def codespell(text: str) -> list[Finding]:
    """codespell's text output; fixable with ``codespell -w``."""
    findings = []
    for line in text.splitlines():
        match = CODESPELL.match(line.strip())
        if match:
            findings.append(
                Finding(
                    tool="codespell",
                    rule="schreibfehler",
                    path=match["path"],
                    line=int(match["line"]),
                    message=f"{match['wrong']} → {match['fix']}",
                    severity="hinweis",
                    fixable=True,
                )
            )
    return findings


def typos(text: str) -> list[Finding]:
    """``typos --format json`` (one JSON object per line)."""
    return [
        Finding(
            tool="typos",
            rule="schreibfehler",
            path=str(item.get("path", "")),
            line=_int(item.get("line_num")),
            column=_int(item.get("byte_offset")) + 1,
            message=f"{item.get('typo', '')} → {', '.join(str(c) for c in _list(item.get('corrections')))}",
            severity="hinweis",
            fixable=True,
        )
        for item in _json_lines(text)
        if item.get("type") == "typo"
    ]


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def mutmut(text: str) -> list[Finding]:
    """``mutmut results``: surviving (or undecided) mutants per function."""
    findings = []
    for line in text.splitlines():
        match = MUTANT.match(line)
        if match:
            module, _, function = match["name"].rpartition(".")
            findings.append(
                Finding(
                    tool="mutmut",
                    rule=match["status"].replace(" ", "-"),
                    path=_module_path(module),
                    line=0,
                    message=f"Mutante {match['number']} in {function.removeprefix('x_')}: {match['status']}",
                    severity="warnung",
                )
            )
    return findings


def diff_cover(text: str) -> list[Finding]:
    """``diff-cover --json-report``: changed lines without test coverage, one finding per file."""
    findings = []
    for path, raw in _dict(_dict(_json(text)).get("src_stats")).items():
        stats = _dict(raw)
        lines = [line for line in _list(stats.get("violation_lines")) if isinstance(line, int)]
        if lines:
            shown = ", ".join(str(n) for n in lines[:20]) + (" …" if len(lines) > 20 else "")
            findings.append(
                Finding(
                    tool="diff-cover",
                    rule="ungetestete-aenderung",
                    path=path,
                    line=lines[0],
                    message=(
                        f"geänderte Zeilen ohne Testabdeckung: {shown} "
                        f"({stats.get('percent_covered', '?')} % abgedeckt)"
                    ),
                    severity="warnung",
                )
            )
    return findings


def ast_grep(text: str) -> list[Finding]:
    """``ast-grep scan --json=stream`` (lines are 0-based there)."""
    findings = []
    for item in _json_lines(text):
        start = _dict(_dict(item.get("range")).get("start"))
        findings.append(
            Finding(
                tool="ast-grep",
                rule=str(item.get("ruleId", "ast-grep")),
                path=str(item.get("file", "")),
                line=_int(start.get("line")) + 1,
                column=_int(start.get("column")) + 1,
                message=str(item.get("message", "")),
                severity=AST_GREP_LEVEL.get(str(item.get("severity", "warning")), "warnung"),
                fixable=item.get("replacement") is not None,
            )
        )
    return findings


def leak_report(tool: str) -> Parser:
    """gitleaks-compatible JSON reports (gitleaks, betterleaks); secret values are never copied."""

    def parse(text: str) -> list[Finding]:
        return [
            Finding(
                tool=tool,
                rule=str(item.get("RuleID", "")),
                path=str(item.get("File", "")),
                line=_int(item.get("StartLine")),
                column=_int(item.get("StartColumn")),
                message=f"mögliches Geheimnis ({item.get('RuleID', 'unbekannt')})",
                severity="fehler",
            )
            for item in _objects(_json(text))
        ]

    return parse


def lychee(text: str) -> list[Finding]:
    """``lychee --format json``: broken links with their position."""
    findings = []
    for path, entries in _dict(_dict(_json(text)).get("error_map")).items():
        for entry in _objects(entries):
            span = _dict(entry.get("span"))
            status = _dict(entry.get("status"))
            findings.append(
                Finding(
                    tool="lychee",
                    rule="defekter-link",
                    path=path,
                    line=_int(span.get("line")),
                    column=_int(span.get("column")),
                    message=f"{entry.get('url', '')}: {status.get('text', 'Fehler')}",
                    severity="fehler",
                )
            )
    return findings


def prettier(text: str) -> list[Finding]:
    """``prettier --check``: one finding per unformatted file, fixable with ``--write``."""
    return [
        Finding(
            tool="prettier",
            rule="format",
            path=line.removeprefix("[warn] ").strip(),
            line=0,
            message="nicht nach Prettier formatiert",
            severity="hinweis",
            fixable=True,
        )
        for line in text.splitlines()
        if line.startswith("[warn] ") and "Code style issues" not in line
    ]
