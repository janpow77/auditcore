"""Compact, deduplicated findings report – written for LLM input.

Only new findings (baseline-filtered) are listed, grouped by file, with exact
locations and one line each; autofixable findings are summarised separately
because a fixer, not a model, handles them. The report states its own size in
estimated tokens so callers can enforce a budget.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from .befunde import Finding

CHARS_PER_TOKEN = 4


def findings_from_documents(documents: Iterable[dict[str, object]]) -> list[Finding]:
    findings = []
    for document in documents:
        items = document.get("befunde", [])
        for item in items if isinstance(items, list) else []:
            if isinstance(item, dict):
                findings.append(
                    Finding(
                        tool=str(item.get("werkzeug", "")),
                        rule=str(item.get("regel", "")),
                        path=str(item.get("datei", "")),
                        line=int(str(item.get("zeile", 0))),
                        column=int(str(item.get("spalte", 0))),
                        message=str(item.get("meldung", "")),
                        severity=str(item.get("schwere", "fehler")),
                        fixable=bool(item.get("automatisch_behebbar")),
                        fingerprint=str(item.get("fingerabdruck", "")),
                    )
                )
    return findings


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def render(findings: list[Finding], limit: int = 200, token_budget: int = 0) -> str:
    """Markdown; stops early when the token budget would be exceeded."""
    fixable = [f for f in findings if f.fixable]
    manual = [f for f in findings if not f.fixable]
    counts = Counter(f.tool for f in manual)
    lines = [
        f"# Befunde ({len(manual)} zu bearbeiten, {len(fixable)} automatisch behebbar)",
        "",
        "Werkzeuge: " + (", ".join(f"{tool} {count}" for tool, count in counts.most_common()) or "keine"),
    ]
    if fixable:
        lines.append(
            f"Automatisch behebbar ({len(fixable)}): zuerst `auditcore-runner lokal <profil> --beheben` ausführen."
        )
    current_file = ""
    shown = 0
    for finding in sorted(manual, key=lambda f: (f.path, f.line))[:limit]:
        if finding.path != current_file:
            current_file = finding.path
            lines += ["", f"## {current_file}"]
        lines.append(
            f"- {finding.line}:{finding.column} {finding.tool}/{finding.rule} [{finding.severity}] {finding.message}"
        )
        shown += 1
        if token_budget and estimate_tokens("\n".join(lines)) > token_budget:
            lines.append(f"… gekürzt wegen Token-Budget ({token_budget})")
            break
    if len(manual) > shown:
        lines.append(f"\n{len(manual) - shown} weitere Befunde nicht aufgeführt.")
    text = "\n".join(lines) + "\n"
    return text + f"\n<!-- geschätzte Tokens: {estimate_tokens(text)} -->\n"
