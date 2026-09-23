"""OpenSanctions matching API: documented shape, key handling, no silent failures."""

from __future__ import annotations

import json
from typing import Any

import pytest
from auditcore_harvest import AuthError, ParserError, RateLimitError, Response
from auditcore_harvest.memory import StaticCredentials
from replay_support import FILES

from auditcore_registry_sources import (
    MatchClient,
    assess_pep,
    assess_sanctions,
    load_profile,
    parse_response,
    person_query,
    sanctions_query,
)

MATCH = load_profile("flowsearch.opensanctions_match", "2026.09.1")
PEP = load_profile("flowsearch.pep_risk", "2026.09.1")


class Recorder:
    def __init__(self, status: int, body: bytes, headers: dict[str, str] | None = None) -> None:
        self.status, self.body, self.headers = status, body, headers or {}
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        self.calls.append({"method": method, "url": url, **kwargs})
        return Response(self.status, self.body, self.headers, url)


def test_documented_shape_is_read() -> None:
    answer = parse_response((FILES / "opensanctions_match_sanctions.json").read_bytes())["entity1"]
    assert answer.total == 4 and len(answer.candidates) == 4
    result = assess_sanctions(answer, MATCH)
    assert result.found and [m.id for m in result.matches] == ["NK-demo1", "NK-demo2"]
    assert result.below_threshold == 1 and result.without_sanction_topic == 1
    pep = assess_pep(
        parse_response((FILES / "opensanctions_match_pep.json").read_bytes())["entity1"], PEP
    )
    assert pep.is_pep and pep.category == "PEP (aktiv)" and pep.risk_level == "high"
    assert [(m.pep_type, m.risk) for m in pep.matches] == [
        ("PEP (aktiv)", "high"),
        ("Former PEP", "medium"),
        ("RCA (Relative/Close Associate)", "medium"),  # 0.78 lies in the medium band
        ("Unknown", "medium"),
    ]
    assert pep.decisions


def test_client_sends_api_key_header_and_body() -> None:
    transport = Recorder(200, (FILES / "opensanctions_match_sanctions.json").read_bytes())
    client = MatchClient(
        transport, StaticCredentials({("registry.opensanctions_match", "api_key"): "k-123"})
    )
    answers = client.match({"entity1": sanctions_query("Müller GmbH", "DE")}, threshold=0.7)
    call = transport.calls[0]
    assert call["method"] == "POST" and call["url"].endswith("/match/default")
    assert call["headers"]["Authorization"] == "ApiKey k-123"
    assert call["params"] == {"threshold": "0.7"}
    body = json.loads(call["data"])
    assert body == {
        "queries": {
            "entity1": {
                "schema": "LegalEntity",
                "properties": {"name": ["Müller GmbH"], "country": ["DE"]},
            }
        }
    }
    assert answers["entity1"].candidates[0].caption.startswith("Müller")
    assert person_query("A", birth_date="1980", nationality="at").to_dict()["properties"] == {
        "name": ["A"],
        "birthDate": ["1980"],
        "nationality": ["at"],
    }


def test_missing_key_rejected_answers_and_bad_bodies_are_errors() -> None:
    client = MatchClient(Recorder(200, b"{}"), StaticCredentials({}))
    with pytest.raises(AuthError, match="NOT_CONFIGURED"):
        client.match({"q": sanctions_query("x", None)})
    creds = StaticCredentials({("registry.opensanctions_match", "api_key"): "k"})
    with pytest.raises(AuthError):
        MatchClient(Recorder(401, b'{"detail":"No API key provided."}'), creds).match(
            {"q": sanctions_query("x", None)}
        )
    with pytest.raises(RateLimitError):
        MatchClient(Recorder(429, b"", {"Retry-After": "5"}), creds).match(
            {"q": sanctions_query("x", None)}
        )
    with pytest.raises(ParserError):
        MatchClient(Recorder(200, b'{"responses": {"q": {}}}'), creds).match(
            {"q": sanctions_query("x", None)}
        )
    with pytest.raises(ValueError):
        MatchClient(Recorder(200, b"{}"), creds).match({})


def test_legacy_wrapped_shape_is_not_the_api() -> None:
    with pytest.raises(ParserError):
        parse_response((FILES / "opensanctions_match_sanctions_wrapped.json").read_bytes())
