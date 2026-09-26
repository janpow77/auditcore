"""Framework-free handlers of the REST contract ``dataprotection_ui/1``.

Each handler takes the :class:`~.contract.Principal` of the request and the
decoded JSON body and returns JSON data (or an :class:`~.export.ExportFile`).
Library errors (:class:`~auditcore_dataprotection.errors.DataProtectionError`)
pass through; the HTTP layer maps them with :func:`~.contract.library_error`.
All rules — content check, threshold analysis, risk, proposal, four-eyes
release — are the library's; the handlers only validate the envelope.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import TypeVar, cast

from ..assessment_input import UNSET
from ..calculation import propose
from ..errors import AuthorizationError
from ..model import Assessment, RegisterVersion
from ..register_content import check_register, normalize_content
from ..report_data import assessment_report, register_report
from .backend import Backend
from .contract import (
    ApiError,
    JsonObject,
    Principal,
    body_object,
    invalid,
    revision,
    text,
    text_list,
)
from .export import EXPORT_FORMATS, ExportFile, assessment_export, register_export
from .views import assessment_view, overview_view, profile_view, register_state, version_view

_SURVEY_FIELDS = (
    "answers",
    "scenarios",
    "necessity",
    "proportionality",
    "data_subject_view",
    "dossier",
    "measure_status",
    "action_plan",
)


class _PreviewIds:
    """Placeholder identifiers for checking unsaved content."""

    def __init__(self) -> None:
        self._count = 0

    def new_id(self, kind: str) -> str:
        self._count += 1
        return f"neu-{self._count}"


_T = TypeVar("_T")


def _optional(data: Mapping[str, object], key: str, kind: type[_T]) -> _T:
    """Field of the survey or the library's ``UNSET`` (keep the stored value)."""
    if key not in data:
        return cast(_T, UNSET)
    value = data[key]
    if not isinstance(value, kind):
        raise invalid(f"'{key}' hat den falschen Typ.")
    return value


def _format(body: Mapping[str, object], allowed: tuple[str, ...]) -> str:
    fmt = body.get("format", "html")
    if fmt not in allowed:
        raise invalid(f"'format' muss einer der Werte {', '.join(allowed)} sein.")
    return str(fmt)


def _content(body: Mapping[str, object]) -> JsonObject:
    content = body.get("content")
    if not isinstance(content, Mapping):
        raise invalid("'content' muss das Verzeichnis als JSON-Objekt enthalten.")
    return dict(content)


class DataProtectionApi:
    """Handlers for register (VVT) and assessments (DSFA) of one backend."""

    def __init__(self, backend: Backend) -> None:
        self.backend = backend
        self.profile = backend.profile

    # ------------------------------------------------------------ profile

    def profile_info(self) -> JsonObject:
        """``GET /profile``."""
        return profile_view(self.profile)

    def calculate(self, body: object) -> JsonObject:
        """``POST /calculate``: proposal of the library for unsaved answers and scenarios."""
        data = body_object(body, frozenset({"answers", "scenarios"}))
        answers = data.get("answers", {})
        scenarios = data.get("scenarios", [])
        if not isinstance(answers, Mapping) or not isinstance(scenarios, list):
            raise invalid("'answers' muss ein Objekt und 'scenarios' eine Liste sein.")
        return propose(self.profile, answers, scenarios).to_dict()

    # ----------------------------------------------------------- register

    def register(self, who: Principal) -> JsonObject:
        """``GET /register``."""
        service = self.backend.registers
        draft = service.draft(who.tenant_id, who.actor)
        released = service.released(who.tenant_id, who.actor)
        history = service.history(who.tenant_id, who.actor)
        return register_state(draft, released, history, self.profile)

    def check_register(self, who: Principal, body: object) -> JsonObject:
        """``POST /register/check``: content check of unsaved content."""
        self.backend.registers.effective(who.tenant_id, who.actor)  # read permission
        content = _content(body_object(body, frozenset({"content"})))
        normalize_content(content, _PreviewIds())  # types and structure only
        # Unsaved activities have no identifier yet; like the library, the
        # issues then name the activity by its name.
        return {"issues": [i.to_dict() for i in check_register(content, self.profile)]}

    def save_draft(self, who: Principal, body: object) -> JsonObject:
        """``POST /register/draft``: create or replace the open draft."""
        data = body_object(body, frozenset({"content", "expected_revision"}))
        saved = self.backend.registers.save_draft(
            who.tenant_id,
            who.actor,
            _content(data),
            expected_revision=revision(data, required=False),
        )
        return version_view(saved, self.profile)

    def release_register(self, who: Principal, body: object) -> JsonObject:
        """``POST /register/release``: four-eyes release of the open draft."""
        data = body_object(body, frozenset({"expected_revision"}))
        expected = cast(int, revision(data))
        released = self.backend.registers.release(
            who.tenant_id, who.actor, expected_revision=expected
        )
        return version_view(released, self.profile)

    def _register_version(self, who: Principal, source: object) -> RegisterVersion:
        service = self.backend.registers
        if source not in ("draft", "released", None):
            raise invalid("'source' muss 'draft' oder 'released' sein.")
        if source == "draft":
            found = service.draft(who.tenant_id, who.actor)
        elif source == "released":
            found = service.released(who.tenant_id, who.actor)
        else:
            found = service.effective(who.tenant_id, who.actor)
        if found is None:
            raise ApiError(404, "not_found", "Es gibt keine solche Fassung des Verzeichnisses.")
        return found

    def export_register(self, who: Principal, body: object) -> ExportFile:
        """``POST /register/export``: HTML print view, Markdown or CSV."""
        data = body_object(body, frozenset({"format", "source"}))
        fmt = _format(data, EXPORT_FORMATS)
        version = self._register_version(who, data.get("source"))
        try:
            overview = self.backend.assessments.overview(who.tenant_id, who.actor)
        except AuthorizationError:
            overview = None
        return register_export(register_report(version, self.profile, overview=overview), fmt)

    # -------------------------------------------------------- assessments

    def overview(self, who: Principal, department: str | None = None) -> JsonObject:
        """``GET /assessments``: activities with the state of their newest DPIA."""
        rows = self.backend.assessments.overview(
            who.tenant_id, who.actor, department=department or None
        )
        return overview_view(rows)

    def _view(self, who: Principal, assessment: Assessment) -> JsonObject:
        service = self.backend.assessments
        versions = service.versions(
            who.tenant_id, who.actor, assessment.activity_id, assessment.register_id
        )
        return assessment_view(assessment, service, versions)

    def assessment(self, who: Principal, assessment_id: str) -> JsonObject:
        """``GET /assessments/{id}``."""
        found = self.backend.assessments.get(who.tenant_id, who.actor, assessment_id)
        return self._view(who, found)

    def start(self, who: Principal, body: object) -> JsonObject:
        """``POST /assessments``: first or next version for an activity."""
        data = body_object(body, frozenset({"activity_id"}))
        activity_id = text(data, "activity_id")
        created = self.backend.assessments.start(
            who.tenant_id, who.actor, activity_id, self.profile
        )
        return self._view(who, created)

    def update(self, who: Principal, assessment_id: str, body: object) -> JsonObject:
        """``POST /assessments/{id}``: change the survey; the library recalculates."""
        data = body_object(body, frozenset({"expected_revision", *_SURVEY_FIELDS}))
        updated = self.backend.assessments.update(
            who.tenant_id,
            who.actor,
            assessment_id,
            expected_revision=cast(int, revision(data)),
            answers=_optional(data, "answers", dict),
            scenarios=_optional(data, "scenarios", list),
            necessity=_optional(data, "necessity", str),
            proportionality=_optional(data, "proportionality", str),
            data_subject_view=_optional(data, "data_subject_view", str),
            dossier=_optional(data, "dossier", dict),
            measure_status=_optional(data, "measure_status", dict),
            action_plan=_optional(data, "action_plan", list),
        )
        return self._view(who, updated)

    def decide(self, who: Principal, assessment_id: str, body: object) -> JsonObject:
        """``POST /assessments/{id}/decide``: adopt the proposal or deviate with reasons."""
        fields = {"expected_revision", "decision", "justification", "conditions"}
        data = body_object(body, frozenset(fields))
        decided = self.backend.assessments.decide(
            who.tenant_id,
            who.actor,
            assessment_id,
            expected_revision=cast(int, revision(data)),
            decision=text(data, "decision"),
            justification=text(data, "justification", required=False),
            conditions=text_list(data, "conditions"),
        )
        return self._view(who, decided)

    def dpo_request(self, who: Principal, assessment_id: str, body: object) -> JsonObject:
        """``POST /assessments/{id}/dpo-request``: document that the DPO was asked."""
        fields = {"expected_revision", "requested_from", "requested_on"}
        data = body_object(body, frozenset(fields))
        try:
            requested_on = date.fromisoformat(text(data, "requested_on"))
        except ValueError:
            raise invalid("'requested_on' muss ein Datum JJJJ-MM-TT sein.") from None
        updated = self.backend.assessments.record_dpo_request(
            who.tenant_id,
            who.actor,
            assessment_id,
            expected_revision=cast(int, revision(data)),
            requested_from=text(data, "requested_from"),
            requested_on=requested_on,
        )
        return self._view(who, updated)

    def release(self, who: Principal, assessment_id: str, body: object) -> JsonObject:
        """``POST /assessments/{id}/release``: four-eyes release."""
        data = body_object(body, frozenset({"expected_revision"}))
        released = self.backend.assessments.release(
            who.tenant_id, who.actor, assessment_id, expected_revision=cast(int, revision(data))
        )
        return self._view(who, released)

    def reassess(self, who: Principal, assessment_id: str) -> JsonObject:
        """``POST /assessments/{id}/reassess``: new version from a released one."""
        created = self.backend.assessments.reassess(who.tenant_id, who.actor, assessment_id)
        return self._view(who, created)

    def export_assessment(self, who: Principal, assessment_id: str, body: object) -> ExportFile:
        """``POST /assessments/{id}/export``: HTML print view or Markdown."""
        data = body_object(body, frozenset({"format"}))
        fmt = _format(data, ("html", "markdown"))
        found = self.backend.assessments.get(who.tenant_id, who.actor, assessment_id)
        return assessment_export(assessment_report(found, self.profile), fmt)
