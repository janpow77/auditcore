"""Öffentliche, dauerhaft gespeicherte Koordinator-API."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

from . import lifecycle, placement
from .codec import encode, read_job
from .database import Database, event
from .models import Job, JobSpec, Lease, Outcome, State, StopRequest
from .resources import Allocation, Node, SchedulerPolicy
from .validation import identifier, integer, names, number


class Queue:
    """Ein DB-Stand pro Koordinator; parallele Prozesse öffnen eigene Verbindungen.

    Über Rechnergrenzen ruft ein authentifizierter App-Adapter diese API auf.
    Die SQLite-Datei gehört auf lokalen Speicher, nicht auf ein Netzlaufwerk.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        policy: SchedulerPolicy | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.database = Database(path)
        self.policy = policy or SchedulerPolicy()
        self.clock = clock

    def _now(self) -> float:
        return number(self.clock(), "clock")

    def enqueue(self, spec: JobSpec) -> Job:
        """Gleiche Kennung und gleicher Vertrag sind idempotent; Änderungen werden abgewiesen."""
        encoded, now = encode(spec), self._now()
        with self.database.transaction() as conn:
            existing = conn.execute(
                "SELECT spec FROM jobs WHERE scope=? AND job_id=?", (spec.scope, spec.job_id)
            ).fetchone()
            if existing and existing[0] != encoded:
                raise ValueError("Auftragskennung ist bereits mit einem anderen Vertrag belegt.")
            if not existing:
                self._insert(conn, spec, encoded, now)
            placement.propagate_blocked(conn, now)
        result = self.get(spec.scope, spec.job_id)
        assert result is not None
        return result

    @staticmethod
    def _insert(conn: sqlite3.Connection, spec: JobSpec, encoded: str, now: float) -> None:
        for parent in spec.dependencies:
            if not conn.execute(
                "SELECT 1 FROM jobs WHERE scope=? AND job_id=?", (spec.scope, parent)
            ).fetchone():
                raise ValueError(f"Voraussetzung fehlt im selben Bereich: {parent}")
        conn.execute(
            "INSERT INTO jobs(scope,job_id,spec,state,available_at,created_at) "
            "VALUES(?,?,?,'waiting',?,?)",
            (spec.scope, spec.job_id, encoded, max(now, spec.not_before), now),
        )
        conn.executemany(
            "INSERT INTO dependencies VALUES(?,?,?)",
            ((spec.scope, spec.job_id, parent) for parent in spec.dependencies),
        )
        event(conn, spec.scope, spec.job_id, now, "waiting")

    def publish_node(self, node: Node) -> bool:
        """Ältere Inventarmeldungen dürfen einen neueren Sperrzustand nicht überschreiben."""
        with self.database.transaction() as conn:
            result = conn.execute(
                "INSERT INTO nodes VALUES(?,?,?) ON CONFLICT(node_id) "
                "DO UPDATE SET observed_at=excluded.observed_at, "
                "snapshot=excluded.snapshot "
                "WHERE excluded.observed_at>nodes.observed_at",
                (node.node_id, node.observed_at, encode(node)),
            )
            return result.rowcount == 1

    def claim(self) -> Lease | None:
        """Platzierung und Reservierung sind eine einzige Transaktion."""
        with self.database.transaction() as conn:
            now = self._now()
            lifecycle.recover(conn, now)
            return placement.claim(conn, now, self.policy)

    def heartbeat(self, token: str, *, progress: float | None = None) -> bool:
        """Lebenszeichen verlängern keine Laufzeit- oder Fortschrittsfrist."""
        if progress is not None:
            number(progress, "progress")
        with self.database.transaction() as conn:
            return lifecycle.heartbeat(conn, token, self._now(), progress)

    def finish(self, token: str, outcome: Outcome) -> bool:
        """Nur nach beendetem Prozess/Remote-Aufruf; veraltete Ergebnisse werden abgewiesen."""
        with self.database.transaction() as conn:
            return lifecycle.finish(conn, token, self._now(), outcome)

    def recover_expired(self) -> tuple[str, ...]:
        with self.database.transaction() as conn:
            return lifecycle.recover(conn, self._now())

    def confirm_stopped(self, token: str) -> bool:
        """Sperre eines abgelaufenen/abgebrochenen Versuchs nach Prozessende freigeben."""
        with self.database.transaction() as conn:
            return lifecycle.confirm_stopped(conn, token, self._now())

    def pending_stops(self) -> tuple[StopRequest, ...]:
        """Auch nach Koordinator-Neustart alle noch zu beendenden Versuche finden."""
        with self.database.connect() as conn:
            return tuple(
                StopRequest(r[0], r[1], r[2], r[3], r[4])
                for r in conn.execute(
                    "SELECT l.token,a.node_id,j.scope,j.job_id,j.error FROM leases l "
                    "JOIN allocations a ON a.token=l.token "
                    "JOIN jobs j ON j.scope=l.scope AND j.job_id=l.job_id "
                    "WHERE j.state IN ('recovering','cancelling','pausing') ORDER BY l.token"
                )
            )

    def cancel(self, scope: str, job_id: str) -> bool:
        with self.database.transaction() as conn:
            return lifecycle.cancel(conn, scope, job_id, self._now())

    def drain_node(self, node_id: str) -> tuple[str, ...]:
        """Neue Zuteilung sperren und laufende Arbeit zum kontrollierten Stoppen markieren."""
        from dataclasses import replace

        from .codec import read_node

        with self.database.transaction() as conn:
            now = self._now()
            row = conn.execute("SELECT snapshot FROM nodes WHERE node_id=?", (node_id,)).fetchone()
            if row is None:
                return ()
            node = replace(read_node(row[0]), accepting=False, observed_at=now)
            conn.execute(
                "UPDATE nodes SET snapshot=?,observed_at=? WHERE node_id=?",
                (encode(node), now, node_id),
            )
            return lifecycle.stop_node(conn, node_id, now)

    def reserve(
        self,
        node_id: str,
        gpu_ids: tuple[str, ...],
        *,
        reason: str,
        cpus: int = 0,
        memory_mb: int = 0,
    ) -> str:
        """Externe Arbeit, etwa Training, reservieren; keine automatische Freigabe nach Zeit."""
        identifier(node_id)
        identifier(reason)
        names(gpu_ids)
        integer(cpus, "cpus")
        integer(memory_mb, "memory_mb")
        with self.database.transaction() as conn:
            return placement.reserve(
                conn, node_id, gpu_ids, cpus, memory_mb, reason, self._now(), self.policy
            )

    def release_reservation(self, token: str) -> bool:
        """Nur externe Reservierungen; aktive Auftragsberechtigungen sind hier geschützt."""
        with self.database.transaction() as conn:
            result = conn.execute(
                "DELETE FROM allocations WHERE token=? AND NOT EXISTS "
                "(SELECT 1 FROM leases WHERE leases.token=allocations.token)",
                (token,),
            )
            return result.rowcount == 1

    def allocations(self) -> tuple[Allocation, ...]:
        with self.database.connect() as conn:
            return placement.occupied(conn)

    def get(self, scope: str, job_id: str) -> Job | None:
        with self.database.connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE scope=? AND job_id=?", (scope, job_id)
            ).fetchone()
            return (
                None
                if row is None
                else Job(
                    read_job(row["spec"]),
                    State(row["state"]),
                    row["attempts"],
                    row["available_at"],
                    row["created_at"],
                    row["error"],
                )
            )

    def events(self, scope: str, job_id: str) -> tuple[tuple[float, str, str], ...]:
        with self.database.connect() as conn:
            return tuple(
                (r[0], r[1], r[2])
                for r in conn.execute(
                    "SELECT at,kind,detail FROM events WHERE scope=? AND job_id=? "
                    "ORDER BY event_id",
                    (scope, job_id),
                )
            )
