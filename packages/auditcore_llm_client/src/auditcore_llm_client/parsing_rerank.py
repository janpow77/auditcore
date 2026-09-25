"""Reranker answers: ``{"scores": [...]}`` (``/v1/rerank``) or ``{"results": [...]}``.

audit_designer prefers ``results`` when the key is present, flowinvoice prefers
``scores`` – the profile's rerank route decides. A score list of the wrong
length is replaced by zeros as before, but the result is marked ``degraded``.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from auditcore_llm_client.errors import InvalidResponseError
from auditcore_llm_client.jsontypes import (
    JsonObject,
    JsonValue,
    as_int,
    as_list,
    as_object,
    as_text,
    strict_number,
)
from auditcore_llm_client.received import ReceivedResponse
from auditcore_llm_client.results import RerankResult, RerankScore

log = logging.getLogger("auditcore_llm_client")


def _entry(item: JsonValue) -> RerankScore | None:
    entry = as_object(item)
    try:
        index = int(strict_number(entry.get("index")))
        score = strict_number(entry.get("score", 0.0))
    except ValueError:
        return None
    document = entry.get("document")
    return RerankScore(index, score, document if isinstance(document, str) else None)


def _from_results(data: JsonObject, count: int) -> tuple[list[float], list[RerankScore]]:
    scores = [0.0] * count
    results: list[RerankScore] = []
    for item in as_list(data.get("results")):
        entry = _entry(item)
        if entry is None:
            continue
        if 0 <= entry.index < count:
            scores[entry.index] = entry.score
        results.append(entry)
    return scores, results


def _from_scores(raw: list[JsonValue], documents: Sequence[str],
                 path: str) -> tuple[list[float], list[RerankScore], bool]:
    try:
        scores = [strict_number(s) for s in raw]
    except ValueError:
        raise InvalidResponseError(f"{path}: ungültiger Score", endpoint=path) from None
    degraded = len(scores) != len(documents)
    if degraded:
        log.error("%s: %d Scores für %d Dokumente – Null-Scores", path, len(raw), len(documents))
        scores = [0.0] * len(documents)
    pairs = [RerankScore(i, s, documents[i]) for i, s in enumerate(scores)]
    return scores, pairs, degraded


def parse_rerank(received: ReceivedResponse, documents: Sequence[str], model: str,
                 prefer_results: bool) -> RerankResult:
    """Map either answer form onto input order; ``prefer_results`` = audit_designer rule."""
    data = as_object(received.json())
    use_results = "results" in data if prefer_results else data.get("scores") is None
    degraded = False
    if use_results:
        scores, results = _from_results(data, len(documents))
    else:
        scores, results, degraded = _from_scores(
            as_list(data.get("scores")), documents, received.path
        )
    return RerankResult(
        scores=scores,
        results=results,
        model=as_text(data.get("model"), model),
        spoke=as_text(data.get("spoke")),
        duration_ms=as_int(data.get("duration_ms")),
        degraded=degraded,
    )
