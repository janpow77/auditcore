"""Content of a register version: structure, identifiers, content checks, changes.

A register version is a JSON document with a cover sheet (``deckblatt``),
departments (``referate``) and activities (``taetigkeiten``), using the field
names of the source application.
"""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from auditcore_common.hashing import canonical_sha256

from .errors import NotFoundError, ValidationError
from .legacy_admin import legacy_activities_with_identifiers
from .model import RegisterVersion
from .ports import IdFactory
from .results import Issue
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
_MAX_DEPTH = 8

# ---------------------------------------------------------------------------
# Structure and identifiers
# ---------------------------------------------------------------------------


def _json_value(value: object, path: str, depth: int = 0) -> None:
    if depth > _MAX_DEPTH:
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


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _check_activity_types(activity: Mapping[str, object], index: int) -> None:
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
        if value is not None and not _is_count(value):
            raise ValidationError(
                f"{where}: Feld '{name}' muss eine nichtnegative ganze Zahl oder leer sein."
            )


def content_hash(content: Mapping[str, object]) -> str:
    """SHA-256 of the canonical JSON content; binds exports and assessments to a version."""
    return canonical_sha256(content)


def _structured_copy(content: Mapping[str, Any]) -> dict[str, Any]:
    """Deep copy with cover sheet, departments and activities of the expected types."""
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
    return data


def _with_identifiers(
    activities: list[dict[str, Any]], ids: IdFactory | None, scheme: str
) -> list[dict[str, Any]]:
    """Missing identifiers by the chosen scheme; existing identifiers stay unchanged."""
    if scheme == "legacy":
        return legacy_activities_with_identifiers(activities)
    if scheme == "uuid":
        if ids is None:
            raise ValidationError("Für neue Kennungen ist ein IdFactory-Port erforderlich.")
        return [a if a.get("id") else {**a, "id": ids.new_id("activity")} for a in activities]
    raise ValidationError(f"Unbekanntes Kennungsschema '{scheme}'.")


def _check_identifiers(activities: Sequence[Mapping[str, object]]) -> None:
    seen: set[str] = set()
    for activity in activities:
        identifier = activity.get("id")
        if not isinstance(identifier, str) or not _IDENTIFIER.fullmatch(identifier):
            raise ValidationError(f"Ungültige Tätigkeitskennung {identifier!r}.")
        if identifier in seen:
            raise ValidationError(f"Die Tätigkeitskennung '{identifier}' ist doppelt vergeben.")
        seen.add(identifier)


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
    data = _structured_copy(content)
    for index, activity in enumerate(data["taetigkeiten"], start=1):
        _check_activity_types(activity, index)
    activities = _with_identifiers(data["taetigkeiten"], ids, scheme)
    _check_identifiers(activities)
    data["taetigkeiten"] = activities
    return data


# ---------------------------------------------------------------------------
# Content checks (Art. 30 Abs. 1 DSGVO)
# ---------------------------------------------------------------------------


def _blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


#: ``issue(code, field, message, blocking=True)`` of :func:`check_activity`.
_Report = Callable[..., None]


def _check_required_text(
    activity: Mapping[str, object], columns: Mapping[str, str], issue: _Report
) -> None:
    for field in REQUIRED_TEXT:
        if _blank(activity.get(field)):
            issue("missing_field", field, f"„{columns.get(field, field)}“ fehlt")


def _check_transfer(
    activity: Mapping[str, object], columns: Mapping[str, str], issue: _Report
) -> None:
    transfer = activity.get("drittlandtransfer")
    if transfer is None:
        issue("undecided_flag", "drittlandtransfer", "Drittlandsübermittlung ist nicht angegeben")
        return
    if transfer is not True:
        return
    for field in ("name_empfaenger_drittland", "drittland_garantien"):
        if _blank(activity.get(field)):
            issue(
                "missing_field",
                field,
                f"„{columns.get(field, field)}“ fehlt bei Drittlandsübermittlung",
            )


def _check_processors(activity: Mapping[str, object], issue: _Report) -> None:
    """Processor contract and joint controllers."""
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


def _check_open_flags(activity: Mapping[str, object], issue: _Report) -> None:
    """Non-blocking: Art. 9/10 flags and the number of persons."""
    for field in ("besondere_kategorien", "daten_art10"):
        if activity.get(field) is None:
            issue("undecided_flag", field, f"„{field}“ ist nicht angegeben", False)
    if activity.get("anzahl_betroffene") is None:
        issue("missing_count", "anzahl_betroffene", "Zahl der betroffenen Personen fehlt", False)


def check_activity(activity: Mapping[str, object], profile: RuleProfile) -> tuple[Issue, ...]:
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

    _check_required_text(activity, columns, issue)
    _check_transfer(activity, columns, issue)
    _check_processors(activity, issue)
    _check_open_flags(activity, issue)
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


# ---------------------------------------------------------------------------
# Changes, lookup and layout
# ---------------------------------------------------------------------------


def _normalized(value: object) -> object:
    return None if value == "" else value


def activity_changes(
    before: Mapping[str, object], after: Mapping[str, object], profile: RuleProfile
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
