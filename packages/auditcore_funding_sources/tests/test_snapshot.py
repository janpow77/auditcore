"""The database-free mode plan equals the executed original ``run_beneficiary_harvest``.

The fixture ``modes_run`` was recorded against a disposable PostgreSQL with the
unchanged source (smart, full-refresh, force, snapshot, rejected files).
"""

from __future__ import annotations

from typing import Any

import pytest
from conftest import FIXTURES, load, revive

from auditcore_funding_sources import snapshot, workshop
from auditcore_funding_sources.errors import SnapshotRejected

RUNS = revive(load("flowworkshop")["constants"])["modes_run"]
BASE = (FIXTURES / "files" / "semikolon_ohne_titel.csv").read_bytes()
CHANGED = BASE.replace(b"150000;75000", b"160000;80000").replace(
    b"Ohne Kosten e.V.;Beratung;;;", b"Neu GmbH;Beratung;;;"
)
DUPLICATE = BASE + (
    b"Beispiel GmbH;Energie 2030;1.234.567,89;617.283,95;01067;Dresden;01.02.2024;"
    b"31.12.2026;AZ-1;EFRE\n"
)
# Same bytes as the capture (header misspelt, so no name column is recognised).
REJECTED = "Name des Begrünstigten;Gesamtkosten\nA;-5\n".encode()
CONTENT = {
    "snapshot-initial": BASE,
    "smart-same": BASE,
    "smart-changed": CHANGED,
    "full-refresh-changed": CHANGED,
    "force-base": BASE,
    "snapshot-changed": CHANGED,
    "snapshot-duplicate-row": DUPLICATE,
    "smart-rejected": REJECTED,
    "snapshot-rejected": REJECTED,
    "invalid-mode": BASE,
    "no-context": BASE,
}
CONTEXT = workshop.SnapshotContext("hessen_efre", "Hessen", "EFRE", "2021-2027", "DE")


def test_plan_reproduces_every_executed_run() -> None:
    stored: list[str] = []
    assert [r["name"] for r in RUNS] == list(CONTENT)
    for observed in RUNS:
        rows = workshop.parse_file(CONTENT[observed["name"]], "liste.csv")
        context = (
            CONTEXT if observed["name"] != "no-context" else workshop.SnapshotContext("hessen_efre")
        )
        expected_ids = [row[0] for row in observed["inventory"]]
        if observed["exception"]:
            with pytest.raises((ValueError, SnapshotRejected)) as caught:
                snapshot.plan_snapshot(
                    rows, context, mode=observed["mode"], stored_identities=stored
                )
            assert str(caught.value) == observed["exception"]["message"]
            assert sorted(stored) == sorted(expected_ids)
            continue
        plan = snapshot.plan_snapshot(
            rows, context, mode=observed["mode"], stored_identities=stored
        )
        result: dict[str, Any] = revive(observed["result"])  # encoded twice by the capture
        assert plan.status == result["status"]
        assert plan.records_seen == result["records_seen"]
        assert plan.records_inserted == result["records_inserted"]
        assert plan.records_skipped == result["records_skipped"]
        assert plan.records_failed == result["records_failed"]
        assert plan.message == result["error"]
        stored = plan.resulting_identities(stored)
        assert stored == sorted(expected_ids), observed["name"]


def test_modes_are_not_a_parser_option() -> None:
    rows = workshop.parse_file(BASE, "liste.csv")
    with pytest.raises(ValueError, match="mode muss"):
        snapshot.plan_snapshot(rows, CONTEXT, mode="replace", stored_identities=[])
    smart = snapshot.plan_snapshot(rows, CONTEXT, mode="smart", stored_identities=["x"])
    snap = snapshot.plan_snapshot(rows, CONTEXT, mode="snapshot", stored_identities=["x"])
    assert not smart.delete_all_first and snap.delete_all_first
    assert "x" in smart.resulting_identities(["x"]) and "x" not in snap.resulting_identities(["x"])


def test_rejection_happens_before_any_deletion() -> None:
    rows = workshop.parse_file(
        "Name des Begünstigten;Gesamtkosten;Unionsbeteiligung\nA GmbH;10;20\nB GmbH;5;1\n".encode(),
        "x.csv",
    )
    with pytest.raises(SnapshotRejected) as caught:
        snapshot.plan_snapshot(rows, CONTEXT, mode="snapshot", stored_identities=["keep"])
    assert "EU-Anteil ist größer als Gesamtkosten" in caught.value.errors[0]
