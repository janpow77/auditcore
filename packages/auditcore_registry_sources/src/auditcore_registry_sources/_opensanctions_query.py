"""Credentials, configuration status and request bodies of the matching API."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from auditcore_harvest import CredentialProvider

from ._types import JsonObject

SOURCE_ID = "registry.opensanctions_match"
BASE_URL = "https://api.opensanctions.org"
#: Environment variable a consumer may use for its own key (decision A3, 23.09.2026).
ENV_VAR = "OPENSANCTIONS_API_KEY"
#: Where an operator obtains a key (free for academia, non-profits and journalism).
KEY_INFO_URL = "https://www.opensanctions.org/api/"
NOT_CONFIGURED = (
    "NOT_CONFIGURED: kein OpenSanctions-API-Schlüssel. Jeder Betreiber beschafft einen "
    f"eigenen Schlüssel ({KEY_INFO_URL}) und übergibt ihn als Parameter api_key oder über "
    f"die Umgebungsvariable {ENV_VAR} (credentials_from_environment)."
)


@dataclass(frozen=True)
class KeyCredentials:
    """Credential provider holding one operator key for the matching API."""

    api_key: str | None

    def get(self, source_id: str, name: str) -> str | None:
        """The key for this source, else ``None``."""
        if source_id == SOURCE_ID and name == "api_key" and self.api_key:
            return self.api_key
        return None


def credentials_from_environment(environ: Mapping[str, str]) -> KeyCredentials:
    """Key from ``environ[ENV_VAR]`` (pass ``os.environ``); empty values count as missing."""
    value = (environ.get(ENV_VAR) or "").strip()
    return KeyCredentials(value or None)


def configuration_status(credentials: CredentialProvider) -> str:
    """``CONFIGURED`` or ``NOT_CONFIGURED`` without revealing the key."""
    return "CONFIGURED" if credentials.get(SOURCE_ID, "api_key") else "NOT_CONFIGURED"


@dataclass(frozen=True)
class MatchQuery:
    """One entity example of a match request."""

    schema: str
    properties: Mapping[str, Sequence[str]]

    def to_dict(self) -> JsonObject:
        """JSON view of the query."""
        return {
            "schema": self.schema,
            "properties": {k: list(v) for k, v in self.properties.items() if v},
        }


def sanctions_query(name: str, country: str | None) -> MatchQuery:
    """flowsearch sanctions request: ``LegalEntity`` with name and country."""
    properties: dict[str, list[str]] = {"name": [name]}
    if country:
        properties["country"] = [country]
    return MatchQuery("LegalEntity", properties)


def person_query(
    name: str, *, birth_date: str | None = None, nationality: str | None = None
) -> MatchQuery:
    """flowsearch PEP request: ``Person`` with optional birth date and nationality."""
    properties: dict[str, list[str]] = {"name": [name]}
    if birth_date:
        properties["birthDate"] = [birth_date]
    if nationality:
        properties["nationality"] = [nationality]
    return MatchQuery("Person", properties)


def build_request(queries: Mapping[str, MatchQuery]) -> bytes:
    """JSON body ``{"queries": {...}}``."""
    if not queries:
        raise ValueError("Mindestens eine Abfrage ist nötig.")
    body = {"queries": {key: q.to_dict() for key, q in queries.items()}}
    return json.dumps(body, ensure_ascii=False).encode("utf-8")
