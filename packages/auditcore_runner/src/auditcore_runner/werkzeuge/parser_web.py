"""Parsers for web, GUI and documentation tools (stylelint, markdownlint, jscpd, knip, tsc, size-limit, Lighthouse CI)."""

from __future__ import annotations

from .befunde import Finding
from .parser_erweitert import TSC, _dict, _int, _json, _list, _objects

KNIP_RULES = {
    "files": "unbenutzte-datei",
    "dependencies": "unbenutzte-abhaengigkeit",
    "devDependencies": "unbenutzte-entwicklungsabhaengigkeit",
    "optionalPeerDependencies": "unbenutzte-peer-abhaengigkeit",
    "unlisted": "nicht-deklarierte-abhaengigkeit",
    "unresolved": "unaufgeloester-import",
    "binaries": "unbekanntes-programm",
    "exports": "unbenutzter-export",
    "types": "unbenutzter-typ",
    "enumMembers": "unbenutztes-enum-mitglied",
    "namespaceMembers": "unbenutztes-namespace-mitglied",
    "duplicates": "doppelter-export",
}


def stylelint(text: str) -> list[Finding]:
    """``stylelint -f json``."""
    findings = []
    for file in _objects(_json(text)):
        for warning in _objects(file.get("warnings")):
            findings.append(
                Finding(
                    tool="stylelint",
                    rule=str(warning.get("rule", "stylelint")),
                    path=str(file.get("source", "")),
                    line=_int(warning.get("line")),
                    column=_int(warning.get("column")),
                    message=str(warning.get("text", "")),
                    severity="fehler" if warning.get("severity") == "error" else "warnung",
                )
            )
    return findings


def markdownlint(text: str) -> list[Finding]:
    """``markdownlint --json`` (markdownlint-cli)."""
    findings = []
    for item in _objects(_json(text)):
        names = [str(n) for n in _list(item.get("ruleNames"))]
        detail = item.get("errorDetail")
        message = str(item.get("ruleDescription", "")) + (f" ({detail})" if detail else "")
        findings.append(
            Finding(
                tool="markdownlint",
                rule=names[0] if names else "markdownlint",
                path=str(item.get("fileName", "")),
                line=_int(item.get("lineNumber")),
                message=message,
                severity="warnung",
                fixable=item.get("fixInfo") is not None,
            )
        )
    return findings


def jscpd(text: str) -> list[Finding]:
    """jscpd's ``jscpd-report.json``: each duplicate is reported at its first occurrence."""
    findings = []
    for item in _objects(_dict(_json(text)).get("duplicates")):
        first, second = _dict(item.get("firstFile")), _dict(item.get("secondFile"))
        findings.append(
            Finding(
                tool="jscpd",
                rule=f"duplikat-{item.get('format', 'code')}",
                path=str(first.get("name", "")),
                line=_int(first.get("start")),
                message=(
                    f"{_int(item.get('lines'))} Zeilen identisch mit {second.get('name', '')}:"
                    f"{_int(second.get('start'))}–{_int(second.get('end'))}"
                ),
                severity="warnung",
            )
        )
    return findings


def _knip_entries(issue: dict[str, object]) -> list[tuple[str, str, int, int]]:
    """(rule, name, line, column) for every entry of one knip issue record."""
    entries = []
    for category, rule in KNIP_RULES.items():
        for entry in _objects(issue.get(category)):
            entries.append((rule, str(entry.get("name", "")), _int(entry.get("line")), _int(entry.get("col"))))
    return entries


def knip(text: str) -> list[Finding]:
    """``knip --reporter json``: unused files, dependencies, exports and types."""
    findings = []
    for issue in _objects(_dict(_json(text)).get("issues")):
        path = str(issue.get("file", ""))
        for rule, name, line, column in _knip_entries(issue):
            findings.append(
                Finding(
                    tool="knip",
                    rule=rule,
                    path=path,
                    line=line,
                    column=column,
                    message=name if rule != "unbenutzte-datei" else "Datei wird nirgends verwendet",
                    severity="warnung",
                )
            )
    return findings


def tsc(text: str) -> list[Finding]:
    """TypeScript compiler (``tsc --noEmit --pretty false``)."""
    findings = []
    for line in text.splitlines():
        match = TSC.match(line.strip())
        if match:
            findings.append(
                Finding(
                    tool="tsc",
                    rule=match["code"],
                    path=match["path"],
                    line=int(match["line"]),
                    column=int(match["col"]),
                    message=match["message"],
                    severity="fehler" if match["level"] == "error" else "warnung",
                )
            )
    return findings


def size_limit(text: str) -> list[Finding]:
    """``size-limit --json``: every entry above its limit."""
    return [
        Finding(
            tool="size-limit",
            rule="groessengrenze",
            path="package.json",
            line=0,
            message=f"{item.get('name', '')}: {_int(item.get('size'))} B über Grenze {_int(item.get('sizeLimit'))} B",
            severity="fehler",
        )
        for item in _objects(_json(text))
        if item.get("passed") is False
    ]


def lighthouse(text: str) -> list[Finding]:
    """Lighthouse CI ``.lighthouseci/assertion-results.json``: failed assertions."""
    return [
        Finding(
            tool="lighthouse",
            rule=str(item.get("auditId") or item.get("name", "lighthouse")),
            path=str(item.get("url", "")),
            line=0,
            message=(
                f"{item.get('name', '')}: {item.get('actual', '?')} "
                f"{item.get('operator', '')} {item.get('expected', '?')}".strip()
            ),
            severity="fehler" if item.get("level") == "error" else "warnung",
        )
        for item in _objects(_json(text))
        if item.get("passed") is False
    ]


def none(text: str) -> list[Finding]:
    """Tools that produce an artefact (e.g. an SBOM) but no findings."""
    return []
