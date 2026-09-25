"""Match API answers and the client that requests them through an injected transport."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from auditcore_harvest import (
    AuthError,
    CredentialProvider,
    ParserError,
    Transport,
    raise_for_status,
)

from ._opensanctions_query import (
    BASE_URL,
    NOT_CONFIGURED,
    SOURCE_ID,
    KeyCredentials,
    MatchQuery,
    build_request,
    configuration_status,
)
from ._types import JsonObject


@dataclass(frozen=True)
class Candidate:
    """A scored entity of the API answer."""

    id: str
    caption: str
    schema: str
    score: float
    api_match: bool | None
    datasets: tuple[str, ...]
    topics: tuple[str, ...]
    properties: Mapping[str, Any]
    first_seen: str | None
    last_seen: str | None
    last_change: str | None

    def first(self, prop: str) -> str:
        """First value of a property or ``""``."""
        values = self.properties.get(prop) or []
        return str(values[0]) if values else ""

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "id": self.id,
            "caption": self.caption,
            "schema": self.schema,
            "score": self.score,
            "api_match": self.api_match,
            "datasets": list(self.datasets),
            "topics": list(self.topics),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "last_change": self.last_change,
        }


@dataclass(frozen=True)
class MatchResponse:
    """Answer to one query of a match request."""

    query_key: str
    status: int
    total: int | None
    candidates: tuple[Candidate, ...]


def parse_response(body: bytes) -> dict[str, MatchResponse]:
    """Interpret a ``/match`` answer; missing required parts are parser errors."""
    try:
        data = json.loads(body)
        responses = data["responses"]
        if not isinstance(responses, dict):
            raise TypeError("responses")
        result = {}
        for key, answer in responses.items():
            candidates = []
            for item in answer["results"]:
                props = item.get("properties") or {}
                candidates.append(
                    Candidate(
                        id=str(item["id"]),
                        caption=str(item.get("caption", "")),
                        schema=str(item.get("schema", "")),
                        score=float(item["score"]),
                        api_match=item.get("match"),
                        datasets=tuple(item.get("datasets") or ()),
                        topics=tuple(props.get("topics") or ()),
                        properties=props,
                        first_seen=item.get("first_seen"),
                        last_seen=item.get("last_seen"),
                        last_change=item.get("last_change"),
                    )
                )
            total = answer.get("total") or {}
            result[key] = MatchResponse(
                query_key=key,
                status=int(answer.get("status", 200)),
                total=int(total["value"]) if "value" in total else None,
                candidates=tuple(candidates),
            )
        return result
    except (ValueError, KeyError, TypeError) as exc:
        raise ParserError(f"Antwort der Abgleichs-API nicht lesbar: {exc!r}") from exc


class MatchClient:
    """Calls ``/match/{dataset}`` through an injected transport; the key comes from credentials."""

    def __init__(
        self,
        transport: Transport,
        credentials: CredentialProvider | None = None,
        *,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        self.transport = transport
        self.credentials = credentials if credentials is not None else KeyCredentials(api_key)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @property
    def status(self) -> str:
        """``CONFIGURED`` or ``NOT_CONFIGURED``."""
        return configuration_status(self.credentials)

    def match(
        self,
        queries: Mapping[str, MatchQuery],
        *,
        dataset: str = "default",
        threshold: float | None = None,
        limit: int | None = None,
    ) -> dict[str, MatchResponse]:
        """Send one request; raises harvest errors instead of returning empty results."""
        key = self.credentials.get(SOURCE_ID, "api_key")
        if not key:
            raise AuthError(NOT_CONFIGURED)
        params: dict[str, str] = {}
        if threshold is not None:
            params["threshold"] = str(threshold)
        if limit is not None:
            params["limit"] = str(limit)
        response = self.transport.request(
            "POST",
            f"{self.base_url}/match/{dataset}",
            params=params or None,
            headers={"Authorization": f"ApiKey {key}", "Content-Type": "application/json"},
            data=build_request(queries),
            timeout=self.timeout,
        )
        raise_for_status(response)
        return parse_response(response.body)
