"""Source profile ``designer.deminimis.register``: central de-minimis register (eAidRegister).

Behavior of ``janpow77/audit_designer@030a71e``
(``core/shared/research/register/de_minimis.py``, ``de_minimis_ernte.py``,
``de_minimis_models.py``, ``de_minimis_zuordnung.py``), separate from state aid.

This module contains the source-specific parts only: request construction,
response interpretation, field mapping, identities, the authority-level rules
and the completeness rules of an inventory. Fetching, paging, retries and
checkpoints belong to ``auditcore_harvest``; database writes to the consumer.
A register query never releases or decides anything.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Any

from .profiles import load_profile

PROFILE_ID = "designer.deminimis.register"
API_BASE = "https://aid-register.ec.europa.eu/eair/public/api"
PUBLIC_UI = "https://aid-register.ec.europa.eu/home"
PAGE_SIZE = 500
MASKED = "***"
COLUMNS = (
    "referenceNumber",
    "beneficiaryName",
    "beneficiaryReferenceNumber",
    "amountEur",
    "currency",
    "amount",
    "grantingDate",
    "deMinimisType",
    "grantingAuthorityName",
    "sector",
    "instrument",
    "publishedDate",
    "country",
)
HASH_FIELDS = (
    "referenceNumber",
    "beneficiaryName",
    "beneficiaryReferenceNumber",
    "amountEur",
    "grantingDate",
    "deMinimisType",
    "grantingAuthorityName",
    "sector",
    "instrument",
    "country",
)
ISO2_TO_ISO3 = {
    "AT": "AUT",
    "BE": "BEL",
    "BG": "BGR",
    "CY": "CYP",
    "CZ": "CZE",
    "DE": "DEU",
    "DK": "DNK",
    "EE": "EST",
    "EL": "GRC",
    "ES": "ESP",
    "FI": "FIN",
    "FR": "FRA",
    "GR": "GRC",
    "HR": "HRV",
    "HU": "HUN",
    "IE": "IRL",
    "IT": "ITA",
    "LT": "LTU",
    "LU": "LUX",
    "LV": "LVA",
    "MT": "MLT",
    "NL": "NLD",
    "PL": "POL",
    "PT": "PRT",
    "RO": "ROU",
    "SE": "SWE",
    "SI": "SVN",
    "SK": "SVK",
}


def country_code(code: str | None) -> str:
    """Business key of the register (``CountryDEU``).

    The ISO code ``DE`` would silently match nothing in the register search.
    """
    raw = (code or "DEU").strip().upper()
    if raw.startswith("COUNTRY"):
        return "Country" + raw[7:]
    if len(raw) == 2:
        raw = ISO2_TO_ISO3.get(raw, raw)
    return f"Country{raw}"


@dataclass
class SearchCriteria:
    """Search body of the public API (field names of the interface)."""

    country: str | None = "CountryDEU"
    beneficiaryName: str | None = None  # noqa: N815 - interface field name
    beneficiaryIdentifier: str | None = None  # noqa: N815
    referenceNumber: str | None = None  # noqa: N815
    grantingAuthorityName: str | None = None  # noqa: N815
    deMinimisTypes: list[str] | None = None  # noqa: N815
    grantingDateFrom: str | None = None  # noqa: N815
    grantingDateTo: str | None = None  # noqa: N815
    amountFrom: float | None = None  # noqa: N815
    amountTo: float | None = None  # noqa: N815
    pageNumber: int = 0  # noqa: N815
    pageSize: int = 100  # noqa: N815
    languageCode: str = "de"  # noqa: N815

    def body(self) -> dict[str, Any]:
        """Request body without empty values (``None``, ``[]``, ``""``)."""
        return {k: v for k, v in self.__dict__.items() if v not in (None, [], "")}


@dataclass(frozen=True)
class Request:
    """A read-only request; transport and retries are supplied by the harvest core."""

    method: str
    url: str
    json: Mapping[str, Any] | None = None
    expected_empty_status: tuple[int, ...] = ()


def search_request(criteria: SearchCriteria) -> Request:
    """``POST /de-minimis-aid-awards`` for one page."""
    return Request("POST", f"{API_BASE}/de-minimis-aid-awards", criteria.body())


def count_request(criteria: SearchCriteria) -> Request:
    """``POST /de-minimis-aid-awards/counters`` without paging fields."""
    body = criteria.body()
    body.pop("pageNumber", None)
    body.pop("pageSize", None)
    return Request("POST", f"{API_BASE}/de-minimis-aid-awards/counters", body)


def beneficiary_request(reference: str) -> Request:
    """``GET /de-minimis-aid-awards/beneficiary/{reference}``; ``404`` means no awards."""
    if not isinstance(reference, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", reference):
        raise ValueError("Ungültige Referenznummer des Begünstigten.")
    return Request(
        "GET",
        f"{API_BASE}/de-minimis-aid-awards/beneficiary/{reference}",
        expected_empty_status=(404,),
    )


class RegisterResponseError(ValueError):
    """The register answered with something that is not an award list (FS-D01)."""


def parse_award_list(
    payload: Any, *, status: int = 200, strict: bool = True
) -> list[dict[str, Any]]:
    """Award list of a search or beneficiary response.

    ``strict=False`` reproduces the source application, which turned any
    non-list JSON into an empty list — indistinguishable from "no award".
    """
    if status == 404:
        return []
    if isinstance(payload, list) and all(isinstance(p, dict) for p in payload):
        return list(payload)
    if not strict:
        return payload if isinstance(payload, list) else []
    raise RegisterResponseError("Die Antwort des Registers ist keine Liste von Meldungen.")


def legacy_error_message(status: int | None) -> str:
    """Message of the source client for an HTTP status (``None`` = not reachable)."""
    if status is None:
        return "Das De-minimis-Register ist nicht erreichbar."
    return f"Das De-minimis-Register antwortete mit {status}."


def parse_count(payload: Any) -> int | None:
    """Total from ``{"count": n}`` or ``[{"count": n}]``; otherwise unknown (``None``)."""
    if isinstance(payload, dict) and isinstance(payload.get("count"), int):
        return int(payload["count"])
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        value = payload[0].get("count")
        return value if isinstance(value, int) else None
    return None


def row(record: Mapping[str, Any]) -> dict[str, Any]:
    """Display row with exactly the documented columns."""
    return {column: record.get(column) for column in COLUMNS}


def as_date(value: Any) -> date | None:
    """Granting date for the cumulation (ISO prefix)."""
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def as_amount(value: Any) -> Decimal | None:
    """Finite amount or ``None``; booleans are not amounts."""
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        amount = Decimal(str(value))
        return amount if amount.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def normalize_name(name: str | None) -> str | None:
    """Lower case with compact whitespace (inventory search helper)."""
    if not name:
        return None
    return " ".join(name.lower().split())


def harvest_amount(value: Any) -> Decimal | None:
    """Amount as stored by the harvest (NaN/Infinity are kept, unlike :func:`as_amount`)."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def harvest_date(value: Any) -> date | None:
    """Date as stored by the harvest."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def harvest_timestamp(value: Any) -> datetime | None:
    """Publication timestamp (``"YYYY-MM-DD HH:MM:SS"`` accepted)."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).strip().replace(" ", "T", 1))
    except ValueError:
        return None


@lru_cache(maxsize=1)
def _authority_rules() -> tuple[tuple[str, tuple[re.Pattern[str], ...]], ...]:
    data = load_profile("designer.deminimis.authority_levels")
    return tuple(
        (target, tuple(re.compile(p, re.IGNORECASE) for p in patterns))
        for target, patterns in data["rules"]
    )


def authority_level(name: str | None) -> str:
    """``Bund``, a federal state or ``unbestimmt`` from the authority name (visible rules)."""
    if not name:
        return "unbestimmt"
    for target, patterns in _authority_rules():
        if any(p.search(name) for p in patterns):
            return target
    return "unbestimmt"


def harvest_fields(record: Mapping[str, Any]) -> dict[str, Any]:
    """Normalised inventory fields of one register record; the raw record is kept."""
    name = record.get("beneficiaryName")
    return {
        "beneficiary_name": name,
        "beneficiary_name_normalized": normalize_name(name),
        "beneficiary_reference": record.get("beneficiaryReferenceNumber"),
        "beneficiary_masked": 1 if name and MASKED in name else 0,
        "amount_eur": harvest_amount(record.get("amountEur")),
        "currency": record.get("currency"),
        "granting_date": harvest_date(record.get("grantingDate")),
        "published_at": harvest_timestamp(record.get("publishedDate")),
        "de_minimis_type": record.get("deMinimisType"),
        "granting_authority": record.get("grantingAuthorityName"),
        "sector": record.get("sector"),
        "instrument": record.get("instrument"),
        "country": (record.get("country") or "").replace("Country", "") or None,
        "authority_level": authority_level(record.get("grantingAuthorityName")),
        "raw_payload": dict(record),
    }


def record_hash(record: Mapping[str, Any]) -> str:
    """SHA-256 over the content fields of a register record (change detection)."""
    canonical = json.dumps(
        {f: record.get(f) for f in HASH_FIELDS},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def inventory_hash(hashes: Iterable[str]) -> str:
    """SHA-256 over the sorted record hashes of one run."""
    return hashlib.sha256("".join(sorted(hashes)).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Inventory reconciliation (source semantics, no database)
# ---------------------------------------------------------------------------


@dataclass
class Reconciliation:
    """Outcome of one harvest over the pages that were actually received."""

    reported: int | None = None
    seen: dict[str, str] = field(default_factory=dict)
    inserted: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    skipped_without_reference: int = 0
    requests: int = 0
    error: str | None = None
    vanished: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        """Only a run that saw at least the reported total without error is complete."""
        return self.error is None and self.reported is not None and len(self.seen) >= self.reported

    @property
    def status(self) -> str:
        """``ok``, ``partial`` or ``failed`` exactly as in the source."""
        if self.complete:
            return "ok"
        return "failed" if self.error else "partial"

    @property
    def content_hash(self) -> str:
        return inventory_hash(self.seen.values())


def reconcile_page(
    state: Reconciliation,
    rows: Sequence[Mapping[str, Any]],
    reported: int | None,
    stored: Mapping[str, str],
) -> bool:
    """Apply one received page; returns whether another page is required.

    ``stored`` maps reference numbers to the stored content hash (``None``
    entries mean unknown). Records without reference number are skipped and
    counted. Order and counters follow ``de_minimis_ernte.ernte``.
    """
    state.requests += 1
    state.reported = reported
    if not rows:
        return False
    for record in rows:
        reference = record.get("referenceNumber")
        if not reference:
            state.skipped_without_reference += 1
            continue
        digest = record_hash(record)
        key = str(reference)
        # A reference repeated within the run compares with the value just written.
        previous = state.seen[key] if key in state.seen else stored.get(key)
        state.seen[key] = digest
        if previous is None:
            state.inserted.append(key)
        elif previous != digest:
            state.updated.append(key)
        else:
            state.unchanged.append(key)
    return not (reported is not None and len(state.seen) >= reported)


def mark_vanished(state: Reconciliation, active_references: Iterable[str]) -> list[str]:
    """References to mark as vanished — only after a complete run, never after a partial one."""
    if not state.complete:
        state.vanished = []
        return []
    state.vanished = sorted(r for r in active_references if r not in state.seen)
    return state.vanished


def inventory_state(
    runs: Sequence[Mapping[str, Any]], active: int, vanished: int, *, legacy: bool = False
) -> dict[str, Any]:
    """What the inventory says about itself.

    ``legacy=True`` reproduces ``bestandsstand``: it reports the last *ok* run
    as current and ``vollstaendig=True`` even when a newer failed or partial
    run already changed stored rows (FS-D02). The corrected form reports the
    newest run and is complete only if that newest run is ``ok``.
    """
    ordered = sorted(runs, key=lambda r: str(r.get("started_at") or ""), reverse=True)
    last_ok = next((r for r in ordered if r.get("status") == "ok"), None)
    newest = ordered[0] if ordered else None
    if legacy:
        return {
            "stand_am": last_ok.get("finished_at") if last_ok else None,
            "inhaltshash": last_ok.get("content_hash") if last_ok else None,
            "saetze": active,
            "verschwunden": vanished,
            "vollstaendig": bool(last_ok),
        }
    return {
        "stand_am": newest.get("finished_at") if newest else None,
        "inhaltshash": newest.get("content_hash") if newest else None,
        "letzter_status": newest.get("status") if newest else None,
        "letzter_vollstaendiger_lauf": last_ok.get("finished_at") if last_ok else None,
        "saetze": active,
        "verschwunden": vanished,
        "vollstaendig": bool(newest and newest.get("status") == "ok"),
    }
