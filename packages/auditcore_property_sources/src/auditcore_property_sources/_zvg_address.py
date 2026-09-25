"""ZVG address recognition: street, house number, postal code and city of a notice text."""

from __future__ import annotations

import re

from ._zvg_text import clean

STREET_SUFFIX = (
    r"(?:stra(?:ße|sse)|str\.?|weg|platz|allee|gasse|ring|damm|ufer|pfad|"
    r"steig|berg|markt|hof|chaussee|promenade|wiesen|feld|acker|grund|litt)"
)
HOUSE_NO = r"\d+\s*[a-zA-Z]?(?:\s*[-+/,]\s*\d+\s*[a-zA-Z]?)*"
RE_NOT_STREET = re.compile(
    r"(?i)\b(?:flur(?:stück)?|gemarkung|grundbuch|blatt|band|gew\.?|zimmer|whg\.?|wohnung)\b"
)
RE_STREET_PREPOSITION = re.compile(
    r"(?i)^(?:am|an|auf|im|in|bei|beim|zum|zur|unterm?|vorm?|hinterm?)\b"
)

Address = tuple[str | None, str | None, str | None, str | None]


def _postal_code_and_city(src: str) -> tuple[str | None, str | None]:
    found = re.search(r"\b(\d{5})\s+([^,;()]+?)(?:,|$)", src)
    if not found:
        return None, None
    return found.group(1), clean(found.group(2))


def _street_with_number(src: str) -> re.Match[str] | None:
    """Street and house number directly before ``, PLZ``."""
    found = re.search(
        rf"([^,;:()]*?{STREET_SUFFIX}[^,;:()]*?)\s+({HOUSE_NO})\s*,\s*\d{{5}}\s+",
        src,
        re.IGNORECASE,
    )
    if found:
        return found
    found = re.search(rf"([A-ZÄÖÜ][^,;:()0-9]{{2,60}}?)\s+({HOUSE_NO})\s*,\s*\d{{5}}\s+", src)
    if found and RE_NOT_STREET.search(found.group(1)):
        return None
    return found


def _looks_like_bare_street(candidate: str) -> bool:
    """A street name without number: suffix or preposition, short, capitalised, no digits."""
    looks_like_street = bool(
        re.search(rf"(?i){STREET_SUFFIX}\b", candidate) or RE_STREET_PREPOSITION.search(candidate)
    )
    return (
        looks_like_street
        and 3 <= len(candidate) <= 60
        and candidate[0].isupper()
        and not any(ch.isdigit() for ch in candidate)
        and len(candidate.split()) <= 5
        and not RE_NOT_STREET.search(candidate)
    )


def _street_before_postal_code(before_plz: str) -> tuple[str | None, str | None]:
    """Street (and number) in the text before the postal code."""
    found = re.search(
        rf"([^,;:()]*?{STREET_SUFFIX}[^,;:()]*?)\s+(\d+\s*[a-zA-Z]?)\s*,?\s*$",
        before_plz,
        re.IGNORECASE,
    )
    if found:
        return clean(found.group(1)), clean(found.group(2))[:32]
    found = re.search(r"([^,;:()]+?)\s*,\s*$", before_plz)
    if not found:
        return None, None
    candidate = clean(found.group(1))
    return (candidate if _looks_like_bare_street(candidate) else None), None


def extract_address(text: str) -> Address:
    """``(street, house_number, postal_code, city)``; only safely recognised parts."""
    src = clean(text)
    if not src:
        return None, None, None, None
    postal_code, city = _postal_code_and_city(src)
    street: str | None = None
    house_number: str | None = None
    found = _street_with_number(src)
    if found:
        street, house_number = clean(found.group(1)), clean(found.group(2))[:32]
    elif postal_code:
        street, house_number = _street_before_postal_code(src[: src.find(postal_code)])
    if street and street.lower() in {"e", "str", "str.", "straße", "strasse"}:
        street = None
    if postal_code == "00000":
        postal_code = None
    return street, house_number, postal_code, city


def expand_street(street: str | None) -> str | None:
    """Write out ``…str.``/``…pl.`` abbreviations (``Graubergerstr.`` → ``Graubergerstraße``)."""
    if not street:
        return street
    s = street
    s = re.sub(r"(?i)([a-zäöüß])str\.?(?=\s|,|$)", r"\1straße", s)
    s = re.sub(r"(?i)([a-zäöüß])pl\.?(?=\s|,|$)", r"\1platz", s)
    s = re.sub(r"(?i)\bstr\.?(?=\s|,|$)", "Straße", s)
    return re.sub(r"\s+", " ", s).strip()


def normalized_street(street: str | None) -> str:
    """Comparison form of a street name (original ``_norm_street``)."""
    s = expand_street(street) or ""
    return re.sub(r"[\s.\-]", "", s).lower()
