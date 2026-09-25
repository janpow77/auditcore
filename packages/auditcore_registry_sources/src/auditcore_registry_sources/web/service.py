"""Framework-free review service behind the HTTP adapters.

Every method takes plain data (parsed JSON, query mappings, the actor the
consumer authenticated) and returns JSON-ready dictionaries or raises
:class:`~.contract.ReviewError`. Authentication, authorisation beyond the
four-eyes rule, tenant separation and retention stay with the consumer: its
identity resolver decides who the actor is, its store decides which runs are
visible.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from .contract import (
    CONTRACT,
    OUTCOMES,
    Actor,
    RunRequest,
    conflict,
    invalid,
    not_found,
    parse_decision,
    parse_run_request,
    parse_second_review,
)
from .review import (
    EVENT_DECISION,
    EVENT_RUN_CREATED,
    EVENT_SECOND_REVIEW,
    ReviewState,
    decision_data,
    fold,
    second_review_data,
)
from .runner import execute, profile_views, resolve_profile
from .sources import SnapshotProvider, SourceState, state_view
from .store import ReviewEvent, ReviewStore, SequenceConflict, StoredRun
from .views import HitFilter, hit_view, log_view, run_view, summary


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ScreeningReviewService:
    """Screening runs, hit review with mandatory reasons and optional four-eyes rule."""

    def __init__(
        self,
        provider: SnapshotProvider,
        store: ReviewStore,
        *,
        four_eyes_outcomes: Sequence[str] = (),
        stale_after_days: float | None = None,
        clock: Callable[[], datetime] = _utc_now,
        new_id: Callable[[], str] = lambda: uuid.uuid4().hex,
    ) -> None:
        unknown = [o for o in four_eyes_outcomes if o not in OUTCOMES]
        if unknown:
            raise ValueError(f"Unbekannte Entscheidung(en) für das Vier-Augen-Prinzip: {unknown}")
        self.provider = provider
        self.store = store
        self.four_eyes_outcomes = tuple(four_eyes_outcomes)
        self.stale_after_days = stale_after_days
        self.clock = clock
        self.new_id = new_id

    def _now(self) -> str:
        return self.clock().astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    # -- reading -------------------------------------------------------------

    def settings(self) -> dict[str, Any]:
        """Profiles and review rules the client needs to render forms."""
        return {
            "contract": CONTRACT,
            "profiles": profile_views(),
            "four_eyes_outcomes": list(self.four_eyes_outcomes),
            "stale_after_days": self.stale_after_days,
        }

    def sources(self) -> dict[str, Any]:
        """Current state (Quellenstand) of every list."""
        now = self.clock()
        return {
            "contract": CONTRACT,
            "checked_at": self._now(),
            "sources": [state_view(s, now, self.stale_after_days) for s in self.provider.states()],
        }

    def list_runs(self) -> dict[str, Any]:
        """Summaries of the visible runs, newest first."""
        runs = [summary(run, fold(self.store.events(run.run_id))) for run in self.store.list_runs()]
        return {"contract": CONTRACT, "runs": runs}

    def _run(self, run_id: str) -> StoredRun:
        run = self.store.get_run(run_id)
        if run is None:
            raise not_found("Prüflauf nicht gefunden.")
        return run

    def get_run(self, run_id: str, query: Mapping[str, str] | None = None) -> dict[str, Any]:
        """A run with its hits, filtered by ``query``."""
        run = self._run(run_id)
        state = fold(self.store.events(run_id))
        return run_view(run, state, HitFilter.from_query(query or {}))

    def log(self, run_id: str) -> dict[str, Any]:
        """The review log of a run."""
        run = self._run(run_id)
        return log_view(run, self.store.events(run_id))

    # -- writing -------------------------------------------------------------

    def _selected_states(self, request: RunRequest) -> list[SourceState]:
        states = {s.list.key: s for s in self.provider.states() if s.kind == request.kind}
        if request.lists is None:
            if not states:
                raise invalid("Für diese Prüfart ist keine Liste eingerichtet.", field="lists")
            return list(states.values())
        unknown = [key for key in request.lists if key not in states]
        if unknown:
            raise invalid(
                f"Unbekannte oder unpassende Liste(n): {', '.join(unknown)}.", field="lists"
            )
        return [states[key] for key in request.lists]

    def create_run(self, body: Any, actor: Actor) -> dict[str, Any]:
        """Screen the subjects and store the run with its creation event."""
        request = parse_run_request(body)
        profile = resolve_profile(request)
        states = self._selected_states(request)
        snapshots = self.provider.snapshots([s.list.key for s in states])
        subjects = execute(request, profile, snapshots)
        now = self.clock()
        run = StoredRun(
            run_id=self.new_id(),
            created_at=self._now(),
            created_by=actor.to_dict(),
            kind=request.kind,
            request={
                "kind": request.kind,
                "profile": profile.reference,
                "lists": [s.list.key for s in states],
                "min_score": request.min_score,
                "limit": request.limit,
                "case_reference": request.case_reference,
                "subjects": [s.to_dict() for s in request.subjects],
            },
            result={
                "subjects": subjects,
                "sources": [state_view(s, now, self.stale_after_days) for s in states],
            },
        )
        event = ReviewEvent(
            run_id=run.run_id,
            sequence=1,
            type=EVENT_RUN_CREATED,
            at=run.created_at,
            actor=actor.to_dict(),
            data={"subjects": len(subjects)},
        )
        self.store.add_run(run, event)
        return self.get_run(run.run_id)

    def _append(
        self, run: StoredRun, hit_id: str, kind: str, data: dict[str, Any], actor: Actor, last: int
    ) -> None:
        event = ReviewEvent(
            run_id=run.run_id,
            sequence=last + 1,
            type=kind,
            at=self._now(),
            actor=actor.to_dict(),
            hit_id=hit_id,
            data=data,
        )
        try:
            self.store.append(event, expected_sequence=last)
        except SequenceConflict as exc:
            raise conflict(
                "concurrent_update",
                "Der Prüflauf wurde gleichzeitig geändert. Bitte neu laden und erneut entscheiden.",
            ) from exc

    def _hit(self, run_id: str, hit_id: str) -> tuple[StoredRun, ReviewState]:
        run = self._run(run_id)
        state = fold(self.store.events(run_id))
        try:
            hit_view(run, state, hit_id)
        except KeyError as exc:
            raise not_found("Treffer nicht gefunden.") from exc
        return run, state

    def decide(self, run_id: str, hit_id: str, body: Any, actor: Actor) -> dict[str, Any]:
        """Confirm, dismiss or defer a hit, with mandatory reason."""
        request = parse_decision(body)
        run, state = self._hit(run_id, hit_id)
        data = decision_data(state.of(hit_id), request, four_eyes_outcomes=self.four_eyes_outcomes)
        self._append(run, hit_id, EVENT_DECISION, data, actor, state.last_sequence)
        return hit_view(run, fold(self.store.events(run_id)), hit_id)

    def second_review(self, run_id: str, hit_id: str, body: Any, actor: Actor) -> dict[str, Any]:
        """Approve or reject a pending decision as a second, different person."""
        request = parse_second_review(body)
        run, state = self._hit(run_id, hit_id)
        data = second_review_data(state.of(hit_id), request, actor)
        self._append(run, hit_id, EVENT_SECOND_REVIEW, data, actor, state.last_sequence)
        return hit_view(run, fold(self.store.events(run_id)), hit_id)
