"""Parsers: raw tool output → unified findings. Pure functions over text."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ElementTree  # noqa: S405 - parses local tool output only
from collections.abc import Callable
from typing import cast

from . import parser_erweitert as _erweitert
from . import parser_web as _web
from .befunde import Finding, from_sarif

Parser = Callable[[str], list[Finding]]
MAX_XML_BYTES = 50 * 1024 * 1024
MYPY_LINE = re.compile(
    r"^(?P<path>[^:\n]+):(?P<line>\d+):(?:(?P<col>\d+):)? (?P<level>error|warning|note): "
    r"(?P<message>.*?)(?:\s+\[(?P<code>[\w-]+)\])?$"
)


def _objects(value: object) -> list[dict[str, object]]:
    return [cast(dict[str, object], v) for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def _int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _loads(text: str) -> object:
    stripped = text.strip()
    return json.loads(stripped) if stripped else []


def ruff(text: str) -> list[Finding]:
    """``ruff check --output-format=json``."""
    findings = []
    for item in _objects(_loads(text)):
        location = cast(dict[str, object], item.get("location") or {})
        findings.append(
            Finding(
                tool="ruff",
                rule=str(item.get("code") or "syntax"),
                path=str(item.get("filename", "")),
                line=_int(location.get("row")),
                column=_int(location.get("column")),
                message=str(item.get("message", "")),
                severity="fehler",
                fixable=bool(item.get("fix")),
            )
        )
    return findings


def mypy(text: str) -> list[Finding]:
    """mypy's default text output (``path:line:col: error: message [code]``)."""
    findings = []
    for line in text.splitlines():
        match = MYPY_LINE.match(line.strip())
        if not match or match["level"] == "note":
            continue
        findings.append(
            Finding(
                tool="mypy",
                rule=match["code"] or "mypy",
                path=match["path"],
                line=int(match["line"]),
                column=int(match["col"] or 0),
                message=match["message"],
                severity="fehler" if match["level"] == "error" else "warnung",
            )
        )
    return findings


def _junit_case(case: ElementTree.Element, tool: str = "pytest") -> Finding | None:
    problem = case.find("failure")
    if problem is None:
        problem = case.find("error")
    if problem is None:
        return None
    file = case.get("file") or case.get("classname", "").replace(".", "/") + ".py"
    message = (problem.get("message") or problem.text or "").strip().splitlines()
    return Finding(
        tool=tool,
        rule=problem.tag,
        path=file,
        line=int(case.get("line") or 0),
        message=f"{case.get('name', '')}: {message[0] if message else problem.tag}",
        severity="fehler",
    )


def junit_report(tool: str) -> Parser:
    """JUnit XML (pytest, vitest, Playwright): failed and erroring test cases."""

    def parse(text: str) -> list[Finding]:
        if not text.strip():
            return []
        if len(text) > MAX_XML_BYTES or "<!DOCTYPE" in text or "<!ENTITY" in text:
            raise ValueError("JUnit-XML abgelehnt (zu groß oder mit DOCTYPE/ENTITY)")
        # Without DOCTYPE/ENTITY declarations there is nothing to expand or resolve.
        root = ElementTree.fromstring(text)  # noqa: S314  # nosec B314
        return [f for f in (_junit_case(case, tool) for case in root.iter("testcase")) if f is not None]

    return parse


junit = junit_report("pytest")


def actionlint(text: str) -> list[Finding]:
    """``actionlint -format '{{json .}}'``."""
    return [
        Finding(
            tool="actionlint",
            rule=str(item.get("kind", "actionlint")),
            path=str(item.get("filepath", "")),
            line=_int(item.get("line")),
            column=_int(item.get("column")),
            message=str(item.get("message", "")),
            severity="fehler",
        )
        for item in _objects(_loads(text))
    ]


def gitleaks(text: str) -> list[Finding]:
    """``gitleaks detect --report-format json`` (secret value never copied)."""
    return [
        Finding(
            tool="gitleaks",
            rule=str(item.get("RuleID", "")),
            path=str(item.get("File", "")),
            line=_int(item.get("StartLine")),
            message=f"mögliches Geheimnis ({item.get('Description', 'unbekannt')})",
            severity="fehler",
        )
        for item in _objects(_loads(text))
    ]


def eslint(text: str) -> list[Finding]:
    """``eslint -f json``."""
    findings = []
    for file in _objects(_loads(text)):
        for message in _objects(file.get("messages")):
            findings.append(
                Finding(
                    tool="eslint",
                    rule=str(message.get("ruleId") or "parse"),
                    path=str(file.get("filePath", "")),
                    line=_int(message.get("line")),
                    column=_int(message.get("column")),
                    message=str(message.get("message", "")),
                    severity="fehler" if message.get("severity") == 2 else "warnung",
                    fixable="fix" in message,
                )
            )
    return findings


def codegate(text: str) -> list[Finding]:
    """``auditcore-codegate check --output`` report: every finding behind a failing verdict."""
    data = _loads(text)
    if not isinstance(data, dict):
        return []
    failing = {(v.get("package"), v.get("metric")) for v in _objects(data.get("verdicts")) if v.get("status") != "PASS"}
    packages = data.get("packages") if isinstance(data.get("packages"), dict) else {}
    findings = []
    for package, entry in cast(dict[str, object], packages).items():
        details = entry.get("findings") if isinstance(entry, dict) else []
        for item in _objects(details):
            if (package, item.get("metric")) in failing:
                findings.append(
                    Finding(
                        tool="codegate",
                        rule=str(item.get("metric", "")),
                        path=str(item.get("path", "")),
                        line=_int(item.get("line")),
                        message=str(item.get("detail", "")),
                        severity="fehler",
                    )
                )
    return findings


def sarif(text: str) -> list[Finding]:
    return from_sarif(_loads(text))


PARSERS: dict[str, Parser] = {
    "ruff-json": ruff,
    "mypy-text": mypy,
    "junit-xml": junit,
    "actionlint-json": actionlint,
    "gitleaks-json": gitleaks,
    "eslint-json": eslint,
    "codegate-json": codegate,
    "sarif": sarif,
}

PARSERS.update(
    {
        "pyrefly-json": _erweitert.pyrefly,
        "vulture-text": _erweitert.vulture,
        "deptry-json": _erweitert.deptry,
        "import-linter-text": _erweitert.import_linter,
        "codespell-text": _erweitert.codespell,
        "typos-json": _erweitert.typos,
        "mutmut-text": _erweitert.mutmut,
        "diff-cover-json": _erweitert.diff_cover,
        "ast-grep-json": _erweitert.ast_grep,
        "betterleaks-json": _erweitert.leak_report("betterleaks"),
        "lychee-json": _erweitert.lychee,
        "prettier-text": _erweitert.prettier,
        "stylelint-json": _web.stylelint,
        "markdownlint-json": _web.markdownlint,
        "jscpd-json": _web.jscpd,
        "knip-json": _web.knip,
        "tsc-text": _web.tsc,
        "size-limit-json": _web.size_limit,
        "lighthouse-json": _web.lighthouse,
        "keine": _web.none,
        "vitest-junit": junit_report("vitest"),
        "playwright-junit": junit_report("playwright"),
        "axe-junit": junit_report("axe"),
    }
)
