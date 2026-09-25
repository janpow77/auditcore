"""Decision workflow: mandatory reason, four-eyes rule, final states, conflicts, log."""

from __future__ import annotations

from typing import Any

import pytest
from web_support import ALICE, BOB, make_service, sanctions_body

from auditcore_registry_sources.web import (
    Actor,
    InMemoryReviewStore,
    ReviewError,
    ReviewEvent,
    ScreeningReviewService,
    SequenceConflict,
    StoredRun,
)
from auditcore_registry_sources.web.contract import parse_decision, parse_run_request


def _setup(**options: Any) -> tuple[ScreeningReviewService, str, str]:
    service = make_service(**options)
    run = service.create_run(sanctions_body(), ALICE)
    return service, run["run_id"], run["subjects"][0]["hits"][0]["hit_id"]


def _code(call: Any) -> tuple[int, str]:
    with pytest.raises(ReviewError) as caught:
        call()
    return caught.value.status, caught.value.code


def test_decision_without_four_eyes_is_final() -> None:
    service, run_id, hit_id = _setup()
    reason = "Geburtsdatum und Anschrift weichen vom Vorgang ab."
    hit = service.decide(run_id, hit_id, {"outcome": "dismissed", "reason": reason}, ALICE)
    assert hit["review"]["status"] == "dismissed"
    assert hit["review"]["status_label"] == "verworfen"
    assert hit["review"]["decision"]["reason"] == reason
    assert hit["review"]["decision"]["actor"]["id"] == "pruefer-a"
    again = {"outcome": "confirmed", "reason": "Doch ein Treffer."}
    assert _code(lambda: service.decide(run_id, hit_id, again, BOB)) == (409, "already_decided")


def test_deferred_hit_can_be_decided_again() -> None:
    service, run_id, hit_id = _setup()
    service.decide(
        run_id, hit_id, {"outcome": "deferred", "reason": "Unterlagen angefordert."}, ALICE
    )
    hit = service.decide(
        run_id, hit_id, {"outcome": "confirmed", "reason": "Pass liegt vor, identisch."}, ALICE
    )
    assert hit["review"]["status"] == "confirmed"
    assert hit["review"]["events"] == 2


@pytest.mark.parametrize("reason", [None, "", "   \n\t"])
def test_reason_is_mandatory(reason: Any) -> None:
    service, run_id, hit_id = _setup()
    body = {"outcome": "dismissed", "reason": reason}
    assert _code(lambda: service.decide(run_id, hit_id, body, ALICE)) == (422, "invalid_request")


def test_four_eyes_requires_a_second_different_person() -> None:
    service, run_id, hit_id = _setup()
    body = {"outcome": "confirmed", "reason": "Alle Merkmale stimmen.", "four_eyes": True}
    hit = service.decide(run_id, hit_id, body, ALICE)
    assert hit["review"]["status"] == "pending_second_review"
    assert hit["review"]["decision"]["four_eyes_source"] == "requested"
    same = {"approve": True, "reason": "Selbst bestätigt."}
    assert _code(lambda: service.second_review(run_id, hit_id, same, ALICE)) == (409, "same_person")
    other = {"outcome": "dismissed", "reason": "Neu."}
    assert _code(lambda: service.decide(run_id, hit_id, other, BOB)) == (
        409,
        "second_review_pending",
    )
    hit = service.second_review(
        run_id, hit_id, {"approve": True, "reason": "Nachvollzogen, stimme zu."}, BOB
    )
    assert hit["review"]["status"] == "confirmed"
    assert hit["review"]["second_review"]["actor"]["id"] == "pruefer-b"


def test_rejected_second_review_reopens_the_hit() -> None:
    service, run_id, hit_id = _setup()
    body = {"outcome": "dismissed", "reason": "Kein Bezug.", "four_eyes": True}
    service.decide(run_id, hit_id, body, ALICE)
    hit = service.second_review(
        run_id, hit_id, {"approve": False, "reason": "Geburtsjahr passt, bitte prüfen."}, BOB
    )
    assert hit["review"]["status"] == "open"
    assert hit["review"]["second_review"]["approve"] is False
    hit = service.decide(run_id, hit_id, {"outcome": "deferred", "reason": "Rückfrage."}, ALICE)
    assert hit["review"]["status"] == "deferred"
    assert hit["review"]["second_review"] is None


def test_policy_forces_four_eyes_for_configured_outcomes() -> None:
    service, run_id, hit_id = _setup(four_eyes_outcomes=["confirmed", "dismissed"])
    hit = service.decide(run_id, hit_id, {"outcome": "dismissed", "reason": "Kein Bezug."}, ALICE)
    assert hit["review"]["status"] == "pending_second_review"
    assert hit["review"]["decision"]["four_eyes_source"] == "policy"
    body = {"approve": True, "reason": "Einverstanden."}
    other_hit = service.get_run(run_id)["subjects"][0]["hits"][1]["hit_id"]
    assert _code(lambda: service.second_review(run_id, other_hit, body, BOB)) == (
        409,
        "no_pending_decision",
    )
    with pytest.raises(ValueError):
        make_service(four_eyes_outcomes=["bestätigt"])


def test_stale_expected_sequence_is_a_conflict() -> None:
    service, run_id, hit_id = _setup()
    body = {"outcome": "deferred", "reason": "Rückfrage.", "expected_sequence": 0}
    service.decide(run_id, hit_id, body, ALICE)
    late = {"outcome": "dismissed", "reason": "Kein Bezug.", "expected_sequence": 0}
    assert _code(lambda: service.decide(run_id, hit_id, late, BOB)) == (409, "stale_state")


class RacingStore(InMemoryReviewStore):
    """Simulates another reviewer appending between read and write."""

    def append(self, event: ReviewEvent, *, expected_sequence: int) -> None:
        raise SequenceConflict(expected_sequence, expected_sequence + 1)


def test_concurrent_append_is_reported_not_lost() -> None:
    service, run_id, hit_id = _setup()
    racing = RacingStore()
    run = service.store.get_run(run_id)
    assert isinstance(run, StoredRun)
    racing.add_run(run, service.store.events(run_id)[0])
    service.store = racing
    body = {"outcome": "dismissed", "reason": "Kein Bezug."}
    assert _code(lambda: service.decide(run_id, hit_id, body, ALICE)) == (
        409,
        "concurrent_update",
    )


def test_unknown_hit_is_404() -> None:
    service, run_id, _hit = _setup()
    body = {"outcome": "dismissed", "reason": "x"}
    assert _code(lambda: service.decide(run_id, "hunbekannt", body, ALICE))[0] == 404


def test_log_contains_every_step_with_labels_and_names() -> None:
    service, run_id, hit_id = _setup()
    body = {"outcome": "confirmed", "reason": "Identisch.", "four_eyes": True}
    service.decide(run_id, hit_id, body, ALICE)
    service.second_review(run_id, hit_id, {"approve": True, "reason": "Zugestimmt."}, BOB)
    events = service.log(run_id)["events"]
    assert [e["sequence"] for e in events] == [1, 2, 3]
    assert [e["type_label"] for e in events] == [
        "Prüflauf angelegt",
        "Entscheidung erfasst",
        "Zweitprüfung erfasst",
    ]
    assert events[1]["hit"]["subject_name"] == "Maximilian Beispielmann"
    assert events[1]["outcome_label"] == "bestätigt"
    assert events[2]["actor"]["id"] == "pruefer-b"
    summary = service.list_runs()["runs"][0]
    assert summary["review_counts"]["confirmed"] == 1


def test_store_rejects_duplicate_runs_and_unknown_logs() -> None:
    store = InMemoryReviewStore()
    run = StoredRun("r", "2026-09-25T12:00:00Z", {"id": "a"}, "sanctions", {}, {})
    first = ReviewEvent("r", 1, "run_created", "2026-09-25T12:00:00Z", {"id": "a"})
    store.add_run(run, first)
    with pytest.raises(ValueError):
        store.add_run(run, first)
    with pytest.raises(KeyError):
        store.append(ReviewEvent("x", 2, "t", "now", {"id": "a"}), expected_sequence=1)


@pytest.mark.parametrize(
    "body",
    [
        None,
        [],
        {"kind": "andere"},
        {"kind": "sanctions"},
        {"kind": "sanctions", "profile": {"id": "p"}},
        {"kind": "sanctions", "profile": {"id": "p", "version": "1"}, "subjects": []},
        {"kind": "sanctions", "profile": {"id": "p", "version": "1"}, "subjects": ["x"]},
        {"kind": "sanctions", "profile": {"id": "p", "version": "1"}, "subjects": [{}]},
        {"kind": "sanctions", "profile": {"id": "p", "version": "1"}, "subjects": [{"name": 5}]},
        {
            "kind": "sanctions",
            "profile": {"id": "p", "version": "1"},
            "subjects": [{"name": "abc"}],
            "limit": 0,
        },
        {
            "kind": "sanctions",
            "profile": {"id": "p", "version": "1"},
            "subjects": [{"name": "abc"}],
            "lists": [],
        },
        {
            "kind": "sanctions",
            "profile": {"id": "p", "version": "1"},
            "subjects": [{"name": "abc"}],
            "min_score": True,
        },
        {
            "kind": "sanctions",
            "profile": {"id": "p", "version": "1"},
            "subjects": [{"name": "abc"}] * 201,
        },
    ],
)
def test_run_request_contract(body: Any) -> None:
    with pytest.raises(ReviewError) as caught:
        parse_run_request(body)
    assert caught.value.status == 422


@pytest.mark.parametrize(
    "body",
    [
        None,
        {"outcome": "bestätigt", "reason": "x"},
        {"outcome": "confirmed", "reason": "x", "four_eyes": "ja"},
        {"outcome": "confirmed", "reason": "x", "expected_sequence": -1},
        {"outcome": "confirmed", "reason": "x" * 4001},
    ],
)
def test_decision_contract(body: Any) -> None:
    with pytest.raises(ReviewError):
        parse_decision(body)


def test_actor_needs_an_id() -> None:
    with pytest.raises(ValueError):
        Actor(" ")
