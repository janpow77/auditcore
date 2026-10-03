"""SQLite-Adapter für einen zentralen Koordinator; Transaktionen enthalten keine Arbeit."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
 scope TEXT NOT NULL, job_id TEXT NOT NULL, spec TEXT NOT NULL,
 state TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
 available_at REAL NOT NULL, created_at REAL NOT NULL, error TEXT NOT NULL DEFAULT '',
 PRIMARY KEY(scope, job_id)
);
CREATE INDEX IF NOT EXISTS jobs_due ON jobs(state, available_at);
CREATE TABLE IF NOT EXISTS dependencies (
 scope TEXT NOT NULL, job_id TEXT NOT NULL, parent_id TEXT NOT NULL,
 PRIMARY KEY(scope, job_id, parent_id),
 FOREIGN KEY(scope,job_id) REFERENCES jobs(scope,job_id),
 FOREIGN KEY(scope,parent_id) REFERENCES jobs(scope,job_id)
);
CREATE TABLE IF NOT EXISTS nodes (
 node_id TEXT PRIMARY KEY, observed_at REAL NOT NULL, snapshot TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS allocations (
 token TEXT PRIMARY KEY, node_id TEXT NOT NULL, gpu_ids TEXT NOT NULL,
 cpus INTEGER NOT NULL, memory_mb INTEGER NOT NULL, reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS leases (
 token TEXT PRIMARY KEY REFERENCES allocations(token),
 scope TEXT NOT NULL, job_id TEXT NOT NULL, attempt INTEGER NOT NULL,
 started_at REAL NOT NULL, expires_at REAL NOT NULL, deadline REAL NOT NULL,
 progress_at REAL NOT NULL, progress REAL NOT NULL DEFAULT 0,
 UNIQUE(scope,job_id), FOREIGN KEY(scope,job_id) REFERENCES jobs(scope,job_id)
);
CREATE TABLE IF NOT EXISTS events (
 event_id INTEGER PRIMARY KEY, scope TEXT NOT NULL, job_id TEXT NOT NULL,
 at REAL NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL
);
PRAGMA user_version=1;
"""


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if str(path) == ":memory:":
            raise ValueError("Die Warteschlange benötigt eine dauerhafte SQLite-Datei.")
        with self.connect() as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError(f"Unbekannte Datenbankversion: {version}")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=FULL")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
            except BaseException:
                conn.rollback()
                raise
            else:
                conn.commit()


def event(
    conn: sqlite3.Connection, scope: str, job_id: str, now: float, kind: str, detail: str = ""
) -> None:
    conn.execute(
        "INSERT INTO events(scope,job_id,at,kind,detail) VALUES(?,?,?,?,?)",
        (scope, job_id, now, kind, detail[:1000]),
    )


def transition(
    conn: sqlite3.Connection, scope: str, job_id: str, now: float, state: str, detail: str = ""
) -> None:
    conn.execute(
        "UPDATE jobs SET state=?,error=? WHERE scope=? AND job_id=?",
        (state, detail[:1000], scope, job_id),
    )
    event(conn, scope, job_id, now, state, detail)
