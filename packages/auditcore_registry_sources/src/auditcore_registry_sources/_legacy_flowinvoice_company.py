"""flowinvoice replays: VIES text check, register answer and company verification."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, TypedDict

from . import company
from ._legacy_shared import _profile
from ._legacy_types import RegisterCompanyInfo, VatValidation


def flowinvoice_validate_vat(
    vat_id: str, *, response_text: str | None = None, error: str | None = None
) -> VatValidation:
    """``CompanyVerifier.validate_vat_id`` without ``request_date`` (text search for ``valid``)."""
    compact = vat_id.replace(" ", "").upper()
    match = re.match(r"^([A-Z]{2})(.+)$", compact)
    if not match:
        return {
            "is_valid": False,
            "vat_id": compact,
            "country_code": "",
            "company_name": None,
            "company_address": None,
            "error_message": "Ungültiges Format",
        }
    country = match.group(1)
    if response_text is None:
        return {
            "is_valid": False,
            "vat_id": compact,
            "country_code": country,
            "company_name": None,
            "company_address": None,
            "error_message": error,
        }
    name = re.search(r"<name>(.+?)</name>", response_text, re.DOTALL)
    address = re.search(r"<address>(.+?)</address>", response_text, re.DOTALL)
    return {
        "is_valid": "<valid>true</valid>" in response_text.lower(),
        "vat_id": compact,
        "country_code": country,
        "company_name": name.group(1).strip() if name else None,
        "company_address": address.group(1).strip() if address else None,
        "error_message": None,
    }


def flowinvoice_register_accepts(name: str) -> bool:
    """Input check of ``search_offene_register`` (the source then builds SQL text from the name).

    The library itself sends bound parameters (:func:`company.register_query`);
    the recorded legacy request text is reproduced only in the tests.
    """
    return len(name) <= 100 and bool(re.match(r"^[\w\s\.\-\,\&\(\)GmbH]+$", name))


def flowinvoice_register_company(
    status: int, body: Mapping[str, Any] | None
) -> RegisterCompanyInfo | None:
    """Result of ``search_offene_register`` for a recorded answer."""
    if status != 200 or body is None:
        return None
    rows = body.get("rows", [])
    if not rows:
        return None
    row = rows[0]
    text = row.get("current_status", "").lower()
    if "dissolved" in text or "liquidation" in text:
        state = "dissolved"
    elif "registered" in text:
        state = "active"
    else:
        state = "unknown"
    return {
        "name": row.get("name", ""),
        "legal_form": row.get("company_type"),
        "status": state,
        "registration_number": row.get("company_number"),
        "registration_authority": row.get("native_company_number"),
        "address": row.get("registered_address"),
        "founded_date": None,
        "directors": [],
        "source": "offeneregister.de",
    }


def flowinvoice_normalize_company_name(name: str) -> str:
    """``_normalize_company_name``: legal forms removed as *substrings* (``Hagen AG → hen``)."""
    forms = _profile("flowinvoice.company_verification").setting("legal_forms")
    name = name.lower().strip()
    for form in sorted(forms, key=len, reverse=True):
        name = name.replace(form, "").strip()
    return " ".join(name.split())


def flowinvoice_names_match(a: str, b: str) -> bool:
    """``_names_match`` with the substring normalisation."""
    rule = _profile("flowinvoice.company_verification").setting("name_match")
    n1, n2 = flowinvoice_normalize_company_name(a), flowinvoice_normalize_company_name(b)
    if n1 == n2 or n1 in n2 or n2 in n1:
        return True
    w1, w2 = n1.split()[: int(rule["leading_words"])], n2.split()[: int(rule["leading_words"])]
    if w1 and w2:
        common = len(set(w1) & set(w2))
        if common >= min(len(w1), len(w2)) * float(rule["threshold"]):
            return True
    return False


class CompanyCheck(TypedDict):
    """``verify_company`` result; the VIES and register results are passed through."""

    is_verified: bool
    vat_validation: Mapping[str, Any] | None
    company_info: Mapping[str, Any] | None
    risk_indicators: list[str]
    verification_score: float


def flowinvoice_verify_company(
    name: str,
    *,
    vat: Mapping[str, Any] | None,
    register: Mapping[str, Any] | None,
    country: str = "DE",
) -> CompanyCheck:
    """``verify_company`` from recorded VIES/register results (``None`` register = not found)."""
    profile = _profile("flowinvoice.company_verification")
    indicators = []
    if vat is not None:
        if not vat["is_valid"]:
            if vat.get("error_message") and "SERVICE_UNAVAILABLE" in vat["error_message"]:
                indicators.append("VIES_SERVICE_UNAVAILABLE")
            else:
                indicators.append("INVALID_VAT_ID")
        elif vat.get("company_name") and not flowinvoice_names_match(name, vat["company_name"]):
            indicators.append("VAT_NAME_MISMATCH")
    if country == "DE":
        if register:
            if register["status"] == "dissolved":
                indicators.append("COMPANY_DISSOLVED")
            elif register["status"] == "inactive":
                indicators.append("COMPANY_INACTIVE")
        else:
            indicators.append("NOT_IN_REGISTER")
    verified, score = company.score_indicators(indicators, profile)
    return {
        "is_verified": verified,
        "vat_validation": vat,
        "company_info": register,
        "risk_indicators": indicators,
        "verification_score": score,
    }
