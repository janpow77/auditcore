"""Atomare Auswahl; nicht ausführbare Aufträge werden übersprungen."""

from __future__ import annotations

import json
import sqlite3
from uuid import uuid4

from .codec import read_job, read_node
from .database import event, transition
from .models import Job, Lease, State
from .resources import Allocation, Node, SchedulerPolicy, choose_node


def occupied(conn: sqlite3.Connection) -> tuple[Allocation, ...]:
    return tuple(
        Allocation(row["node_id"], tuple(json.loads(row["gpu_ids"])), row["cpus"], row["memory_mb"])
        for row in conn.execute("SELECT * FROM allocations")
    )


def nodes(conn: sqlite3.Connection) -> tuple[Node, ...]:
    result = []
    for row in conn.execute("SELECT snapshot FROM nodes"):
        try:
            result.append(read_node(row[0]))
        except (ValueError, TypeError, KeyError):
            continue  # Beschädigte Inventare niemals als verfügbare Kapazität behandeln.
    return tuple(result)


def propagate_blocked(conn: sqlite3.Connection, now: float) -> None:
    query = """SELECT DISTINCT j.scope,j.job_id FROM jobs j
      JOIN dependencies d ON d.scope=j.scope AND d.job_id=j.job_id
      JOIN jobs p ON p.scope=d.scope AND p.job_id=d.parent_id
      WHERE j.state IN ('waiting','retry') AND p.state IN ('failed','blocked','cancelled')"""
    while rows := conn.execute(query).fetchall():
        for row in rows:
            transition(
                conn,
                row["scope"],
                row["job_id"],
                now,
                "blocked",
                "Eine unmittelbare Voraussetzung ist fehlgeschlagen oder abgebrochen.",
            )


def waiting(conn: sqlite3.Connection, now: float, policy: SchedulerPolicy) -> list[Job]:
    query = """SELECT j.* FROM jobs j WHERE j.state IN ('waiting','retry')
      AND j.available_at<=? AND NOT EXISTS (
        SELECT 1 FROM dependencies d JOIN jobs p ON p.scope=d.scope AND p.job_id=d.parent_id
        WHERE d.scope=j.scope AND d.job_id=j.job_id AND p.state!='succeeded')"""
    result = []
    for row in conn.execute(query, (now,)).fetchall():
        try:
            spec = read_job(row["spec"])
            if (spec.scope, spec.job_id) != (row["scope"], row["job_id"]):
                raise ValueError("Auftragskennung stimmt nicht mit dem Datensatz überein.")
            result.append(
                Job(
                    spec,
                    State(row["state"]),
                    row["attempts"],
                    row["available_at"],
                    row["created_at"],
                    row["error"],
                )
            )
        except (ValueError, TypeError, KeyError) as error:
            transition(conn, row["scope"], row["job_id"], now, "failed", str(error))
    return sorted(
        result,
        key=lambda job: (
            -(job.spec.priority + int(max(0, now - job.created_at) / policy.aging_interval_s)),
            job.created_at,
            job.spec.scope,
            job.spec.job_id,
        ),
    )


def save_allocation(conn: sqlite3.Connection, token: str, value: Allocation, reason: str) -> None:
    conn.execute(
        "INSERT INTO allocations VALUES(?,?,?,?,?,?)",
        (token, value.node_id, json.dumps(value.gpu_ids), value.cpus, value.memory_mb, reason),
    )


def grant(conn: sqlite3.Connection, job: Job, allocation: Allocation, now: float) -> Lease:
    token = str(uuid4())
    spec = job.spec
    expires = min(now + spec.lease_s, now + spec.timeout_s)
    save_allocation(conn, token, allocation, "job")
    conn.execute(
        "INSERT INTO leases VALUES(?,?,?,?,?,?,?,?,?)",
        (
            token,
            spec.scope,
            spec.job_id,
            job.attempts + 1,
            now,
            expires,
            now + spec.timeout_s,
            now,
            0,
        ),
    )
    conn.execute(
        "UPDATE jobs SET state='running',attempts=attempts+1,error='' WHERE scope=? AND job_id=?",
        (spec.scope, spec.job_id),
    )
    event(conn, spec.scope, spec.job_id, now, "running", allocation.node_id)
    return Lease(
        token,
        spec,
        allocation.node_id,
        allocation.gpu_ids,
        job.attempts + 1,
        now,
        expires,
        now + spec.timeout_s,
    )


def claim(conn: sqlite3.Connection, now: float, policy: SchedulerPolicy) -> Lease | None:
    propagate_blocked(conn, now)
    available, allocations = nodes(conn), occupied(conn)
    for job in waiting(conn, now, policy):
        count = conn.execute(
            "SELECT COUNT(*) FROM leases WHERE scope=?", (job.spec.scope,)
        ).fetchone()[0]
        if count >= policy.max_active_per_scope:
            continue
        if job.attempts >= job.spec.retry.max_attempts:
            transition(
                conn,
                job.spec.scope,
                job.spec.job_id,
                now,
                "failed",
                "Höchstzahl der Versuche erreicht.",
            )
            continue
        allocation = choose_node(job.spec, available, allocations, now, policy)
        if allocation is not None:
            return grant(conn, job, allocation, now)
    return None


def reserve(
    conn: sqlite3.Connection,
    node_id: str,
    gpu_ids: tuple[str, ...],
    cpus: int,
    memory_mb: int,
    reason: str,
    now: float,
    policy: SchedulerPolicy,
) -> str:
    node = next((n for n in nodes(conn) if n.node_id == node_id), None)
    if node is None or not 0 <= now - node.observed_at <= policy.node_max_age_s:
        raise ValueError("Rechner ist nicht verfügbar.")
    active = tuple(a for a in occupied(conn) if a.node_id == node_id)
    busy = {gpu for a in active for gpu in a.gpu_ids}
    allowed = {g.gpu_id for g in node.gpus if not g.blocked}
    if not set(gpu_ids) <= allowed or set(gpu_ids) & busy:
        raise ValueError("Mindestens eine GPU ist belegt oder nicht vorhanden.")
    if sum(a.cpus for a in active) + cpus > node.cpus:
        raise ValueError("CPU-Budget ist belegt.")
    if sum(a.memory_mb for a in active) + memory_mb > node.memory_mb:
        raise ValueError("RAM-Budget ist belegt.")
    token = str(uuid4())
    save_allocation(conn, token, Allocation(node_id, gpu_ids, cpus, memory_mb), reason)
    return token
