"""OpenSanctions matching API (``/match/{dataset}``) for sanctions and PEP checks.

Source: flowsearch ``SanctionsAPIClient`` and ``PEPScreeningAPIClient``.
Verified on 2026-09-23 against the published OpenAPI description (yente
5.5.0): the API requires a key in ``Authorization: ApiKey …`` and answers
``responses.<query>.results[]`` with entities that carry ``score``,
``properties.topics`` and ``datasets`` directly — there is no ``entity``
wrapper. flowsearch sends no key (sanctions) or ``Bearer`` (PEP) and reads
``result.entity``; with the documented response it never finds anything.

This module builds requests, calls the API through an injected
``auditcore_harvest`` transport and interprets responses under the
explicit profiles ``flowsearch.opensanctions_match`` and ``flowsearch.pep_risk``.
Errors are raised (``AuthError``, ``RateLimitError``, ``TransportError``,
``ParserError``); a failed check is never reported as "no hit".
"""

from __future__ import annotations

from ._opensanctions_assessment import (
    PepAssessment,
    PepMatch,
    Position,
    SanctionsAssessment,
    assess_pep,
    assess_sanctions,
    pep_category,
    pep_risk,
    pep_type,
    positions,
)
from ._opensanctions_match import Candidate, MatchClient, MatchResponse, parse_response
from ._opensanctions_query import (
    BASE_URL,
    ENV_VAR,
    KEY_INFO_URL,
    NOT_CONFIGURED,
    SOURCE_ID,
    KeyCredentials,
    MatchQuery,
    build_request,
    configuration_status,
    credentials_from_environment,
    person_query,
    sanctions_query,
)

__all__ = [
    "BASE_URL",
    "ENV_VAR",
    "KEY_INFO_URL",
    "NOT_CONFIGURED",
    "SOURCE_ID",
    "Candidate",
    "KeyCredentials",
    "MatchClient",
    "MatchQuery",
    "MatchResponse",
    "PepAssessment",
    "PepMatch",
    "Position",
    "SanctionsAssessment",
    "assess_pep",
    "assess_sanctions",
    "build_request",
    "configuration_status",
    "credentials_from_environment",
    "parse_response",
    "pep_category",
    "pep_risk",
    "pep_type",
    "person_query",
    "positions",
    "sanctions_query",
]
