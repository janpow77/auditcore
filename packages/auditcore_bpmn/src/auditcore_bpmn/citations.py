"""Normzitate erkennen und EU-Rechtsakte auflösen (CELEX, ELI, EUR-Lex-URL).

Rein syntaktisch, ohne Netzwerkzugriff. Erkannt werden die ausgeschriebene
Form („Artikel 73 Absatz 2 Buchstabe b der Verordnung (EU) 2021/1060“), die
Kurzform („Art. 74 Abs. 2 UAbs. 2“), Paragraphen („§ 44 Absatz 1 LHO“,
„§§ 23 und 44 LHO“), Verwaltungsvorschriften („VV Nummer 4.2 zu § 44 LHO“)
und Anhänge. Ergebnisse sind Vorschläge; übernommen werden sie durch die Anwendung.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from typing import Protocol

from .extensions import LegalBasis, act_long


@dataclass(frozen=True)
class NormResolution:
    """Ergebnis der Auflösung eines Normnamens."""

    act: str
    celex: str | None = None
    eli: str | None = None
    url: str | None = None
    short_title: str | None = None
    document_type: str | None = None
    programming_period: str | None = None
    source: str = "syntaktisch"
    catalogued: bool = False


class NormResolver(Protocol):
    """Port zur Normauflösung (z. B. :class:`auditcore_bpmn.legal.LegalSourcesNormResolver`)."""

    def resolve(self, act: str) -> NormResolution | None:
        """Auflösung eines Normnamens oder ``None``."""


_EU_ACT = re.compile(
    r"(?P<kind>Delegierte(?:n)? Verordnung|Durchführungsverordnung|Verordnung|Richtlinie|Beschluss|Entscheidung)"
    r"\s*\((?:EU|EG|EWG|EU,\s*Euratom|EG,\s*Euratom)\)\s*(?P<nr>Nr\.\s*)?(?P<a>\d{1,4})/(?P<b>\d{1,4})"
)
_OLD_DIRECTIVE = re.compile(r"Richtlinie\s+(?P<a>\d{4})/(?P<b>\d{1,4})/(?:EU|EG|EWG)")
_ELI_KIND = {
    "Verordnung": "reg",
    "Delegierte Verordnung": "reg_del",
    "Delegierten Verordnung": "reg_del",
    "Durchführungsverordnung": "reg_impl",
    "Richtlinie": "dir",
    "Beschluss": "dec",
    "Entscheidung": "dec",
}
_CELEX_TYPE = {"reg": "R", "reg_del": "R", "reg_impl": "R", "dir": "L", "dec": "D"}


def _is_year(value: int) -> bool:
    return 1950 <= value <= 2100


def eu_act(act: str) -> tuple[str, int, int] | None:
    """``(ELI-Art, Jahr, Nummer)`` eines EU-Rechtsakts oder ``None``.

    Ab 2015 lautet die Zählung ``Jahr/Nummer``, davor ``Nr. Nummer/Jahr``;
    Richtlinien stets ``Jahr/Nummer``.
    """
    text = act_long(act)
    match = _EU_ACT.search(text)
    if match:
        kind, first, second = _ELI_KIND[match["kind"]], int(match["a"]), int(match["b"])
        number_first = kind != "dir" and (match["nr"] or (_is_year(second) and not _is_year(first)))
        year, number = (second, first) if number_first else (first, second)
        return (kind, year, number) if _is_year(year) else None
    match = _OLD_DIRECTIVE.search(text)
    return ("dir", int(match["a"]), int(match["b"])) if match else None


class EuActResolver:
    """Syntaktische Auflösung von EU-Rechtsakten ohne Katalog."""

    def resolve(self, act: str) -> NormResolution | None:
        """CELEX, ELI und EUR-Lex-URL eines EU-Rechtsakts oder ``None``."""
        found = eu_act(act)
        if found is None:
            return None
        kind, year, number = found
        celex = f"3{year}{_CELEX_TYPE[kind]}{number:04d}"
        return NormResolution(
            act=act_long(act),
            celex=celex,
            eli=f"http://data.europa.eu/eli/{kind}/{year}/{number}/oj",
            url=f"https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:{celex}",
        )


def enrich(legal_basis: LegalBasis, resolver: NormResolver | None = None) -> LegalBasis:
    """Füllt fehlende CELEX-/ELI-/URL-/Kurzbezeichnung; vorhandene Angaben bleiben."""
    if not legal_basis.act:
        return legal_basis
    result = (resolver or EuActResolver()).resolve(legal_basis.act)
    if result is None:
        return legal_basis
    return replace(
        legal_basis,
        celex=legal_basis.celex or result.celex,
        eli=legal_basis.eli or result.eli,
        url=legal_basis.url or result.url,
        short_title=legal_basis.short_title or result.short_title,
    )


# ---------------------------------------------------------------------------
# Zitate in Freitext
# ---------------------------------------------------------------------------

_EU_ACT_TEXT = (
    r"(?:(?:Delegierten|Durchführungs)\s*)?(?:Verordnung|Richtlinie|VO|RL)\s*"
    r"\((?:EU|EG|EWG|EU,\s*Euratom|EG,\s*Euratom)\)\s*(?:Nr\.\s*)?\d{1,4}/\d{1,4}"
)
_LONG_PARTS = (
    r"(?:\s+(?:Absatz|Abs\.)\s+(?P<abs>\d+[a-z]?))?(?:\s+Unterabsatz\s+(?P<uabs>\d+))?"
    r"(?:\s+(?:Satz|S\.)\s+(?P<satz>\d+))?(?:\s+Buchstabe\s+(?P<buchst>[a-z]{1,3}))?"
    r"(?:\s+(?:Nummer|Nr\.|Ziffer)\s+(?P<nr>[\divx.]+))?"
)
_SHORT_PARTS = (
    r"(?:\s*Abs\.\s*(?P<abs>\d+[a-z]?))?(?:\s*UAbs\.\s*(?P<uabs>\d+))?"
    r"(?:\s*(?:S\.|Satz)\s*(?P<satz>\d+))?(?:\s*(?:Buchst\.|lit\.)\s*(?P<buchst>[a-z]{1,3}))?"
    r"(?:\s*(?:Nr\.|Ziff\.)\s*(?P<nr>[\divx.]+))?"
)
_NATIONAL_ACT = r"(?P<norm>(?:[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]*[A-ZÄÖÜ][A-Za-zÄÖÜäöüß]*|UVgO|VgV|GWB))\b"
_LONG = re.compile(
    r"(?:Artikel\s+(?P<art>\d+[a-z]?)|Anhang\s+(?P<anh>[IVXLC]+))"
    + _LONG_PARTS
    + r"\s+(?:der|des)\s+(?P<norm>"
    + _EU_ACT_TEXT
    + r")"
)
_SHORT = re.compile(
    r"Art\.\s*(?P<art>\d+[a-z]?)" + _SHORT_PARTS + r"(?:\s+(?P<norm>" + _EU_ACT_TEXT + r"|CPR|Dach-VO))?"
)
_SECTION = re.compile(r"§\s*(?P<par>\d+[a-z]?)" + _LONG_PARTS + r"\s+" + _NATIONAL_ACT)
_SECTIONS = re.compile(r"§§\s*(?P<liste>\d+[a-z]?(?:\s*(?:,|und|bis)\s*\d+[a-z]?)+)\s+" + _NATIONAL_ACT)
_ADMIN_RULE = re.compile(r"VV\s+(?:Nummer|Nr\.)\s*(?P<nr>[\d.]+)\s+zu\s+§\s*(?P<par>\d+[a-z]?)\s+" + _NATIONAL_ACT)


@dataclass(frozen=True)
class CitationMatch:
    """Ein erkanntes Zitat mit Fundstelle im Text."""

    legal_basis: LegalBasis
    start: int
    end: int
    text: str
    form: str


def _group(match: re.Match[str], name: str) -> str | None:
    try:
        value = match.group(name)
    except IndexError:
        return None
    return value.strip() if value else None


def _legal_basis(match: re.Match[str], act: str | None, **anchor: str | None) -> LegalBasis:
    """Rechtsgrundlage mit Untergliederung aus den benannten Gruppen des Treffers."""
    return LegalBasis(
        act=act,
        article=anchor.get("article"),
        section=anchor.get("section"),
        annex=anchor.get("annex"),
        paragraph=_group(match, "abs"),
        subparagraph=_group(match, "uabs"),
        sentence=_group(match, "satz"),
        point=_group(match, "buchst"),
        number=_group(match, "nr"),
    )


def _admin_rule(match: re.Match[str]) -> list[LegalBasis]:
    return [LegalBasis(act=f"VV zu § {match['par']} {match['norm']}", number=match["nr"])]


def _long(match: re.Match[str]) -> list[LegalBasis]:
    return [_legal_basis(match, match["norm"], article=_group(match, "art"), annex=_group(match, "anh"))]


def _short(match: re.Match[str]) -> list[LegalBasis]:
    return [_legal_basis(match, _group(match, "norm"), article=match["art"])]


def _sections(match: re.Match[str]) -> list[LegalBasis]:
    return [LegalBasis(act=match["norm"], section=number) for number in re.findall(r"\d+[a-z]?", match["liste"])]


def _section(match: re.Match[str]) -> list[LegalBasis]:
    return [_legal_basis(match, match["norm"], section=match["par"])]


#: Reihenfolge = Vorrang bei Überlappung.
_PATTERNS: tuple[tuple[str, re.Pattern[str], Callable[[re.Match[str]], list[LegalBasis]]], ...] = (
    ("vv", _ADMIN_RULE, _admin_rule),
    ("lang", _LONG, _long),
    ("kurz", _SHORT, _short),
    ("paragraphen", _SECTIONS, _sections),
    ("paragraph", _SECTION, _section),
)


def _matches(text: str) -> Iterator[CitationMatch]:
    taken: list[tuple[int, int]] = []
    for form, pattern, build in _PATTERNS:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if any(span[1] > start and span[0] < end for start, end in taken):
                continue
            taken.append(span)
            for legal_basis in build(match):
                yield CitationMatch(legal_basis.normalized(), span[0], span[1], match.group(0), form)


def find_citations(text: str | None) -> list[CitationMatch]:
    """Normzitate in Freitext (z. B. ``bpmn:documentation``), überlappungsfrei, nach Position."""
    if not text:
        return []
    return sorted(_matches(text), key=lambda hit: (hit.start, hit.legal_basis.citation()))


def parse_citation(text: str) -> LegalBasis:
    """Ein einzelnes Zitat strukturiert lesen; ohne eindeutigen Treffer bleibt es Freitext."""
    hits = find_citations(text)
    if len(hits) == 1 and hits[0].text.strip() == text.strip():
        return hits[0].legal_basis
    return LegalBasis(text=text.strip() or None)
