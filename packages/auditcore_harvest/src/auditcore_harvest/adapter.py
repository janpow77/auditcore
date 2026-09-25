"""Adapter interface: one source profile, one bounded page per call.

An adapter translates a source into :class:`HarvestRecord` objects. It never
loops over pages, sleeps, retries, writes checkpoints or stores data; the
:class:`~auditcore_harvest.engine.HarvestEngine` does that for every adapter.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, TypeVar, runtime_checkable

from .errors import AuthError, ConfigError
from .model import (
    JSON,
    Cursor,
    HarvestRecord,
    HarvestRequest,
    PageResult,
    Provenance,
    Source,
    canonical_hash,
)
from .ports import Clock, CredentialProvider, Transport

T = TypeVar("T")


@dataclass(frozen=True)
class FetchContext:
    """Everything an adapter may use for one page."""

    request: HarvestRequest
    config: Mapping[str, JSON]
    transport: Transport
    credentials: CredentialProvider
    clock: Clock
    timeout: float
    page: int

    def secret(self, source_id: str, name: str) -> str:
        """Required secret from the credential provider or ``AuthError``."""
        value = self.credentials.get(source_id, name)
        if not value:
            raise AuthError(f"Zugangsdaten '{name}' für {source_id} sind nicht konfiguriert.")
        return value

    def provenance(self, source: Source, locator: str, raw: JSON) -> Provenance:
        """Provenance of a record from this page."""
        return Provenance(
            source_id=source.source_id,
            adapter_version=source.adapter_version,
            profile_version=source.profile_version,
            retrieved_at=self.clock.now().isoformat(),
            locator=locator,
            raw_sha256=canonical_hash(raw),
        )

    def record(
        self,
        source: Source,
        record_id: str,
        raw: JSON,
        normalized: Mapping[str, JSON],
        locator: str,
        *,
        deleted: bool = False,
    ) -> HarvestRecord:
        """Record of ``source`` from this page with provenance over ``raw``."""
        return HarvestRecord(
            source_id=source.source_id,
            record_id=record_id,
            raw=raw,
            normalized=normalized,
            provenance=self.provenance(source, locator, raw),
            deleted=deleted,
        )


@runtime_checkable
class SourceAdapter(Protocol):
    """Contract every source adapter implements (contract version 1)."""

    @property
    def source(self) -> Source:
        """Declared source identity and capabilities."""
        ...

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        """Raise :class:`ConfigError` for invalid configuration; never contact the source."""
        ...

    def fetch_page(self, context: FetchContext, cursor: Cursor | None) -> PageResult:
        """Fetch exactly one page and return a :class:`~auditcore_harvest.model.PageResult`."""
        ...


class AdapterRegistry:
    """Explicit registration; no import-time discovery or plugin magic."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], SourceAdapter]] = {}

    def register(self, source_id: str, factory: Callable[[], SourceAdapter]) -> None:
        """Register a factory; a source id can only be registered once."""
        if source_id in self._factories:
            raise ConfigError(f"Quelle '{source_id}' ist bereits registriert.")
        self._factories[source_id] = factory

    def create(self, source_id: str) -> SourceAdapter:
        """New adapter instance; its declared id must match the registration."""
        try:
            adapter = self._factories[source_id]()
        except KeyError as exc:
            raise ConfigError(f"Keine Quelle '{source_id}' registriert.") from exc
        if adapter.source.source_id != source_id:
            raise ConfigError("Registrierte und deklarierte Quellenkennung weichen ab.")
        return adapter

    def sources(self) -> tuple[str, ...]:
        """Registered source ids, sorted."""
        return tuple(sorted(self._factories))


def require(config: Mapping[str, JSON], name: str, kind: type[T]) -> T:
    """Small helper for ``validate_config``: required key of a given type."""
    value = config.get(name)
    if not isinstance(value, kind) or isinstance(value, bool) and kind is not bool:
        raise ConfigError(f"Konfiguration '{name}' fehlt oder hat den falschen Typ.")
    return value
