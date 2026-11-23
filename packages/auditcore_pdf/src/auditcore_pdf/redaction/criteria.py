"""Suchkriterien: Muster und Begriffe als reguläre Ausdrücke mit Prüffunktion."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from auditcore_common.json_values import JsonObject

from auditcore_pdf.redaction.common import _HYPHENS, MAX_TERM_LENGTH, MAX_TERMS, RedactionError
from auditcore_pdf.redaction.patterns import PATTERNS, Validator


@dataclass(frozen=True)
class Criteria:
    """Gewählte Muster und Begriffe eines Durchgangs."""

    patterns: tuple[str, ...] = ()
    terms: tuple[str, ...] = ()
    case_sensitive: bool = False
    whole_word: bool = True

    @classmethod
    def from_input(
        cls,
        patterns: Iterable[str] = (),
        terms: Iterable[str] = (),
        case_sensitive: bool = False,
        whole_word: bool = True,
    ) -> Criteria:
        pattern_list = list(dict.fromkeys(p for p in patterns))
        unknown = [p for p in pattern_list if p not in PATTERNS]
        if unknown:
            raise RedactionError(f"Unbekannte Muster: {', '.join(unknown)}")
        term_list = list(dict.fromkeys(t.strip() for t in terms if t and t.strip()))
        if len(term_list) > MAX_TERMS:
            raise RedactionError(
                f"Höchstens {MAX_TERMS} Begriffe je Durchgang ({len(term_list)} angegeben)"
            )
        too_long = [t for t in term_list if len(t) > MAX_TERM_LENGTH]
        if too_long:
            raise RedactionError(f"Begriffe dürfen höchstens {MAX_TERM_LENGTH} Zeichen lang sein")
        return cls(tuple(pattern_list), tuple(term_list), bool(case_sensitive), bool(whole_word))

    def to_dict(self) -> JsonObject:
        return {
            "patterns": list(self.patterns),
            "terms": list(self.terms),
            "case_sensitive": self.case_sensitive,
            "whole_word": self.whole_word,
        }


@dataclass(frozen=True)
class _Rule:
    source: str
    regex: re.Pattern[str]
    validate: Validator | None = None
    is_term: bool = False


def _term_part(word: str, case_sensitive: bool) -> str:
    out: list[str] = []
    i = 0
    while i < len(word):
        ch = word[i]
        if ch in _HYPHENS:
            # Doppelnamen dürfen am Bindestrich umbrechen („Müller-“ / „Lüdenscheidt“).
            out.append(r"-\s*")
        elif not case_sensitive and ch in "ßẞ":
            out.append("(?:ß|ẞ|ss)")
        elif not case_sensitive and word[i : i + 2].lower() == "ss":
            out.append("(?:ss|ß|ẞ)")
            i += 1
        else:
            out.append(re.escape(ch))
        i += 1
    return "".join(out)


def _term_regex(term: str, case_sensitive: bool, whole_word: bool) -> re.Pattern[str]:
    # Leerraum im Begriff trifft jeden Leerraum im Text, auch einen Zeilenumbruch.
    # NFKC wie im Seitentext, damit Ligaturen und Sonderformen gleich verglichen werden.
    term = unicodedata.normalize("NFKC", term)
    body = r"\s+".join(_term_part(part, case_sensitive) for part in term.split())
    if whole_word:
        body = rf"(?<!\w){body}(?!\w)"
    return re.compile(body, 0 if case_sensitive else re.IGNORECASE)


def _rules(criteria: Criteria) -> list[_Rule]:
    case, whole = criteria.case_sensitive, criteria.whole_word
    rules = [
        _Rule(f"begriff:{t}", _term_regex(t, case, whole), is_term=True) for t in criteria.terms
    ]
    for key in criteria.patterns:
        spec = PATTERNS[key]
        if not spec.ai:
            rules.append(_Rule(key, re.compile(spec.regex, spec.flags), spec.validate))
    return rules


def _matches(rule: _Rule, text: str) -> Iterator[tuple[int, int]]:
    for m in rule.regex.finditer(text):
        start, end = m.span()
        if start == end:
            continue
        span = rule.validate(text, start, end) if rule.validate else (start, end)
        if span:
            yield span
