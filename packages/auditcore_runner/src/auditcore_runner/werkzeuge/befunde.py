"""Unified findings: one shape for every tool, SARIF in and out, baseline filtering.

The fingerprint deliberately ignores the line number, so moving code does not
turn an old finding into a "new" one; it hashes tool, rule, file and the
message with digits normalised.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import cast

SEVERITIES = ("fehler", "warnung", "hinweis")
SARIF_LEVEL = {"fehler": "error", "warnung": "warning", "hinweis": "note"}
FROM_SARIF = {"error": "fehler", "warning": "warnung", "note": "hinweis", "none": "hinweis"}
DIGITS = re.compile(r"\d+")


@dataclass(frozen=True)
class Finding:
    tool: str
    rule: str
    path: str
    line: int
    message: str
    severity: str = "fehler"
    column: int = 0
    fixable: bool = False
    fingerprint: str = ""

    def with_fingerprint(self) -> Finding:
        return self if self.fingerprint else replace(self, fingerprint=fingerprint(self))

    def as_dict(self) -> dict[str, object]:
        return {
            "werkzeug": self.tool,
            "regel": self.rule,
            "datei": self.path,
            "zeile": self.line,
            "spalte": self.column,
            "schwere": self.severity,
            "meldung": self.message,
            "automatisch_behebbar": self.fixable,
            "fingerabdruck": self.fingerprint or fingerprint(self),
        }


def fingerprint(finding: Finding) -> str:
    normalised = DIGITS.sub("#", " ".join(finding.message.split()))
    key = "\x1f".join((finding.tool, finding.rule, finding.path, normalised))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def deduplicate(findings: Iterable[Finding]) -> list[Finding]:
    """Keep the first finding per (fingerprint, line); stable order by file and line."""
    seen: set[tuple[str, int]] = set()
    result: list[Finding] = []
    for finding in sorted((f.with_fingerprint() for f in findings), key=lambda f: (f.path, f.line, f.tool, f.rule)):
        key = (finding.fingerprint, finding.line)
        if key not in seen:
            seen.add(key)
            result.append(finding)
    return result


def load_baseline(path: Path) -> frozenset[str]:
    """Fingerprints accepted as known; a missing file means an empty baseline."""
    if not path.exists():
        return frozenset()
    data = json.loads(path.read_text(encoding="utf-8"))
    values = data.get("fingerabdruecke", []) if isinstance(data, dict) else []
    return frozenset(str(v) for v in values) if isinstance(values, list) else frozenset()


def save_baseline(path: Path, findings: Iterable[Finding]) -> None:
    prints = sorted({f.with_fingerprint().fingerprint for f in findings})
    document = {"schema": "auditcore-runner/befund-baseline/1", "fingerabdruecke": prints}
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def relative_to(findings: Iterable[Finding], roots: Iterable[str]) -> list[Finding]:
    """Repository-relative paths: strips ``file://`` and the checked roots (host path or ``/work``)."""
    prefixes = sorted({r.rstrip("/") + "/" for r in roots if r}, key=len, reverse=True)
    result = []
    for finding in findings:
        path = finding.path.removeprefix("file://")
        for prefix in prefixes:
            if path.startswith(prefix):
                path = path[len(prefix) :]
                break
        result.append(finding if path == finding.path else replace(finding, path=path))
    return result


def only_new(findings: Iterable[Finding], baseline: frozenset[str]) -> list[Finding]:
    return [f for f in (x.with_fingerprint() for x in findings) if f.fingerprint not in baseline]


def to_sarif(findings: Iterable[Finding]) -> dict[str, object]:
    """SARIF 2.1.0 with one run per tool."""
    by_tool: dict[str, list[Finding]] = {}
    for finding in findings:
        by_tool.setdefault(finding.tool, []).append(finding.with_fingerprint())
    runs: list[object] = []
    for tool, items in sorted(by_tool.items()):
        results = [
            {
                "ruleId": f.rule,
                "level": SARIF_LEVEL.get(f.severity, "warning"),
                "message": {"text": f.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": f.path},
                            "region": {"startLine": max(f.line, 1), "startColumn": max(f.column, 1)},
                        }
                    }
                ],
                "partialFingerprints": {"auditcoreRunner/v1": f.fingerprint},
            }
            for f in items
        ]
        runs.append({"tool": {"driver": {"name": tool}}, "results": results})
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0", "runs": runs}


def _dict(value: object) -> dict[str, object]:
    return cast(dict[str, object], value) if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _location(result: dict[str, object]) -> tuple[str, int, int]:
    locations = _list(result.get("locations"))
    physical = _dict(_dict(locations[0]).get("physicalLocation")) if locations else {}
    region = _dict(physical.get("region"))
    uri = str(_dict(physical.get("artifactLocation")).get("uri", ""))
    line, column = region.get("startLine", 0), region.get("startColumn", 0)
    return uri, line if isinstance(line, int) else 0, column if isinstance(column, int) else 0


def from_sarif(document: object, default_tool: str = "sarif") -> list[Finding]:
    """Findings from any SARIF 2.1.0 producer (semgrep, trivy, …)."""
    findings: list[Finding] = []
    for run in _list(_dict(document).get("runs")):
        tool = str(_dict(_dict(_dict(run).get("tool")).get("driver")).get("name", default_tool))
        for item in _list(_dict(run).get("results")):
            result = _dict(item)
            path, line, column = _location(result)
            findings.append(
                Finding(
                    tool=tool,
                    rule=str(result.get("ruleId", "")),
                    path=path,
                    line=line,
                    column=column,
                    message=str(_dict(result.get("message")).get("text", "")),
                    severity=FROM_SARIF.get(str(result.get("level", "warning")), "warnung"),
                )
            )
    return findings
