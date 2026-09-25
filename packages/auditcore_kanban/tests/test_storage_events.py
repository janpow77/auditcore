from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from auditcore_kanban import (
    Board,
    Change,
    FileSystemBoardStore,
    InMemoryBoardStore,
    InMemoryEventLog,
    JsonLinesEventLog,
    KanbanError,
)


@pytest.mark.parametrize("kind", ["memory", "files"])
def test_store_versions(board: Board, tmp_path: Path, kind: str) -> None:
    store = InMemoryBoardStore() if kind == "memory" else FileSystemBoardStore(tmp_path)
    store.save(board, None)
    with pytest.raises(KanbanError, match="VERSION_CONFLICT"):
        store.save(board, None)
    store.save(replace(board, version=2), 1)
    with pytest.raises(KanbanError, match="VERSION_CONFLICT"):
        store.save(replace(board, version=3), 1)
    loaded = store.get("b1")
    assert loaded is not None and loaded.version == 2
    assert [b.id for b in store.list()] == ["b1"]
    assert store.delete("b1") and not store.delete("b1") and store.get("b1") is None
    with pytest.raises(KanbanError, match="VERSION_CONFLICT"):
        store.save(board, 4)


@pytest.mark.parametrize("board_id", ["../x", "a/b", ".hidden", "", "a" * 200])
def test_file_store_rejects_unsafe_ids(tmp_path: Path, board_id: str) -> None:
    with pytest.raises(KanbanError):
        FileSystemBoardStore(tmp_path).get(board_id)


def test_file_store_leaves_no_temp_files(board: Board, tmp_path: Path) -> None:
    FileSystemBoardStore(tmp_path).save(board, None)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["b1.json"]


def test_event_logs(tmp_path: Path) -> None:
    log = InMemoryEventLog()
    first = log.record("b1", 2, "u1", "t", [Change("card.created", "c1", {"x": 1}),
                                             Change("column.rebalanced")])
    log.record("b2", 1, "u1", "t", [Change("board.created")])
    assert [e.seq for e in first] == [1, 2]
    assert [e.seq for e in log.since("b1", 1)] == [2]
    path = tmp_path / "events.jsonl"
    persisted = JsonLinesEventLog(path)
    persisted.record("b1", 2, "u1", "t", [Change("card.created", "c1", {"x": 1})])
    reopened = JsonLinesEventLog(path)
    assert [e.to_json() for e in reopened.since("b1")] == [
        e.to_json() for e in persisted.since("b1")]
    assert reopened.record("b1", 3, "u2", "t", [Change("card.deleted", "c1")])[0].seq == 2
