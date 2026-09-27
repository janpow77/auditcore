"""Repeatable baseline measurement: CI durations (via ``gh``) and LLM token usage.

Token usage is read from local agent logs – Claude Code (``~/.claude/projects``)
and Codex (``~/.codex/sessions``) – aggregated per working directory. Nothing
leaves the machine.
"""

from __future__ import annotations

import json
import statistics
import subprocess
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

RUN_FIELDS = "workflowName,status,conclusion,createdAt,updatedAt,startedAt"


@dataclass(frozen=True)
class WorkflowStats:
    name: str
    runs: int
    median_minutes: float
    p90_minutes: float
    failed_share: float


def _time(value: object) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) and value else None


def workflow_stats(runs: Iterable[dict[str, object]]) -> list[WorkflowStats]:
    """Median/p90 duration and failure share per workflow (skipped/cancelled excluded)."""
    durations: dict[str, list[tuple[float, bool]]] = defaultdict(list)
    for run in runs:
        start, end = _time(run.get("startedAt") or run.get("createdAt")), _time(run.get("updatedAt"))
        if (
            run.get("status") != "completed"
            or run.get("conclusion") in {"skipped", "cancelled"}
            or not start
            or not end
        ):
            continue
        durations[str(run.get("workflowName"))].append(
            ((end - start).total_seconds() / 60, run.get("conclusion") == "success")
        )
    stats = []
    for name, values in durations.items():
        minutes = sorted(m for m, _ in values)
        p90 = minutes[min(len(minutes) - 1, int(0.9 * len(minutes)))]
        failed = sum(1 for _, ok in values if not ok) / len(values)
        stats.append(WorkflowStats(name, len(values), statistics.median(minutes), p90, failed))
    return sorted(stats, key=lambda s: -s.runs)


def fetch_runs(repo: str, days: int, limit: int = 1000) -> list[dict[str, object]]:
    since = (datetime.now(UTC) - timedelta(days=days)).date().isoformat()
    result = subprocess.run(
        ["gh", "run", "list", "-R", repo, "-L", str(limit), "--created", f">={since}", "--json", RUN_FIELDS],
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )
    data = json.loads(result.stdout)
    return [cast(dict[str, object], x) for x in data if isinstance(x, dict)] if isinstance(data, list) else []


def _json_lines(path: Path) -> Iterator[dict[str, object]]:
    try:
        stream = path.open(encoding="utf-8")
    except OSError:
        return
    with stream:
        for line in stream:
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if isinstance(item, dict):
                yield cast(dict[str, object], item)


def claude_usage(root: Path, since: datetime) -> dict[str, Counter[str]]:
    """Tokens per working directory from Claude Code transcripts."""
    usage: dict[str, Counter[str]] = defaultdict(Counter)
    for path in root.glob("*/*.jsonl"):
        for item in _json_lines(path):
            message = item.get("message")
            stamp = _time(item.get("timestamp"))
            counts = message.get("usage") if isinstance(message, dict) else None
            if not isinstance(counts, dict) or not stamp or stamp < since:
                continue
            bucket = usage[Path(str(item.get("cwd") or path.parent.name)).name]
            for key in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"):
                value = counts.get(key)
                bucket[key] += value if isinstance(value, int) else 0
            bucket["antworten"] += 1
    return usage


def _ints(value: object) -> Counter[str]:
    return Counter({k: v for k, v in value.items() if isinstance(v, int)}) if isinstance(value, dict) else Counter()


def _codex_total(path: Path) -> tuple[str, Counter[str]]:
    """Last cumulative ``token_count`` of a session, or the sum of ``turn.completed`` usages."""
    cwd, total, turns = "", Counter[str](), Counter[str]()
    for item in _json_lines(path):
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else item
        if not isinstance(payload, dict):
            continue
        cwd = str(payload.get("cwd") or cwd)
        info = payload.get("info")
        if payload.get("type") == "token_count" and isinstance(info, dict):
            total = _ints(info.get("total_token_usage"))
        if payload.get("type") == "turn.completed":
            turns.update(_ints(payload.get("usage")))
    return Path(cwd).name or "unbekannt", total or turns


def codex_usage(root: Path, since: datetime) -> dict[str, Counter[str]]:
    """Tokens per working directory from Codex session logs (last total per session)."""
    usage: dict[str, Counter[str]] = defaultdict(Counter)
    for path in root.glob("**/*.jsonl"):
        if datetime.fromtimestamp(path.stat().st_mtime, UTC) < since:
            continue
        name, total = _codex_total(path)
        usage[name].update(total)
        usage[name]["sitzungen"] += 1
    return usage


def _attributes(items: object) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in items if isinstance(items, list) else []:
        if isinstance(item, dict):
            value = item.get("value")
            text = next(iter(value.values()), "") if isinstance(value, dict) and value else ""
            result[str(item.get("key"))] = str(text)
    return result


def _points(metric: dict[str, object]) -> list[dict[str, object]]:
    body = metric.get("sum") or metric.get("gauge") or {}
    points = body.get("dataPoints", []) if isinstance(body, dict) else []
    return [cast(dict[str, object], p) for p in points if isinstance(p, dict)] if isinstance(points, list) else []


def _objects(value: object) -> list[dict[str, object]]:
    return [cast(dict[str, object], v) for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def _otel_metrics(document: dict[str, object]) -> Iterator[tuple[dict[str, str], dict[str, object]]]:
    for resource_metrics in _objects(document.get("resourceMetrics")):
        resource_part = resource_metrics.get("resource")
        resource = _attributes(resource_part.get("attributes") if isinstance(resource_part, dict) else None)
        for scope in _objects(resource_metrics.get("scopeMetrics")):
            for metric in _objects(scope.get("metrics")):
                yield resource, metric


def otel_usage(path: Path, group_key: str = "task_type") -> dict[str, Counter[str]]:
    """Claude Code OTel metrics (OTLP/JSON lines, file exporter): tokens and cost per label.

    Groups by the resource or point attribute ``group_key`` (set via
    ``OTEL_RESOURCE_ATTRIBUTES=task_type=…,paket_id=…``), falling back to ``query_source``.
    """
    usage: dict[str, Counter[str]] = defaultdict(Counter)
    for document in _json_lines(path):
        for resource, metric in _otel_metrics(document):
            name = metric.get("name")
            if name not in {"claude_code.token.usage", "claude_code.cost.usage"}:
                continue
            for point in _points(metric):
                attributes = {**resource, **_attributes(point.get("attributes"))}
                group = attributes.get(group_key) or attributes.get("query_source") or "ohne Etikett"
                value = point.get("asInt", point.get("asDouble", 0))
                amount = (
                    float(value)
                    if isinstance(value, (int, float, str)) and str(value).replace(".", "", 1).isdigit()
                    else 0.0
                )
                key = (
                    "kosten_mikrodollar"
                    if name == "claude_code.cost.usage"
                    else f"token_{attributes.get('type', 'gesamt')}"
                )
                usage[group][key] += int(amount * 1_000_000) if key == "kosten_mikrodollar" else int(amount)
    return usage


def _millions(value: int) -> str:
    return f"{value / 1_000_000:.1f} M"


def render_markdown(
    host: str, days: int, stats: list[WorkflowStats], claude: dict[str, Counter[str]], codex: dict[str, Counter[str]]
) -> str:
    lines = [
        f"## Messung {host} ({days} Tage, Stand {datetime.now().date().isoformat()})",
        "",
        "| Workflow | Läufe | Median min | p90 min | Anteil rot |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {s.name} | {s.runs} | {s.median_minutes:.1f} | {s.p90_minutes:.1f} | {s.failed_share:.0%} |" for s in stats
    ]
    lines += [
        "",
        "| Claude: Verzeichnis | Antworten | Ausgabe | Cache gelesen | Cache geschrieben |",
        "|---|---|---|---|---|",
    ]
    ranked = sorted(claude.items(), key=lambda kv: -kv[1]["cache_read_input_tokens"])[:12]
    lines += [
        f"| {name} | {c['antworten']} | {_millions(c['output_tokens'])} | {_millions(c['cache_read_input_tokens'])} | "
        f"{_millions(c['cache_creation_input_tokens'])} |"
        for name, c in ranked
    ]
    if codex:
        lines += ["", "| Codex: Verzeichnis | Sitzungen | Eingabe | davon Cache | Ausgabe |", "|---|---|---|---|---|"]
        lines += [
            f"| {name} | {c['sitzungen']} | {_millions(c['input_tokens'])} | {_millions(c['cached_input_tokens'])} | "
            f"{_millions(c['output_tokens'])} |"
            for name, c in sorted(codex.items(), key=lambda kv: -kv[1]["input_tokens"])[:12]
        ]
    return "\n".join(lines) + "\n"
