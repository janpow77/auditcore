"""CLI: catalogue validation and offline replay with exported records and counts."""

from __future__ import annotations

import json
from pathlib import Path

from auditcore_harvest.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_catalog_command(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["catalog"]) == 0
    assert json.loads(capsys.readouterr().out)["sources"] == 62


def test_catalog_command_rejects_invalid_file(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema": "x"}))
    assert main(["catalog", "--file", str(bad)]) == 2


def test_replay_exports_exactly_the_harvested_records(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"url": "https://feed.example.invalid/rss"}))
    output = tmp_path / "records.jsonl"
    code = main(
        [
            "replay",
            "auditcore_harvest.reference:_feed_example",
            "--fixture",
            str(FIXTURES / "example_feed.json"),
            "--config",
            str(config),
            "--output",
            str(output),
        ]
    )
    result = json.loads(capsys.readouterr().out)
    lines = [json.loads(line) for line in output.read_text().splitlines()]
    assert code == 0 and result["records_delivered"] == len(lines) == 2
    assert {r["provenance"]["profile_version"] for r in lines} == {"2026.09.1"}
    assert all(r["content_hash"] and r["record_id"] for r in lines)


def test_replay_rejects_bad_adapter_spec(tmp_path: Path) -> None:
    assert main(["replay", "kein-modul", "--fixture", "x", "--config", "y"]) == 2
