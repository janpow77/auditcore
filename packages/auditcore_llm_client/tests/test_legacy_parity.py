"""Replay every recorded legacy case against the library (sync and async).

Requests must be identical (method, URL, relevant headers, body). Results must
match field by field; errors must carry the same status code. Deliberate
deviations are listed in ``DEVIATIONS`` and documented in
``docs/behavior-changes.md``.
"""

from __future__ import annotations

import pytest
from conftest import KEY, Gateway, call_library, load_observed, plain

from auditcore_llm_client import (
    LlmClientError,
    NotAssignedError,
    RouterHealth,
    UsageRecord,
    config_from_env,
    get_profile,
)

OBSERVED = load_observed()
GROUPS: list[dict[str, object]] = OBSERVED["groups"]  # type: ignore[assignment]
CASES = [(g, c) for g in GROUPS for c in g["cases"]]  # type: ignore[attr-defined]

#: Case id → reason. Everything else must behave exactly like the legacy client.
DEVIATIONS = {
    "ck-stream-http-500": "B7: HTTP-Fehler im Stream wird als Exception gemeldet",
    "ck-stream-unreachable": "B7: Transportfehler im Stream wird als Exception gemeldet",
}
#: audit_designer ``health()`` dropped the status code; the library always keeps it.
STATUS_ADDED = {"ad-health-503"}
LLM_FIELDS = ("content", "model", "input_tokens", "output_tokens", "latency_ms", "raw_response")


def _ids(item: tuple[dict[str, object], dict[str, object]]) -> str:
    return str(item[1]["id"])


def _config(group: dict[str, object], usage: list[UsageRecord]) -> object:
    config = config_from_env(get_profile(str(group["profile"])), group["env"])  # type: ignore[arg-type]
    import dataclasses

    return dataclasses.replace(config, usage_hook=usage.append)


def _compare_result(case: dict[str, object], actual: object) -> None:
    expected = case["result"]
    op = str(case["library"]["fn"])  # type: ignore[index]
    if op in {"generate", "chat"}:
        if isinstance(expected, str):
            assert actual.content == expected  # type: ignore[attr-defined]
            return
        for field in LLM_FIELDS:
            assert getattr(actual, field) == expected[field], field  # type: ignore[index]
        return
    if op.startswith("safe:"):
        assert actual[0] is None and expected[0] is None  # type: ignore[index]
        assert KEY not in actual[1]  # type: ignore[index]
        return
    got = plain(actual)
    if isinstance(got, dict):
        got.pop("degraded", None)
    assert got == expected


def _compare_error(case: dict[str, object], error: LlmClientError) -> None:
    expected = case.get("error")
    assert KEY not in str(error) and KEY not in repr(error.args)
    assert error.__cause__ is None
    if expected is None:
        assert case["id"] in DEVIATIONS
        return
    if case["id"] in STATUS_ADDED:
        assert expected["status_code"] is None and error.status_code is not None  # type: ignore[index]
    else:
        assert error.status_code == expected["status_code"]  # type: ignore[index]
    if "not-assigned" in str(case["id"]):
        assert isinstance(error, NotAssignedError)


def _compare_usage(case: dict[str, object], usage: list[UsageRecord]) -> None:
    expected = case["usage"]
    if not expected:
        return
    assert [
        {"prompt_tokens": u.prompt_tokens, "completion_tokens": u.completion_tokens,
         "gpu_time_ms": u.latency_ms, "model_name": u.model}
        for u in usage
    ] == expected


@pytest.mark.parametrize("variant", ["sync", "async"])
@pytest.mark.parametrize(("group", "case"), CASES, ids=[_ids(c) for c in CASES])
def test_case_matches_legacy(group: dict[str, object], case: dict[str, object],
                             variant: str) -> None:
    gateway = Gateway(case["responses"])  # type: ignore[arg-type]
    usage: list[UsageRecord] = []
    health = RouterHealth()
    config = _config(group, usage)
    try:
        actual = call_library(config, gateway, case["library"], variant, health=health)  # type: ignore[arg-type]
    except LlmClientError as error:
        _compare_error(case, error)
        assert "error" in case or case["id"] in DEVIATIONS
    else:
        assert "error" not in case, "Bibliothek wirft nicht, Altclient schon"
        _compare_result(case, actual)
    assert gateway.requests == case["requests"]
    assert len(gateway.responses) == case["unused_responses"]
    _compare_usage(case, usage)
    record = health.to_dict()
    assert KEY not in str(record)
    failed = "error" in case or str(case["library"]["fn"]).startswith("safe:")  # type: ignore[index]
    failed = failed or case["id"] in DEVIATIONS
    result = case.get("result")
    if isinstance(result, dict) and "state" in result:
        failed = result["state"] not in {"ok", "empty"}
    assert record["consecutive_failures"] == (1 if failed else 0)


def test_every_group_is_bound_to_a_pinned_source() -> None:
    sources = {(g["source"]["repository"], g["source"]["commit"]) for g in GROUPS}  # type: ignore[index]
    assert sources == {
        ("janpow77/audit_designer", "ccd65245182982af3ef885a7a6d43583f4f72cbb"),
        ("janpow77/flowinvoice", "fb2d18568d2eaf64574d131ceae51a936b9aac02"),
        ("janpow77/audit-portal", "d8eefa426826bdecb67036774f3128ae05e7d0d0"),
        ("janpow77/cockpit", "df203d4c33e786eb8a8ad3fe53b3b7eb9241d406"),
    }
    assert len(CASES) == 60


def test_legacy_key_leaks_are_recorded() -> None:
    """The observation behind the security finding: legacy clients leak the key."""
    leaking = sorted(
        str(c["id"]) for _, c in CASES
        if (c.get("error") or {}).get("key_in_message")  # type: ignore[union-attr]
        or c.get("key_in_result") or c.get("key_in_logs")
        or (c.get("health") or {}).get("key_in_health")  # type: ignore[union-attr]
    )
    assert leaking == [
        "ad-generate-key-echo", "ad-generate-unreachable", "ad-safe-llm-key-echo",
        "ck-stream-http-500", "ck-stream-unreachable", "fi-embed-unreachable",
        "fi-safe-llm-key-echo",
    ]
