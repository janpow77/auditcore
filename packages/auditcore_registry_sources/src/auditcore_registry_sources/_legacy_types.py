"""Shapes of the dictionaries the legacy replays return (keys exactly as in the originals)."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict


class DesignerRecord(TypedDict):
    """``SanktionslistenDienst._zu_datensatz``."""

    list_key: str
    entry_id: str
    entity_schema: str
    name: str
    name_normalized: str
    aliases: list[str] | None
    birth_date: str | None
    countries: str | None
    addresses: str | None
    identifiers: str | None
    sanctions_program: str | None
    program_ids: str | None
    first_seen: str | None
    last_seen: str | None
    raw_payload: dict[str, str | None]
    refresh_run_id: None


class DesignerHit(TypedDict):
    """``Sanktionstreffer.to_dict``."""

    source_url: str | None
    source_key: str | None
    list_key: str
    list_name: str
    entry_id: str
    entity_schema: str
    name: str
    matched_name: str
    matched_field: str
    score: float
    confidence: str
    aliases: list[str]
    birth_date: str
    countries: str
    addresses: str
    identifiers: str
    sanctions_program: str
    program_ids: str
    first_seen: str
    last_seen: str
    dob_conflict: bool
    country_conflict: bool


class DesignerListFinding(TypedDict):
    """One list of ``SanktionslistenDienst.suche`` (German keys of the source)."""

    list_key: str
    source_key: str | None
    durchsucht: bool
    bestand: int
    stand: datetime | None
    hinweis: str | None
    treffer: list[DesignerHit]


class WorkshopRecord(TypedDict):
    """flowworkshop ``FsfRecord`` fields (as the CSV row delivers them) plus comparison forms."""

    id: str
    schema: str
    name: str
    aliases: list[str]
    birth_date: str
    countries: str
    addresses: str
    identifiers: str
    sanctions: str
    program_ids: str
    first_seen: str
    last_seen: str
    name_norm: str
    alias_norms: tuple[str, ...]


class WorkshopHit(TypedDict):
    """flowworkshop hit dictionary."""

    id: str
    schema: str
    name: str
    matched_on: str
    matched_field: str
    score: float
    confidence: str
    aliases: list[str]
    birth_date: str
    countries: str
    addresses: str
    identifiers: str
    sanctions: str
    program_ids: str
    first_seen: str
    last_seen: str
    source_key: str
    source_display_name: str
    dob_conflict: bool
    country_conflict: bool


class PortalRecord(TypedDict):
    """``audit_prep.sanctions.row_to_record``."""

    entry_id: str
    schema: str
    name: str
    aliases: list[str]
    birth_date: str
    countries: list[str]
    addresses: str
    identifiers: str
    sanctions: str
    program_ids: str
    first_seen: str
    last_seen: str
    name_norm: str
    name_folded: str
    alias_folded: list[str]
    vat_ids: list[str]


class PortalValidation(TypedDict):
    """Errors and warnings of ``parse_sanctions_csv``."""

    errors: list[str]
    warnings: list[str]


class PepEntry(TypedDict):
    """``PEPChecker._download_and_parse`` entry."""

    id: str
    name: str
    name_normalized: str
    aliases: list[str]
    aliases_normalized: list[str]
    countries: str
    dataset: str
    first_seen: str | None
    last_seen: str | None
    position: str


class VatValidation(TypedDict):
    """``CompanyVerifier.validate_vat_id`` without ``request_date``."""

    is_valid: bool
    vat_id: str
    country_code: str
    company_name: str | None
    company_address: str | None
    error_message: str | None


class RegisterCompanyInfo(TypedDict):
    """``search_offene_register`` result (values of the register row as delivered)."""

    name: str
    legal_form: str | None
    status: str
    registration_number: str | None
    registration_authority: str | None
    address: str | None
    founded_date: None
    directors: list[str]
    source: str
