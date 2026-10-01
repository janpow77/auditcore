"""Deterministische Generatoren für formattreue und natürlich wirkende Pseudonyme."""

from __future__ import annotations

import hashlib
import re
import unicodedata

from .names import (
    COMPANY_PREFIXES,
    COMPANY_SUFFIXES,
    EMAIL_DOMAIN,
    FIRST_NAMES,
    IBAN_LENGTHS,
    LAST_NAMES,
    LEGAL_FORMS,
    NULL_BANK_CODE_DE,
    PHONE_BLOCK,
    PHONE_PREFIX,
)


def compute_index(salt: str, entity_type: str, original: str, attempt: int) -> int:
    """Berechnet einen deterministischen Hash-Index für einen Ersatzkandidaten."""
    raw = f"{salt}|{entity_type}|{original}|{attempt}".encode()
    return int.from_bytes(hashlib.blake2b(raw, digest_size=8).digest(), "big")


def clean_ascii_slug(text: str) -> str:
    """Wandelt Umlaute und Sonderzeichen in einen sicheren ASCII-Bezeichner um."""
    replaced = text
    for src, target in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        replaced = replaced.replace(src, target).replace(src.upper(), target)
    normalized = unicodedata.normalize("NFKD", replaced.lower())
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = "".join(ch for ch in ascii_only if ch.isalnum() or ch in "._-")
    return slug or "kontakt"


def detect_legal_form(name: str) -> str | None:
    """Ermittelt die Rechtsform am Ende eines Firmennamens."""
    cleaned = name.rstrip(" .,;")
    for form in LEGAL_FORMS:
        if cleaned.endswith(form):
            return form
    return None


def generate_person_pseudonym(salt: str, original: str, attempt: int) -> str:
    """Erzeugt einen Personennamen mit derselben Wortzahl wie das Original."""
    idx = compute_index(salt, "person_name", original, attempt)
    last = LAST_NAMES[idx % len(LAST_NAMES)]
    words = original.strip().split()
    if len(words) <= 1:
        return last
    first = FIRST_NAMES[(idx // len(LAST_NAMES)) % len(FIRST_NAMES)]
    return f"{first} {last}"


def generate_company_pseudonym(salt: str, original: str, attempt: int) -> str:
    """Erzeugt einen Firmennamen mit Beibehaltung der erkannten Rechtsform."""
    idx = compute_index(salt, "company_name", original, attempt)
    prefix = COMPANY_PREFIXES[idx % len(COMPANY_PREFIXES)]
    suffix = COMPANY_SUFFIXES[(idx // len(COMPANY_PREFIXES)) % len(COMPANY_SUFFIXES)]
    form = detect_legal_form(original)
    if form:
        return f"{prefix} {suffix} {form}"
    return f"{prefix} {suffix}"


def iban_check_digits(country: str, bban: str) -> str:
    """Berechnet die beiden Prüfziffern zu einem IBAN-Rumpf nach ISO 13616."""
    rearranged = f"{bban}{country}00"
    digits = "".join(str(int(ch, 36)) for ch in rearranged.upper())
    remainder = int(digits) % 97
    check = 98 - remainder
    return f"{check:02d}"


def is_valid_iban(iban: str) -> bool:
    """Prüft eine IBAN nach ISO 13616 (MOD 97-10)."""
    compact = re.sub(r"[\s\-]", "", iban).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", compact):
        return False
    expected_len = IBAN_LENGTHS.get(compact[:2])
    if expected_len is not None and len(compact) != expected_len:
        return False
    rearranged = compact[4:] + compact[:4]
    digits = "".join(str(int(ch, 36)) for ch in rearranged)
    return int(digits) % 97 == 1


def generate_iban_pseudonym(salt: str, original: str, attempt: int) -> str:
    """Erzeugt eine formattreue, prüfzifferngültige IBAN ohne reales Institut."""
    compact = "".join(ch for ch in original.upper() if ch.isalnum())
    country = compact[:2] if len(compact) >= 2 and compact[:2].isalpha() else "DE"
    target_len = IBAN_LENGTHS.get(country, len(compact) if len(compact) > 8 else 22)
    bban_len = max(target_len - 4, 8)
    idx = compute_index(salt, "iban", original, attempt)
    digits = f"{idx}".rjust(bban_len, "0")[-bban_len:]
    if country == "DE":
        digits = NULL_BANK_CODE_DE + digits[len(NULL_BANK_CODE_DE) :]
    check = iban_check_digits(country, digits)
    full = f"{country}{check}{digits}"
    return " ".join(full[i : i + 4] for i in range(0, len(full), 4))


def generate_email_pseudonym(salt: str, original: str, attempt: int) -> str:
    """Erzeugt eine formattreue E-Mail-Adresse unter der RFC-2606-Beispieldomäne."""
    idx = compute_index(salt, "email", original, attempt)
    first = FIRST_NAMES[idx % len(FIRST_NAMES)]
    last = LAST_NAMES[(idx // len(FIRST_NAMES)) % len(LAST_NAMES)]
    company = COMPANY_PREFIXES[(idx // 97) % len(COMPANY_PREFIXES)]
    local = f"{clean_ascii_slug(first)}.{clean_ascii_slug(last)}"
    domain = clean_ascii_slug(company)
    return f"{local}@{domain}.{EMAIL_DOMAIN}"


def generate_phone_pseudonym(salt: str, original: str, attempt: int) -> str:
    """Erzeugt eine formattreue Rufnummer im reservierten Prüfbereich."""
    idx = compute_index(salt, "phone", original, attempt)
    suffix_number = idx % 10000
    return f"{PHONE_PREFIX} {PHONE_BLOCK} {suffix_number:04d}"


def generate_placeholder(label: str, counter: int) -> str:
    """Erzeugt eine nummerierte Platzhaltermarke."""
    return f"[{label} {counter}]"
