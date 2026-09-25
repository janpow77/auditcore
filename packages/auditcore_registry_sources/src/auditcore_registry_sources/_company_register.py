"""OffeneRegister lookup: bound datasette query, answer parsing and status mapping."""

from __future__ import annotations

import json
from dataclasses import dataclass

from auditcore_harvest import ParserError, Transport, TransportError, raise_for_status

from ._types import JsonObject
from .errors import QueryError
from .profiles import RegistryProfile

REGISTER_URL = "https://db.offeneregister.de/openregister"


#: Datasette query with bound parameters; the name is never part of the SQL text.
REGISTER_SQL = "select * from companies where name like :pattern limit :limit"


def register_query(name: str, *, limit: int = 5) -> tuple[str, dict[str, str]]:
    """URL and parameters of a register lookup (datasette named parameters)."""
    if not name or not name.strip():
        raise QueryError("Pflichtangabe fehlt: Firmenname.")
    return f"{REGISTER_URL}.json", {
        "sql": REGISTER_SQL,
        "pattern": f"%{name.strip()}%",
        "limit": str(int(limit)),
        "_shape": "objects",
    }


@dataclass(frozen=True)
class RegisterCompany:
    """First register row with the mapped status."""

    name: str
    status: str
    legal_form: str | None
    registration_number: str | None
    registration_authority: str | None
    address: str | None
    raw_status: str

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "name": self.name,
            "status": self.status,
            "legal_form": self.legal_form,
            "registration_number": self.registration_number,
            "registration_authority": self.registration_authority,
            "address": self.address,
            "raw_status": self.raw_status,
        }


@dataclass(frozen=True)
class RegisterLookup:
    """``FOUND``, ``NOT_FOUND`` or ``UNAVAILABLE`` — the last is never "not in register"."""

    status: str
    company: RegisterCompany | None = None
    candidates: int = 0
    error: str | None = None

    def to_dict(self) -> JsonObject:
        """JSON view."""
        return {
            "status": self.status,
            "company": None if self.company is None else self.company.to_dict(),
            "candidates": self.candidates,
            "error": self.error,
        }


def register_status(raw: str, profile: RegistryProfile) -> str:
    """Map an OffeneRegister status text with the profile's words (else ``unknown``)."""
    words = profile.setting("register_status")
    text = (raw or "").lower()
    if any(w in text for w in words["dissolved"]):
        return "dissolved"
    if any(w in text for w in words["active"]):
        return "active"
    return "unknown"


def parse_register_rows(body: bytes, profile: RegistryProfile) -> RegisterLookup:
    """Datasette ``_shape=objects`` answer → first company (as the source)."""
    try:
        data = json.loads(body)
        rows = data["rows"]
        if not isinstance(rows, list):
            raise TypeError("rows")
    except (ValueError, KeyError, TypeError) as exc:
        raise ParserError(f"Registerantwort nicht lesbar: {exc!r}") from exc
    if not rows:
        return RegisterLookup("NOT_FOUND")
    row = rows[0]
    raw = str(row.get("current_status") or "")
    return RegisterLookup(
        "FOUND",
        RegisterCompany(
            name=str(row.get("name", "")),
            status=register_status(raw, profile),
            legal_form=row.get("company_type"),
            registration_number=row.get("company_number"),
            registration_authority=row.get("native_company_number"),
            address=row.get("registered_address"),
            raw_status=raw,
        ),
        candidates=len(rows),
    )


def lookup_register(
    transport: Transport, name: str, profile: RegistryProfile, *, timeout: float = 15.0
) -> RegisterLookup:
    """One datasette request; transport failures become ``UNAVAILABLE``."""
    url, params = register_query(name, limit=int(profile.setting("register_query")["limit"]))
    try:
        response = raise_for_status(transport.request("GET", url, params=params, timeout=timeout))
    except TransportError as exc:
        return RegisterLookup("UNAVAILABLE", error=str(exc))
    return parse_register_rows(response.body, profile)
