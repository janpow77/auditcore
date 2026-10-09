"""Review package (Prüfpaket) of one activity: what is submitted, in which state.

The package shows status, version and scope on its first page: "submitted for
review" never reads as "released", and a released documentation never reads as
an operational decision (catalogue 10.3). It is an internal export; the public
pattern lives in :mod:`.publication`.
"""

from __future__ import annotations

from typing import cast

from .model import DEFAULT_REGISTER, Actor
from .publication import ExportProfile
from .report_data import assessment_report
from .rules import load_profile
from .status import STATUS_LABELS, DocumentationStatus
from .workspace import ActivityWorkspace

PACKAGE_SCHEMA = "auditcore_dataprotection.review_package/1"
NOTICE = (
    "Arbeitsunterlage zur Prüfung. Sie ist weder eine Freigabe der Verarbeitung noch ein "
    "Nachweis ihrer Rechtmäßigkeit; maßgeblich sind die getrennt ausgewiesenen Status und "
    "die Entscheidung der zuständigen Stelle."
)


def review_package(
    workspace: ActivityWorkspace,
    tenant_id: str,
    actor: Actor,
    activity_id: str,
    *,
    register_id: str = DEFAULT_REGISTER,
) -> dict[str, object]:
    """Register entry, screening, DPIA, gates, checklist and statements of one activity."""
    overview = workspace.overview(tenant_id, actor, activity_id, register_id=register_id)
    evaluation = workspace.evaluate(tenant_id, actor, activity_id, register_id=register_id)
    working = workspace.working(tenant_id, actor, register_id)
    activity = next(a for a in working.activities if a.get("id") == activity_id)
    assessment = evaluation.assessment
    dpia = None
    if assessment is not None:
        rules = load_profile(assessment.profile_id, assessment.profile_version)
        dpia = assessment_report(assessment, rules)
    status = cast(dict[str, str], overview["status"])
    wizard = cast(dict[str, object], overview["assistent"])
    documentation = DocumentationStatus(status["dokumentation"])
    return {
        "schema": PACKAGE_SCHEMA,
        "art": ExportProfile.REVIEW_PACKAGE.value,
        "hinweis": NOTICE,
        "stand": {
            "bezeichnung": STATUS_LABELS[documentation],
            "register": overview["register"],
            "profil": overview["profil"],
            "fragenkatalog": wizard["catalog_version"],
            "geltungsbereich": {
                "taetigkeit": activity.get("name"),
                "umgebung": activity.get("umgebung"),
                "anwendungen": activity.get("anwendungen"),
            },
        },
        "status": overview["status"],
        "sperren": overview["sperren"],
        "taetigkeit": dict(activity),
        "pruefpunkte": overview["pruefpunkte"],
        "offene_aufgaben": overview["offene_aufgaben"],
        "folgenabschaetzung": dpia,
    }
