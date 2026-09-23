"""Bridge from a harvest run to regulierung's run protocol (``erfolg``/``teilweise``/``fehler``).

The consumer keeps its run log (``external_api_lauf``), registry, secrets and
ORM rows; these helpers only translate the structured
:class:`auditcore_harvest.HarvestResult` into the status words and the
secret-free error text the existing protocol and API expect.
"""

from __future__ import annotations

from auditcore_harvest import HarvestResult, RunStatus

LEGACY_STATUS = {
    RunStatus.COMPLETE: "erfolg",
    RunStatus.PARTIAL: "teilweise",
    RunStatus.FAILED: "fehler",
    RunStatus.CANCELLED: "fehler",
}


def legacy_status(result: HarvestResult) -> str:
    """``erfolg`` (complete), ``teilweise`` (partial) or ``fehler`` (failed/cancelled)."""
    return LEGACY_STATUS[result.status]


def error_text(result: HarvestResult, *, limit: int = 500) -> str | None:
    """Error and issue messages of the run, joined and bounded; ``None`` if there were none."""
    parts = [str(error.get("message", "")) for error in result.errors]
    parts += [f"{issue.locator}: {issue.message}" for issue in result.issues]
    text = "; ".join(p for p in parts if p)
    return text[:limit] if text else None
