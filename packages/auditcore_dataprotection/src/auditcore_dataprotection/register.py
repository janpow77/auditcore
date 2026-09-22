"""Records of processing activities: content checks, identifiers, versions, release.

A register version is a JSON document with a cover sheet (``deckblatt``),
departments (``referate``) and activities (``taetigkeiten``), using the field
names of the source application. Drafts are replaced only with the revision
that was read; releases require a second person who did not edit the draft.
Released versions are never changed; a new draft becomes the next version.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from .calculation import Issue
from .errors import (
    AuthorizationError,
    ConflictError,
    FourEyesViolation,
    NotFoundError,
    StaleRevisionError,
    TenantMismatchError,
    ValidationError,
)
from .legacy import legacy_activities_with_identifiers
from .model import DEFAULT_REGISTER, Actor, AuditEvent, Permission, RegisterStatus, RegisterVersion
from .ports import AuditSink, Authorizer, Clock, IdFactory, RegisterRepository
from .rules import RuleProfile

TEXT_FIELDS = (
    "name",
    "referat",
    "zweck",
    "ermaechtigungsgrundlage",
    "ansprechperson",
    "kategorien_betroffene",
    "kategorien_daten",
    "kategorien_empfaenger",
    "name_empfaenger",
    "name_empfaenger_drittland",
    "drittland_garantien",
    "auftragsverarbeiter",
    "gemeinsame_verantwortliche",
    "speicherdauer",
    "loeschfrist_rechtsgrundlage",
    "tom",
    "anmerkungen",
)
FLAG_FIELDS = (
    "drittlandtransfer",
    "besondere_kategorien",
    "daten_art10",
    "avv_besteht",
    "gemeinsame_verantwortlichkeit",
)
COUNT_FIELDS = ("anzahl_betroffene",)
REQUIRED_TEXT = (
    "name",
    "zweck",
    "ermaechtigungsgrundlage",
    "kategorien_betroffene",
    "kategorien_daten",
    "kategorien_empfaenger",
    "speicherdauer",
    "tom",
)
MAX_ACTIVITIES = 5_000
MAX_CONTENT_BYTES = 5 * 1024 * 1024
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}")


def _json_value(value: Any, path: str, depth: int = 0) -> None:
    if depth > 8:
        raise ValidationError(f"{path}: zu tief verschachtelt.")
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValidationError(f"{path}: ungültige Zahl.")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json_value(item, f"{path}[{index}]", depth + 1)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValidationError(f"{path}: Schlüssel müssen Text sein.")
            _json_value(item, f"{path}.{key}", depth + 1)
        return
    raise ValidationError(f"{path}: Wert vom Typ {type(value).__name__} ist nicht zulässig.")


def _check_activity_types(activity: Mapping[str, Any], index: int) -> None:
    where = f"Tätigkeit {index}"
    for name in TEXT_FIELDS:
        value = activity.get(name)
        if value is not None and not isinstance(value, str):
            raise ValidationError(f"{where}: Feld '{name}' muss Text sein.")
    for name in FLAG_FIELDS:
        value = activity.get(name)
        if value is not None and not isinstance(value, bool):
            raise ValidationError(
                f"{where}: Feld '{name}' muss Ja/Nein (True/False) oder leer sein, war: {value!r}."
            )
    for name in COUNT_FIELDS:
        value = activity.get(name)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValidationError(
                f"{where}: Feld '{name}' muss eine nichtnegative ganze Zahl oder leer sein."
            )


def content_hash(content: Mapping[str, Any]) -> str:
    """SHA-256 of the canonical JSON content; binds exports and assessments to a version."""
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_content(
    content: Mapping[str, Any], ids: IdFactory | None = None, *, scheme: str = "uuid"
) -> dict[str, Any]:
    """Validate structure and types and persist a stable identifier per activity.

    ``scheme="legacy"`` derives missing identifiers from the name exactly like
    the source application (for migration of existing data); ``"uuid"`` asks
    the identifier port. Existing identifiers are never changed.

    Raises:
        ValidationError: wrong types, duplicate or malformed identifiers,
            too many activities or oversized content.
    """
    if not isinstance(content, Mapping):
        raise ValidationError("Der Inhalt des Verzeichnisses muss eine Zuordnung sein.")
    _json_value(content, "inhalt")
    data: dict[str, Any] = copy.deepcopy(dict(content))
    if len(json.dumps(data, ensure_ascii=False).encode("utf-8")) > MAX_CONTENT_BYTES:
        raise ValidationError("Der Inhalt des Verzeichnisses überschreitet die zulässige Größe.")
    cover = data.setdefault("deckblatt", {})
    if not isinstance(cover, dict):
        raise ValidationError("'deckblatt' muss eine Zuordnung sein.")
    departments = data.setdefault("referate", [])
    if not isinstance(departments, list) or not all(isinstance(d, str) for d in departments):
        raise ValidationError("'referate' muss eine Liste von Texten sein.")
    activities = data.setdefault("taetigkeiten", [])
    if not isinstance(activities, list) or not all(isinstance(a, dict) for a in activities):
        raise ValidationError("'taetigkeiten' muss eine Liste von Zuordnungen sein.")
    if len(activities) > MAX_ACTIVITIES:
        raise ValidationError(f"Mehr als {MAX_ACTIVITIES} Tätigkeiten sind nicht zulässig.")
    for index, activity in enumerate(activities, start=1):
        _check_activity_types(activity, index)
    if scheme == "legacy":
        activities = legacy_activities_with_identifiers(activities)
    elif scheme == "uuid":
        if ids is None:
            raise ValidationError("Für neue Kennungen ist ein IdFactory-Port erforderlich.")
        activities = [a if a.get("id") else {**a, "id": ids.new_id("activity")} for a in activities]
    else:
        raise ValidationError(f"Unbekanntes Kennungsschema '{scheme}'.")
    seen: set[str] = set()
    for activity in activities:
        identifier = activity.get("id")
        if not isinstance(identifier, str) or not _IDENTIFIER.fullmatch(identifier):
            raise ValidationError(f"Ungültige Tätigkeitskennung {identifier!r}.")
        if identifier in seen:
            raise ValidationError(f"Die Tätigkeitskennung '{identifier}' ist doppelt vergeben.")
        seen.add(identifier)
    data["taetigkeiten"] = activities
    return data


def _blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def check_activity(activity: Mapping[str, Any], profile: RuleProfile) -> tuple[Issue, ...]:
    """Content check of one activity against Art. 30 Abs. 1 GDPR fields.

    Blocking issues prevent the release of the register; non-blocking issues
    are shown to the editor (for example an unanswered Art. 9 flag).
    """
    issues: list[Issue] = []
    subject = str(activity.get("id") or activity.get("name") or "")
    columns = dict(profile.register_columns)

    def issue(code: str, field: str, message: str, blocking: bool = True) -> None:
        """Record one issue with its legal reference."""
        reference = profile.register_references.get(field, "")
        suffix = f" ({reference})" if reference else ""
        issues.append(Issue(code, f"{message}{suffix}", blocking, f"{subject}:{field}"))

    for field in REQUIRED_TEXT:
        if _blank(activity.get(field)):
            issue("missing_field", field, f"„{columns.get(field, field)}“ fehlt")
    transfer = activity.get("drittlandtransfer")
    if transfer is None:
        issue("undecided_flag", "drittlandtransfer", "Drittlandsübermittlung ist nicht angegeben")
    elif transfer is True:
        for field in ("name_empfaenger_drittland", "drittland_garantien"):
            if _blank(activity.get(field)):
                issue(
                    "missing_field",
                    field,
                    f"„{columns.get(field, field)}“ fehlt bei Drittlandsübermittlung",
                )
    if not _blank(activity.get("auftragsverarbeiter")) and activity.get("avv_besteht") is None:
        issue("undecided_flag", "avv_besteht", "Angabe zum Auftragsverarbeitungsvertrag fehlt")
    if activity.get("avv_besteht") is False and not _blank(activity.get("auftragsverarbeiter")):
        issue(
            "missing_contract",
            "avv_besteht",
            "Für den Auftragsverarbeiter besteht kein Vertrag",
            False,
        )
    if activity.get("gemeinsame_verantwortlichkeit") is True and _blank(
        activity.get("gemeinsame_verantwortliche")
    ):
        issue("missing_field", "gemeinsame_verantwortliche", "Gemeinsame Verantwortliche fehlen")
    for field in ("besondere_kategorien", "daten_art10"):
        if activity.get(field) is None:
            issue("undecided_flag", field, f"„{field}“ ist nicht angegeben", False)
    if activity.get("anzahl_betroffene") is None:
        issue("missing_count", "anzahl_betroffene", "Zahl der betroffenen Personen fehlt", False)
    return tuple(issues)


def check_register(content: Mapping[str, Any], profile: RuleProfile) -> tuple[Issue, ...]:
    """Cover sheet (Art. 30 Abs. 1 lit. a) plus every activity."""
    issues: list[Issue] = []
    cover = content.get("deckblatt") or {}
    controller = cover.get("verantwortlicher") or {}
    dpo = cover.get("dsb") or {}
    if _blank(controller.get("name")):
        issues.append(
            Issue(
                "missing_field",
                "Verantwortlicher fehlt (Art. 30 Abs. 1 lit. a DSGVO)",
                True,
                "deckblatt:verantwortlicher",
            )
        )
    if _blank(dpo.get("name")):
        issues.append(
            Issue(
                "missing_field",
                "Datenschutzbeauftragte/r fehlt (Art. 30 Abs. 1 lit. a DSGVO)",
                True,
                "deckblatt:dsb",
            )
        )
    for activity in content.get("taetigkeiten") or ():
        issues.extend(check_activity(activity, profile))
    return tuple(issues)


def _normalized(value: Any) -> Any:
    return None if value == "" else value


def activity_changes(
    before: Mapping[str, Any], after: Mapping[str, Any], profile: RuleProfile
) -> tuple[dict[str, Any], ...]:
    """Significant differences; only ``None``, ``""`` and a missing key are equal.

    The source application compared ``(old or "") != (new or "")``, which hides
    a change from ``False``/``0`` to "not specified". That legacy semantics
    remains available as :func:`auditcore_dataprotection.legacy.legacy_compare_activity`.
    """
    changes = []
    for field, title in profile.significant_fields.items():
        old = _normalized(before.get(field))
        new = _normalized(after.get(field))
        if old != new:
            changes.append(
                {
                    "feld": field,
                    "bezeichnung": title,
                    "vorher": before.get(field),
                    "nachher": after.get(field),
                }
            )
    return tuple(changes)


@dataclass
class RegisterService:
    """Create, edit, version and release registers inside a tenant."""

    repository: RegisterRepository
    authorizer: Authorizer
    audit: AuditSink
    clock: Clock
    ids: IdFactory
    profile: RuleProfile
    identifier_scheme: str = "uuid"
    require_complete_release: bool = True

    def _allow(self, actor: Actor, permission: Permission, tenant_id: str) -> None:
        if not isinstance(actor, Actor) or not actor.id:
            raise AuthorizationError("Ohne zugeordnete Person ist keine Bearbeitung möglich.")
        if not self.authorizer.authorize(actor, permission, tenant_id):
            raise AuthorizationError(f"Keine Berechtigung für {permission.value}.")

    def _scoped(self, version: RegisterVersion | None, tenant_id: str) -> RegisterVersion | None:
        if version is not None and version.tenant_id != tenant_id:
            raise TenantMismatchError("Das Verzeichnis gehört zu einem anderen Mandanten.")
        return version

    def _event(self, actor: Actor, action: str, version: RegisterVersion, **details: Any) -> None:
        self.audit.record(
            AuditEvent(
                tenant_id=version.tenant_id,
                actor_id=actor.id,
                action=action,
                entity="register",
                entity_id=version.register_id,
                version=version.version,
                at=self.clock.now(),
                details={"content_hash": version.content_hash, **details},
            )
        )

    def draft(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> RegisterVersion | None:
        """Open draft of the register, if any."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        return self._scoped(self.repository.get_draft(tenant_id, register_id), tenant_id)

    def released(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> RegisterVersion | None:
        """Currently released version, if any."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        return self._scoped(self.repository.get_released(tenant_id, register_id), tenant_id)

    def effective(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> RegisterVersion | None:
        """Released version if any, otherwise the draft (source-application rule)."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        return self._effective(tenant_id, register_id)

    def _effective(self, tenant_id: str, register_id: str) -> RegisterVersion | None:
        released = self._scoped(self.repository.get_released(tenant_id, register_id), tenant_id)
        if released is not None:
            return released
        return self._scoped(self.repository.get_draft(tenant_id, register_id), tenant_id)

    def history(
        self, tenant_id: str, actor: Actor, register_id: str = DEFAULT_REGISTER
    ) -> tuple[RegisterVersion, ...]:
        """All versions of the register, newest first."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        versions = self.repository.list_versions(tenant_id, register_id)
        return tuple(v for v in versions if self._scoped(v, tenant_id) is not None)

    def save_draft(
        self,
        tenant_id: str,
        actor: Actor,
        content: Mapping[str, Any],
        *,
        register_id: str = DEFAULT_REGISTER,
        expected_revision: int | None = None,
    ) -> RegisterVersion:
        """Create the next draft or replace the open draft (revision required).

        Released versions stay untouched; editors of the draft accumulate so
        that none of them can release it.
        """
        self._allow(actor, Permission.REGISTER_EDIT, tenant_id)
        data = normalize_content(content, self.ids, scheme=self.identifier_scheme)
        digest = content_hash(data)
        now = self.clock.now()
        draft = self._scoped(self.repository.get_draft(tenant_id, register_id), tenant_id)
        if draft is not None:
            if expected_revision != draft.revision:
                raise StaleRevisionError(
                    f"Der Entwurf wurde inzwischen geändert (Revision {draft.revision}). "
                    "Bitte neu laden."
                )
            editors = draft.editors if actor.id in draft.editors else (*draft.editors, actor.id)
            updated = replace(
                draft,
                content=data,
                content_hash=digest,
                editors=editors,
                created_by=actor.id,
                created_at=now,
                revision=draft.revision + 1,
            )
            self.repository.replace(updated, expected_revision)
            self._event(actor, "register.draft_saved", updated)
            return updated
        if expected_revision is not None:
            raise StaleRevisionError("Es gibt keinen offenen Entwurf mit dieser Revision.")
        versions = self.repository.list_versions(tenant_id, register_id)
        released = self._scoped(self.repository.get_released(tenant_id, register_id), tenant_id)
        number = max((v.version for v in versions), default=0) + 1
        created = RegisterVersion(
            tenant_id=tenant_id,
            register_id=register_id,
            version=number,
            status=RegisterStatus.DRAFT,
            content=data,
            content_hash=digest,
            created_by=actor.id,
            created_at=now,
            editors=(actor.id,),
            predecessor_version=released.version if released else None,
        )
        self.repository.add(created)
        self._event(actor, "register.draft_created", created)
        return created

    def release(
        self,
        tenant_id: str,
        actor: Actor,
        *,
        expected_revision: int,
        register_id: str = DEFAULT_REGISTER,
    ) -> RegisterVersion:
        """Four-eyes release of the open draft; the previous release is superseded."""
        self._allow(actor, Permission.REGISTER_RELEASE, tenant_id)
        draft = self._scoped(self.repository.get_draft(tenant_id, register_id), tenant_id)
        if draft is None:
            raise ConflictError(
                f"Es liegt kein offener Entwurf für '{register_id}' zur Freigabe vor."
            )
        if draft.revision != expected_revision:
            raise StaleRevisionError("Der Entwurf wurde seit dem Laden geändert.")
        if actor.id in draft.editors:
            raise FourEyesViolation(
                "Vier-Augen-Prinzip verletzt: Die Kennung "
                f"'{actor.id}' hat diesen Entwurf bearbeitet und darf ihn nicht freigeben. "
                "Die Freigabe muss durch eine zweite fachkundige Person erfolgen."
            )
        blocking = [i for i in check_register(draft.content, self.profile) if i.blocking]
        if self.require_complete_release and blocking:
            raise ConflictError(
                f"Das Verzeichnis ist unvollständig ({len(blocking)} Pflichtangaben fehlen), "
                f"zuerst: {blocking[0].message}."
            )
        previous = self._scoped(self.repository.get_released(tenant_id, register_id), tenant_id)
        released = replace(
            draft,
            status=RegisterStatus.RELEASED,
            released_by=actor.id,
            released_at=self.clock.now(),
            predecessor_version=previous.version if previous else None,
            revision=draft.revision + 1,
        )
        self.repository.replace(released, expected_revision)
        if previous is not None:
            self.repository.mark_superseded(
                tenant_id, register_id, previous.version, previous.revision
            )
        self._event(
            actor, "register.released", released, superseded=previous.version if previous else None
        )
        return released

    def activity(
        self, tenant_id: str, actor: Actor, activity_id: str, register_id: str = DEFAULT_REGISTER
    ) -> tuple[Mapping[str, Any], RegisterVersion]:
        """Activity of the effective version together with that version."""
        self._allow(actor, Permission.REGISTER_READ, tenant_id)
        return find_activity(self._effective(tenant_id, register_id), activity_id)


def find_activity(
    version: RegisterVersion | None, activity_id: str
) -> tuple[Mapping[str, Any], RegisterVersion]:
    """Activity and version for an identifier; NotFoundError otherwise."""
    if version is None:
        raise NotFoundError(
            "Für diesen Mandanten ist noch kein Verzeichnis von Verarbeitungstätigkeiten "
            "hinterlegt. Die Folgenabschätzung setzt darauf auf (Art. 30, Art. 35 DSGVO)."
        )
    for activity in version.activities:
        if activity.get("id") == activity_id:
            return activity, version
    raise NotFoundError(f"Verarbeitungstätigkeit mit ID {activity_id} nicht gefunden")


def group_by_department(
    activities: Sequence[Mapping[str, Any]], departments: Sequence[str]
) -> list[tuple[str, list[Mapping[str, Any]]]]:
    """Source layout: listed departments in order, then unknown ones, empty ones omitted."""
    known = [d for d in departments if any(a.get("referat") == d for a in activities)]
    unknown = sorted({a.get("referat") or "Ohne Referat" for a in activities} - set(known))
    return [
        (name, [a for a in activities if (a.get("referat") or "Ohne Referat") == name])
        for name in known + unknown
    ]
