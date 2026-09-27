from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from auditcore_runner import measure

RUNS = [
    {
        "workflowName": "ci",
        "status": "completed",
        "conclusion": "success",
        "startedAt": "2026-09-20T10:00:00Z",
        "updatedAt": "2026-09-20T10:04:00Z",
    },
    {
        "workflowName": "ci",
        "status": "completed",
        "conclusion": "failure",
        "startedAt": "2026-09-21T10:00:00Z",
        "updatedAt": "2026-09-21T10:10:00Z",
    },
    {
        "workflowName": "ci",
        "status": "completed",
        "conclusion": "cancelled",
        "startedAt": "2026-09-22T10:00:00Z",
        "updatedAt": "2026-09-22T11:00:00Z",
    },
]


def test_workflow_stats() -> None:
    [stats] = measure.workflow_stats(RUNS)
    assert stats.runs == 2 and stats.median_minutes == 7.0 and stats.p90_minutes == 10.0 and stats.failed_share == 0.5


def test_claude_and_codex_usage(tmp_path: Path) -> None:
    project = tmp_path / "claude" / "-home-x-repo"
    project.mkdir(parents=True)
    line = {
        "timestamp": "2026-09-26T10:00:00Z",
        "cwd": "/tmp/repo",
        "message": {"usage": {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 1000}},
    }
    (project / "s.jsonl").write_text(json.dumps(line) + "\nkaputt\n", encoding="utf-8")
    usage = measure.claude_usage(tmp_path / "claude", datetime(2026, 9, 1, tzinfo=UTC))
    assert usage["repo"]["output_tokens"] == 5 and usage["repo"]["antworten"] == 1
    codex = tmp_path / "codex" / "2026" / "09"
    codex.mkdir(parents=True)
    events = [
        {"type": "session_meta", "payload": {"cwd": "/tmp/projekt"}},
        {
            "type": "event_msg",
            "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 50, "output_tokens": 7}}},
        },
    ]
    session = codex / "rollout-1.jsonl"
    session.write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    os.utime(session, (datetime(2026, 9, 26, tzinfo=UTC).timestamp(),) * 2)
    result = measure.codex_usage(tmp_path / "codex", datetime(2026, 9, 1, tzinfo=UTC))
    assert result["projekt"]["input_tokens"] == 50 and result["projekt"]["sitzungen"] == 1
    text = measure.render_markdown("host", 14, measure.workflow_stats(RUNS), usage, result)
    assert "| ci | 2 | 7.0 | 10.0 | 50% |" in text and "| projekt | 1 |" in text


def test_otel_usage_groups_by_task_type(tmp_path: Path) -> None:
    point = {"asInt": "1200", "attributes": [{"key": "type", "value": {"stringValue": "output"}}]}
    cost = {"asDouble": 0.25, "attributes": []}
    document = {
        "resourceMetrics": [
            {
                "resource": {"attributes": [{"key": "task_type", "value": {"stringValue": "docstrings"}}]},
                "scopeMetrics": [
                    {
                        "metrics": [
                            {"name": "claude_code.token.usage", "sum": {"dataPoints": [point]}},
                            {"name": "claude_code.cost.usage", "sum": {"dataPoints": [cost]}},
                        ]
                    }
                ],
            }
        ]
    }
    path = tmp_path / "otel.jsonl"
    path.write_text(json.dumps(document) + "\n", encoding="utf-8")
    usage = measure.otel_usage(path)
    assert usage["docstrings"]["token_output"] == 1200 and usage["docstrings"]["kosten_mikrodollar"] == 250000
