"""The coherent bundle: operations, claims, receipts, payment applications, accounts.

:func:`build_bundle` returns canonical tables (English field keys, typed
cells). Template profiles (:mod:`templates`) project these tables into the
column layouts of the documents; no template has code of its own.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from auditcore_dummybundle import accounts, applications, corrections
from auditcore_dummybundle.chain import build_claims, build_operation, settle_claim
from auditcore_dummybundle.config import BundleConfig
from auditcore_dummybundle.model import Budget, Row, SolutionEntry
from auditcore_dummybundle.receipts import build_receipts, build_suppliers

#: Columns of the appendices that the bundle fills with zero amounts only.
_EMPTY_ANNEXES = {
    "accounts_annex3": ("paid", "paid_public", "booked", "booked_public"),
    "accounts_annex7": ("advances", "covered", "uncovered"),
}


@dataclass
class Bundle:
    """Canonical tables of one run, keyed by table name."""

    config: BundleConfig
    tables: dict[str, list[Row]]
    solution: list[SolutionEntry] = field(default_factory=list)
    #: Row object of every solution entry, in the same order (for output row numbers).
    solution_rows: list[Row] = field(default_factory=list)
    skipped_anomalies: list[str] = field(default_factory=list)

    def table(self, name: str) -> list[Row]:
        """Rows of the canonical table ``name``."""
        return self.tables[name]


def _chain(config: BundleConfig, budget: Budget) -> tuple[list[Row], list[Row], list[Row]]:
    suppliers = build_suppliers(config)
    operations: list[Row] = []
    claims: list[Row] = []
    receipts: list[Row] = []
    for index in range(1, config.operations + 1):
        operation = build_operation(config, index)
        operations.append(operation)
        for claim in build_claims(config, operation):
            budget.tick()
            own = build_receipts(config, operation, claim, suppliers)
            settle_claim(config, claim, own)
            claims.append(claim)
            receipts.extend(own)
    return operations, claims, receipts


def build_bundle(config: BundleConfig, budget: Budget | None = None) -> Bundle:
    """Build the consistent bundle for ``config``; equal configurations give equal bundles."""
    operations, claims, receipts = _chain(config, budget or Budget())
    schedule = applications.build_schedule(config)
    applications.assign_claims(schedule, claims)
    corrected = corrections.build_corrections(config, operations, claims, receipts, schedule)
    payment = applications.build_applications(config, schedule, claims, corrected)
    annex1 = accounts.build_annex1(config, payment, corrected)
    tables: dict[str, list[Row]] = {
        "operations": operations,
        "claims": claims,
        "receipts": receipts,
        "payment_applications": payment,
        "corrections": corrected,
        "findings": corrections.build_findings(corrected),
        "accounts_annex1": annex1,
        "accounts_annex2": accounts.build_annex2(config, corrected),
        "accounts_annex4": accounts.build_annex4(config, payment, annex1, corrected),
        "accounts_annex5": accounts.build_annex5(annex1),
        "accounts_annex6": [],
        "accounts_head": accounts.build_head(config),
        "population": accounts.build_population(config, operations, claims, corrected, schedule),
    }
    for name, columns in _EMPTY_ANNEXES.items():
        tables[name] = accounts.build_empty_annex(config, columns)
    return Bundle(config, tables)
