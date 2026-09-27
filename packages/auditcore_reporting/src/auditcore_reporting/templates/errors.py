"""Errors of the report template engine; all messages are German and name the location."""

from __future__ import annotations

from dataclasses import dataclass


class TemplateError(ValueError):
    """A template definition is invalid (schema, blocks, placeholders, conditions)."""


class TemplateNotFoundError(LookupError):
    """No template with this id (and version) is registered."""


class UnsafeDocumentError(ValueError):
    """A DOCX template contains macros, external content or exceeds a resource limit."""


class RenderDependencyError(RuntimeError):
    """The optional renderer extra for the requested format is not installed."""


class RenderLimitError(ValueError):
    """Rendering would exceed an explicit resource limit."""


@dataclass(frozen=True)
class Issue:
    """One data problem: JSON path (``$.feststellungen[0].betrag``) and German message."""

    path: str
    message: str

    def to_dict(self) -> dict[str, str]:
        """JSON form for the REST contract."""
        return {"path": self.path, "message": self.message}


class TemplateDataError(ValueError):
    """The data do not satisfy the data contract (JSON schema) of the template."""

    def __init__(self, issues: tuple[Issue, ...]) -> None:
        self.issues = issues
        first = issues[0] if issues else Issue("$", "unbekannter Fehler")
        more = f" (und {len(issues) - 1} weitere)" if len(issues) > 1 else ""
        super().__init__(f"Daten passen nicht zur Vorlage: {first.path}: {first.message}{more}")
