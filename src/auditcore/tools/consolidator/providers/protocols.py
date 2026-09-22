"""Replaceable infrastructure interfaces; no provider in the domain core."""

from pathlib import Path
from typing import Any, Protocol

from auditcore.tools.consolidator.models import RepositoryRecord


class RepositoryProvider(Protocol):
    """Authenticated source-of-code provider."""

    def repositories(self) -> list[RepositoryRecord]:
        """List every visible repository with pagination."""
        ...

    def checkout(self, repository: RepositoryRecord) -> Path:
        """Materialize immutable source for analysis."""
        ...


class InventoryProvider(Protocol):
    """Persistent inventory contract."""

    def load(self, name: str) -> Any:
        """Read a catalog."""
        ...

    def save(self, name: str, data: Any) -> None:
        """Persist a catalog."""
        ...


class DependencyGraphProvider(Protocol):
    """Structural graph extraction contract."""

    def analyze(self, path: Path) -> dict[str, Any]:
        """Return graph evidence or explicit nonexecution."""
        ...


class KnowledgeStore(Protocol):
    """Versioned knowledge storage contract."""

    def sync(self, documents: list[dict[str, Any]]) -> dict[str, Any]:
        """Store screened structured observations."""
        ...

    def search(self, query: str) -> dict[str, Any]:
        """Search current knowledge without implying code absence."""
        ...


class SemanticAnalysisProvider(Protocol):
    """Semantic suggestions never authorize business-rule changes."""

    def compare(self, symbols: list[dict[str, Any]]) -> dict[str, Any]:
        """Return classified and source-linked semantic observations."""
        ...
