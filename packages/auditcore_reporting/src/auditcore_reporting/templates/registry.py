"""Registry of versioned templates; built-in templates are package data."""

from __future__ import annotations

import json
from collections.abc import Iterable
from importlib import resources

from .definition import define_template
from .errors import TemplateError, TemplateNotFoundError
from .model import ReportTemplate

BUILTIN = ("vermerk-1.0.0.json", "pruefbericht-1.0.0.json")


def _key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


class TemplateRegistry:
    """Templates by id and version; a registered version is never replaced."""

    def __init__(self, templates: Iterable[ReportTemplate] = ()) -> None:
        self._templates: dict[tuple[str, str], ReportTemplate] = {}
        for template in templates:
            self.register(template)

    def register(self, template: ReportTemplate) -> None:
        """Add a template; the same id and version with other content is rejected."""
        key = (template.id, template.version)
        known = self._templates.get(key)
        if known is not None and known.fingerprint != template.fingerprint:
            raise TemplateError(
                f"{template.id} {template.version} ist bereits mit anderem Inhalt registriert; "
                "Änderungen brauchen eine neue Version."
            )
        self._templates[key] = template

    def versions(self, template_id: str) -> tuple[str, ...]:
        """All versions of a template, oldest first."""
        found = [version for tid, version in self._templates if tid == template_id]
        return tuple(sorted(found, key=_key))

    def get(self, template_id: str, version: str | None = None) -> ReportTemplate:
        """A version, or the newest version that is not archived."""
        if version is not None:
            template = self._templates.get((template_id, version))
            if template is None:
                raise TemplateNotFoundError(
                    f"Vorlage {template_id} {version} ist nicht registriert."
                )
            return template
        active = [
            self._templates[(template_id, v)]
            for v in self.versions(template_id)
            if self._templates[(template_id, v)].status != "Archiviert"
        ]
        if not active:
            raise TemplateNotFoundError(f"Vorlage {template_id!r} ist nicht registriert.")
        return active[-1]

    def latest(self) -> tuple[ReportTemplate, ...]:
        """Newest non-archived version of every template, sorted by id."""
        ids = sorted({tid for tid, _ in self._templates})
        result = []
        for template_id in ids:
            try:
                result.append(self.get(template_id))
            except TemplateNotFoundError:
                continue
        return tuple(result)


def builtin_definitions() -> tuple[dict[str, object], ...]:
    """JSON definitions of the built-in, authority-neutral templates."""
    folder = resources.files("auditcore_reporting.templates") / "builtin"
    return tuple(json.loads((folder / name).read_text(encoding="utf-8")) for name in BUILTIN)


def builtin_registry() -> TemplateRegistry:
    """Registry with the built-in templates ``vermerk`` and ``pruefbericht``."""
    return TemplateRegistry(define_template(definition) for definition in builtin_definitions())
