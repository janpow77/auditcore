"""Einstieg der Prüfung: :func:`validate`."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

from ..model import BpmnDocument, as_document
from ..profiles import Profile
from . import audit_authority, content, segregation, structure  # noqa: F401 - registriert die Regeln
from .context import ValidationConfig, ValidationContext
from .issues import ValidationReport
from .registry import run


def validate(
    source: str | bytes | BpmnDocument,
    config: ValidationConfig | None = None,
    *,
    reference_date: date | None = None,
    profile: Profile | None = None,
) -> ValidationReport:
    """Prüft ein Diagramm (XML oder Modell) gegen alle registrierten Regeln.

    Die Kataloge stammen aus dem Profil des Diagramms (Feld ``profil`` der
    Diagramm-Infos, sonst die Förderperiode, sonst ``foerderperiode-2021-2027``);
    ``profile`` bzw. ``config.profile`` erzwingt ein Profil.
    """
    config = config or ValidationConfig()
    if reference_date is not None:
        config = replace(config, reference_date=reference_date)
    if profile is not None:
        config = replace(config, profile=profile)
    context = ValidationContext.create(as_document(source), config)
    return ValidationReport(
        issues=tuple(run(context)),
        profile=context.profile.reference,
        profile_origin=context.profile_origin,
        reference_date=context.reference_date.isoformat(),
    )
