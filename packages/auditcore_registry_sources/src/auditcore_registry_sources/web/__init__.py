"""Screening review API (Screening-Trefferprüfung), contract ``screening_review/1``.

Framework-free core: :class:`ScreeningReviewService` runs sanctions and PEP
screenings through the library, keeps an append-only review log in an
injected :class:`ReviewStore` and derives each hit's state (open, confirmed,
dismissed, deferred, pending second review) from it. HTTP adapters are
optional: :func:`auditcore_registry_sources.web.http.create_routes` /
``create_app`` (extra ``web``, Starlette) and
:func:`auditcore_registry_sources.web.fastapi_router.create_router` (FastAPI).
They are not imported here, so the core works without either framework.
"""

from __future__ import annotations

from .contract import (
    CONTRACT,
    OUTCOMES,
    REVIEW_STATUSES,
    Actor,
    ReviewError,
    Subject,
)
from .service import ScreeningReviewService
from .sources import SnapshotProvider, SourceState, StaticSnapshotProvider
from .store import InMemoryReviewStore, ReviewEvent, ReviewStore, SequenceConflict, StoredRun

__all__ = [
    "CONTRACT",
    "OUTCOMES",
    "REVIEW_STATUSES",
    "Actor",
    "InMemoryReviewStore",
    "ReviewError",
    "ReviewEvent",
    "ReviewStore",
    "ScreeningReviewService",
    "SequenceConflict",
    "SnapshotProvider",
    "SourceState",
    "StaticSnapshotProvider",
    "StoredRun",
    "Subject",
]
