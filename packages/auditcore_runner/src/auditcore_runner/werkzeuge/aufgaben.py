"""Task package: the exact work left after autofix, for a headless agent run.

Each item carries file:line, rule, a short code excerpt and a fix hint – line-
precise feedback is what keeps model runs short. The package writes a file and
recommends a call (Claude Code or Codex) with a budget; it never runs a model.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from pathlib import Path

from .befunde import Finding

KINDS = ("claude", "codex", "lokal")


@dataclass(frozen=True)
class TaskItem:
    finding: Finding
    excerpt: str = ""
    hint: str = ""


@dataclass(frozen=True)
class Budget:
    max_usd: float = 1.0
    max_turns: int = 20
    allowed_tools: tuple[str, ...] = ("Read", "Edit", "Bash(git diff:*)")


@dataclass(frozen=True)
class TaskPackage:
    package_id: str
    task_type: str
    root: Path
    items: tuple[TaskItem, ...]
    budget: Budget = field(default_factory=Budget)


def excerpt(root: Path, finding: Finding, context: int = 2) -> str:
    path = root / finding.path
    if not path.is_file() or finding.line <= 0:
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(finding.line - 1 - context, 0)
    chosen = lines[start : finding.line + context]
    return "\n".join(f"{start + i + 1:>5} {text}" for i, text in enumerate(chosen))


def build(
    package_id: str, task_type: str, root: Path, findings: list[Finding], hints: dict[str, str] | None = None
) -> TaskPackage:
    """Items only for findings a fixer could not resolve."""
    items = tuple(
        TaskItem(f, excerpt(root, f), (hints or {}).get(f"{f.tool}/{f.rule}", "")) for f in findings if not f.fixable
    )
    return TaskPackage(package_id, task_type, root, items)


def render(package: TaskPackage) -> str:
    lines = [
        f"# Aufgabenpaket {package.package_id} ({package.task_type})",
        "",
        "Behebe genau die folgenden Befunde. Ändere nichts anderes; prüfe am Ende mit",
        "`auditcore-runner lokal pr`, dass sie verschwunden sind.",
    ]
    for number, item in enumerate(package.items, 1):
        finding = item.finding
        lines += ["", f"## {number}. {finding.path}:{finding.line} – {finding.tool}/{finding.rule}", finding.message]
        if item.hint:
            lines.append(f"Hinweis: {item.hint}")
        if item.excerpt:
            lines += ["```", item.excerpt, "```"]
    return "\n".join(lines) + "\n"


def command(package: TaskPackage, file: Path, kind: str = "claude") -> str:
    """Recommended headless call; OTEL attributes tag the run for ``messen``."""
    labels = f"OTEL_RESOURCE_ATTRIBUTES=task_type={package.task_type},paket_id={package.package_id}"
    if kind == "codex":
        return f'{labels} codex exec --json "$(cat {shlex.quote(str(file))})"'
    tools = ",".join(package.budget.allowed_tools)
    return (
        f"{labels} claude -p --bare --append-system-prompt-file {shlex.quote(str(file))} "
        f"--max-budget-usd {package.budget.max_usd:g} --max-turns {package.budget.max_turns} "
        f"--allowedTools {shlex.quote(tools)} --output-format json "
        f"{shlex.quote('Arbeite das Aufgabenpaket ab.')}"
    )
