"""Input contract of the screening review API: actors, subjects, run requests, errors.

Everything a client sends is validated here before it reaches the library.
Messages are German because they are shown to reviewers unchanged; codes are
stable and machine-readable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ._types import ActorView, SubjectInput

CONTRACT = "auditcore_registry_sources.screening_review/1"

KIND_SANCTIONS = "sanctions"
KIND_PEP = "pep"
KINDS = (KIND_SANCTIONS, KIND_PEP)

OUTCOME_CONFIRMED = "confirmed"
OUTCOME_DISMISSED = "dismissed"
OUTCOME_DEFERRED = "deferred"
OUTCOMES = (OUTCOME_CONFIRMED, OUTCOME_DISMISSED, OUTCOME_DEFERRED)

STATUS_OPEN = "open"
STATUS_PENDING = "pending_second_review"
REVIEW_STATUSES = (STATUS_OPEN, STATUS_PENDING, *OUTCOMES)
FINAL_STATUSES = (OUTCOME_CONFIRMED, OUTCOME_DISMISSED)

MAX_SUBJECTS = 200
MAX_TEXT = 500
MAX_REASON = 4000


class ReviewError(Exception):
    """Error of the review API with HTTP status, stable code and German message."""

    def __init__(
        self, status: int, code: str, message: str, details: Mapping[str, object] | None = None
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, dict[str, object]]:
        """JSON body of the error response."""
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


def invalid(message: str, **details: object) -> ReviewError:
    """422: the request is well-formed JSON but violates the contract."""
    return ReviewError(422, "invalid_request", message, details)


def not_found(message: str) -> ReviewError:
    """404."""
    return ReviewError(404, "not_found", message)


def conflict(code: str, message: str, **details: object) -> ReviewError:
    """409: the request collides with the current review state."""
    return ReviewError(409, code, message, details)


@dataclass(frozen=True)
class Actor:
    """Authenticated person as established by the consumer; the API never authenticates."""

    id: str
    display_name: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("Ein Akteur braucht eine Kennung.")

    def to_dict(self) -> ActorView:
        """JSON view."""
        return {"id": self.id, "display_name": self.display_name or self.id}


@dataclass(frozen=True)
class Subject:
    """One name to be screened, with the optional comparison data of the case."""

    subject_id: str
    name: str
    birth_date: str | None = None
    country: str | None = None
    schema: str | None = None
    reference: str | None = None

    def to_dict(self) -> SubjectInput:
        """JSON view."""
        return {
            "subject_id": self.subject_id,
            "name": self.name,
            "birth_date": self.birth_date,
            "country": self.country,
            "schema": self.schema,
            "reference": self.reference,
        }


@dataclass(frozen=True)
class RunRequest:
    """Validated request for a screening run (Prüflauf)."""

    kind: str
    profile_id: str
    profile_version: str
    subjects: tuple[Subject, ...]
    lists: tuple[str, ...] | None = None
    min_score: float | None = None
    limit: int = 15
    case_reference: str | None = None


def _text(value: object, name: str, *, required: bool = False, limit: int = MAX_TEXT) -> str | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise invalid(f"Pflichtangabe fehlt: {name}.", field=name)
        return None
    if not isinstance(value, str):
        raise invalid(f"„{name}“ ist als Text anzugeben.", field=name)
    stripped = value.strip()
    if len(stripped) > limit:
        raise invalid(f"„{name}“ ist länger als {limit} Zeichen.", field=name)
    return stripped


def _number(value: object, name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise invalid(f"„{name}“ ist als Zahl anzugeben.", field=name)
    return float(value)


def _subjects(raw: object) -> tuple[Subject, ...]:
    if not isinstance(raw, list) or not raw:
        raise invalid("Mindestens ein zu prüfender Name ist anzugeben.", field="subjects")
    if len(raw) > MAX_SUBJECTS:
        raise invalid(f"Höchstens {MAX_SUBJECTS} Namen je Prüflauf.", field="subjects")
    result = []
    for position, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise invalid("Jeder Eintrag in „subjects“ ist ein Objekt.", field="subjects")
        name = _text(item.get("name"), "Name", required=True)
        assert name is not None
        result.append(
            Subject(
                subject_id=f"s{position}",
                name=name,
                birth_date=_text(item.get("birth_date"), "Geburtsdatum", limit=64),
                country=_text(item.get("country"), "Staatsangehörigkeit/Land", limit=200),
                schema=_text(item.get("schema"), "Eintragstyp", limit=64),
                reference=_text(item.get("reference"), "Bezug"),
            )
        )
    return tuple(result)


def _profile_ref(raw: object) -> tuple[str, str]:
    if not isinstance(raw, dict):
        raise invalid(
            "Das Profil ist ausdrücklich als {id, version} anzugeben; es gibt kein "
            "stillschweigendes Standardprofil.",
            field="profile",
        )
    profile_id = _text(raw.get("id"), "Profilkennung", required=True, limit=200)
    version = _text(raw.get("version"), "Profilversion", required=True, limit=64)
    assert profile_id is not None and version is not None
    return profile_id, version


def _lists(raw: object) -> tuple[str, ...] | None:
    if raw is None:
        return None
    if not isinstance(raw, list) or not all(isinstance(k, str) and k for k in raw):
        raise invalid("„lists“ ist eine Liste von Listenkennungen.", field="lists")
    if not raw:
        raise invalid("Mindestens eine Liste ist auszuwählen.", field="lists")
    return tuple(dict.fromkeys(raw))


def _limit(raw: object) -> int:
    if raw is None:
        return 15
    if isinstance(raw, bool) or not isinstance(raw, int) or not 1 <= raw <= 100:
        raise invalid("„limit“ ist eine ganze Zahl zwischen 1 und 100.", field="limit")
    return raw


def parse_run_request(body: object) -> RunRequest:
    """Validate the JSON body of ``POST /runs``."""
    if not isinstance(body, dict):
        raise invalid("Der Anfragetext ist ein JSON-Objekt.")
    kind = body.get("kind")
    if kind not in KINDS:
        raise invalid(f"„kind“ ist einer der Werte {', '.join(KINDS)}.", field="kind")
    profile_id, version = _profile_ref(body.get("profile"))
    return RunRequest(
        kind=str(kind),
        profile_id=profile_id,
        profile_version=version,
        subjects=_subjects(body.get("subjects")),
        lists=_lists(body.get("lists")),
        min_score=_number(body.get("min_score"), "min_score"),
        limit=_limit(body.get("limit")),
        case_reference=_text(body.get("case_reference"), "Vorgangsbezug"),
    )


@dataclass(frozen=True)
class DecisionRequest:
    """Validated decision on one hit."""

    outcome: str
    reason: str
    four_eyes: bool
    expected_sequence: int | None


def _expected(raw: object) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
        raise invalid("„expected_sequence“ ist eine nicht negative ganze Zahl.")
    return raw


def parse_reason(raw: object) -> str:
    """Mandatory reason; whitespace alone is no reason."""
    reason = _text(raw, "Begründung", required=True, limit=MAX_REASON)
    assert reason is not None
    return reason


def parse_decision(body: object) -> DecisionRequest:
    """Validate the JSON body of ``POST …/decision``."""
    if not isinstance(body, dict):
        raise invalid("Der Anfragetext ist ein JSON-Objekt.")
    outcome = body.get("outcome")
    if outcome not in OUTCOMES:
        raise invalid(
            "„outcome“ ist confirmed (bestätigen), dismissed (verwerfen) oder "
            "deferred (zurückstellen).",
            field="outcome",
        )
    four_eyes = body.get("four_eyes", False)
    if not isinstance(four_eyes, bool):
        raise invalid("„four_eyes“ ist wahr oder falsch.", field="four_eyes")
    return DecisionRequest(
        outcome=str(outcome),
        reason=parse_reason(body.get("reason")),
        four_eyes=four_eyes,
        expected_sequence=_expected(body.get("expected_sequence")),
    )


@dataclass(frozen=True)
class SecondReviewRequest:
    """Validated second review (Vier-Augen-Prüfung) of a pending decision."""

    approve: bool
    reason: str
    expected_sequence: int | None


def parse_second_review(body: object) -> SecondReviewRequest:
    """Validate the JSON body of ``POST …/second-review``."""
    if not isinstance(body, dict):
        raise invalid("Der Anfragetext ist ein JSON-Objekt.")
    approve = body.get("approve")
    if not isinstance(approve, bool):
        raise invalid("„approve“ ist wahr (zustimmen) oder falsch (ablehnen).", field="approve")
    return SecondReviewRequest(
        approve=approve,
        reason=parse_reason(body.get("reason")),
        expected_sequence=_expected(body.get("expected_sequence")),
    )


def split_filter(raw: str | None, allowed: Sequence[str], name: str) -> tuple[str, ...]:
    """Comma separated filter values, checked against the allowed values."""
    if not raw:
        return ()
    values = tuple(v.strip() for v in raw.split(",") if v.strip())
    unknown = [v for v in values if v not in allowed]
    if unknown:
        raise invalid(f"Unbekannter Filterwert für „{name}“: {', '.join(unknown)}.", field=name)
    return values
