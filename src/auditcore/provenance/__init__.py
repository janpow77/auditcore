"""Herkunft / Source attribution for migrated domain logic."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceReference:
    """Quellbeleg / Exact repository, revision and symbol identity."""

    repository: str
    path: str
    symbol: str
    revision: str


@dataclass(frozen=True)
class ProvenanceRecord:
    """Migration / Multiple origins and the migration version."""

    target_symbol: str
    sources: tuple[SourceReference, ...]
    migration_version: str
    characterization_reference: str
    license_reference: str
