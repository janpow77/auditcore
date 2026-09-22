"""Regelkonfiguration / Versioned caller-supplied rules, without invented law."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RuleSetMetadata:
    """Regelstand / Provenance and effective date of supplied rules."""

    name: str
    version: str
    source: str
    effective_from: str


@dataclass(frozen=True)
class RuleSet:
    """Regelsatz / Immutable named decimal parameters."""

    metadata: RuleSetMetadata
    parameters: tuple[tuple[str, Decimal], ...]

    def value(self, name: str) -> Decimal:
        """Wert / Return a named value; raise KeyError for an absent rule."""
        return dict(self.parameters)[name]
