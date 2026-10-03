"""Arbeitsberechtigungen, Fortschritt und bestätigte Ressourcenfreigabe."""

from __future__ import annotations

import sqlite3
from typing import cast

from .codec import read_job
from .database import event, transition
from .models import JobSpec, Outcome


def lease_row(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    return cast(
        sqlite3.Row | None,
        conn.execute(
            "SELECT l.*,j.spec,j.state FROM leases l JOIN jobs j "
            "ON j.scope=l.scope AND j.job_id=l.job_id WHERE l.token=?",
            (token,),
        ).fetchone(),
    )


def expiry(row: sqlite3.Row, spec: JobSpec, now: float) -> str | None:
    if now >= row["deadline"]:
        return "Gesamtlaufzeit überschritten."
    if now >= row["expires_at"]:
        return "Arbeitsberechtigung abgelaufen."
    if spec.stall_timeout_s is not None and now >= row["progress_at"] + spec.stall_timeout_s:
        return "Kein messbarer Fortschritt innerhalb der Frist."
    return None


def recover(conn: sqlite3.Connection, now: float) -> tuple[str, ...]:
    tokens = []
    for row in conn.execute(
        "SELECT l.*,j.spec FROM leases l JOIN jobs j "
        "ON j.scope=l.scope AND j.job_id=l.job_id "
        "WHERE j.state='running'"
    ).fetchall():
        try:
            reason = expiry(row, read_job(row["spec"]), now)
        except (ValueError, TypeError, KeyError):
            reason = "Auftragsvertrag ist beschädigt."
        if reason:
            transition(conn, row["scope"], row["job_id"], now, "recovering", reason)
            tokens.append(row["token"])
    return tuple(tokens)


def heartbeat(conn: sqlite3.Connection, token: str, now: float, progress: float | None) -> bool:
    recover(conn, now)
    row = lease_row(conn, token)
    if row is None or row["state"] != "running":
        return False
    spec = read_job(row["spec"])
    if progress is not None and progress < row["progress"]:
        raise ValueError("Fortschritt darf innerhalb eines Versuchs nicht zurückgehen.")
    conn.execute(
        "UPDATE leases SET expires_at=? WHERE token=?",
        (min(now + spec.lease_s, row["deadline"]), token),
    )
    if progress is not None and progress > row["progress"]:
        conn.execute(
            "UPDATE leases SET progress=?,progress_at=? WHERE token=?", (progress, now, token)
        )
    return True


def release_claim(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM leases WHERE token=?", (token,))
    conn.execute("DELETE FROM allocations WHERE token=?", (token,))


def conclude(conn: sqlite3.Connection, row: sqlite3.Row, now: float, outcome: Outcome) -> None:
    spec = read_job(row["spec"])
    state, available, attempts = "failed", now, row["attempt"]
    if outcome.kind == "succeeded":
        state = "succeeded"
    elif outcome.kind == "deferred":
        if outcome.retry_at is None or outcome.retry_at <= now:
            raise ValueError("Zurückstellen benötigt einen zukünftigen Zeitpunkt.")
        state, available, attempts = "waiting", outcome.retry_at, attempts - 1
    elif outcome.kind == "retryable" and attempts < spec.retry.max_attempts:
        state, available = "retry", now + spec.retry.delay(attempts)
    release_claim(conn, row["token"])
    conn.execute(
        "UPDATE jobs SET attempts=?,available_at=? WHERE scope=? AND job_id=?",
        (attempts, available, row["scope"], row["job_id"]),
    )
    transition(conn, row["scope"], row["job_id"], now, state, outcome.message)


def finish(conn: sqlite3.Connection, token: str, now: float, outcome: Outcome) -> bool:
    """Nur ein lebender Versuch darf ein Ergebnis veröffentlichen; Prozess muss beendet sein."""
    recover(conn, now)
    row = lease_row(conn, token)
    if row is None or row["state"] != "running":
        return False
    conclude(conn, row, now, outcome)
    return True


def confirm_stopped(conn: sqlite3.Connection, token: str, now: float) -> bool:
    """Nur nach nachgewiesenem Prozessende aufrufen, niemals allein wegen Zeitablauf."""
    row = lease_row(conn, token)
    if row is None or row["state"] not in ("recovering", "cancelling", "pausing"):
        return False
    if row["state"] == "cancelling":
        release_claim(conn, token)
        transition(conn, row["scope"], row["job_id"], now, "cancelled", "Prozessende bestätigt.")
    else:
        try:
            outcome = Outcome("retryable", "Abgebrochener Versuch; Prozess beendet.")
            if row["state"] == "pausing":
                spec = read_job(row["spec"])
                outcome = Outcome(
                    "deferred",
                    "Rechner wird anderweitig benötigt.",
                    retry_at=now + spec.retry.initial_delay_s,
                )
            conclude(conn, row, now, outcome)
        except (ValueError, TypeError, KeyError):
            release_claim(conn, token)
            transition(
                conn,
                row["scope"],
                row["job_id"],
                now,
                "failed",
                "Auftragsvertrag beschädigt; Prozessende bestätigt.",
            )
    return True


def cancel(conn: sqlite3.Connection, scope: str, job_id: str, now: float) -> bool:
    row = conn.execute(
        "SELECT state FROM jobs WHERE scope=? AND job_id=?", (scope, job_id)
    ).fetchone()
    if row is None or row[0] in ("succeeded", "failed", "blocked", "cancelled"):
        return False
    active = conn.execute(
        "SELECT 1 FROM leases WHERE scope=? AND job_id=?", (scope, job_id)
    ).fetchone()
    transition(
        conn, scope, job_id, now, "cancelling" if active else "cancelled", "Abbruch angefordert."
    )
    return True


def stop_node(conn: sqlite3.Connection, node_id: str, now: float) -> tuple[str, ...]:
    """Laufende Aufträge zurücknehmen, etwa wenn der Eigentümer den Rechner benötigt."""
    rows = conn.execute(
        "SELECT l.* FROM leases l JOIN allocations a ON a.token=l.token "
        "JOIN jobs j ON j.scope=l.scope AND j.job_id=l.job_id "
        "WHERE a.node_id=? AND j.state='running'",
        (node_id,),
    ).fetchall()
    for row in rows:
        transition(
            conn,
            row["scope"],
            row["job_id"],
            now,
            "pausing",
            "Rechnerfreigabe zurückgenommen; Prozessende erforderlich.",
        )
        event(conn, row["scope"], row["job_id"], now, "preempted", node_id)
    return tuple(row["token"] for row in rows)
