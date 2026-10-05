"""Gemeinsame Begriffs- und Mustererkennung für Schwärzung, Bereinigung und Nachprüfung."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from auditcore_pdf.models import STANDARD_PATTERNS, RedactionPattern

#: Zwischen zwei Zeichen eines Begriffs darf eine Silbentrennung am Zeilenende stehen
#: („vertrau-⏎licher“) oder ein weiches Trennzeichen (U+00AD).
_HYPHEN_BREAK = r"(?:-\s+|­\s*)?"

PatternSpec = str | RedactionPattern


def term_regex(term: str, whole_word: bool = False) -> str:
    """Baut den Suchausdruck eines Begriffs, tolerant gegenüber Zeilenumbruch und Trennung.

    Leerraum im Begriff passt auf beliebigen Leerraum einschließlich Zeilenumbruch;
    ``whole_word`` verlangt, dass vor und nach dem Begriff kein Wortzeichen steht.
    Ein leerer Begriff ergibt einen leeren Ausdruck.
    """
    parts = [_HYPHEN_BREAK.join(re.escape(char) for char in part) for part in term.split()]
    joined = r"\s+".join(parts)
    if joined and whole_word:
        joined = rf"(?<!\w){joined}(?!\w)"
    return joined


def resolve_pattern(spec: PatternSpec) -> RedactionPattern:
    """Löst einen Musternamen aus ``STANDARD_PATTERNS`` auf; sonst gilt die Angabe als Regex."""
    if isinstance(spec, RedactionPattern):
        return spec
    return STANDARD_PATTERNS.get(spec) or RedactionPattern(name=spec, regex=spec)


def match_span(match: re.Match[str]) -> tuple[int, int]:
    """Liefert den zu schwärzenden Bereich: Gruppe ``value``, falls vorhanden, sonst alles."""
    if "value" in match.re.groupindex and match.group("value") is not None:
        return match.span("value")
    return match.span()


@dataclass(frozen=True)
class MatchRule:
    """Ein kompilierter Begriff oder ein kompiliertes Muster."""

    label: str
    regex: re.Pattern[str]
    pattern_name: str | None = None

    @property
    def is_term(self) -> bool:
        """Begriffe tragen keinen Musternamen."""
        return self.pattern_name is None

    def describe(self, match: re.Match[str]) -> str:
        """Meldungstext einer Fundstelle (ohne Ortsangabe)."""
        if self.is_term:
            return f"Fundstelle für verbotenen Begriff '{self.label}'"
        start, end = match_span(match)
        return f"Fundstelle für verbotenes Muster '{self.label}': '{match.string[start:end]}'"


class TextMatcher:
    """Findet Begriffe und Muster in beliebigen Zeichenketten."""

    def __init__(
        self,
        terms: Sequence[str] | None = None,
        patterns: Sequence[PatternSpec] | None = None,
        *,
        case_sensitive: bool = False,
        whole_word: bool = False,
    ) -> None:
        flags = 0 if case_sensitive else re.IGNORECASE
        rules: list[MatchRule] = []
        for term in terms or []:
            regex = term_regex(term, whole_word)
            if regex:
                rules.append(MatchRule(term, re.compile(regex, flags)))
        for spec in patterns or []:
            if not spec:
                continue
            pattern = resolve_pattern(spec)
            rules.append(MatchRule(pattern.regex, re.compile(pattern.regex, flags), pattern.name))
        self.rules = rules

    def __bool__(self) -> bool:
        return bool(self.rules)

    def matches(self, text: str) -> bool:
        """Prüft, ob der Text mindestens einen Treffer enthält."""
        return bool(text) and any(rule.regex.search(text) for rule in self.rules)

    def violations(self, text: str, location: str) -> list[str]:
        """Eine Meldung je Begriff bzw. Muster mit Treffer im Text."""
        if not text:
            return []
        found: list[str] = []
        for rule in self.rules:
            match = rule.regex.search(text)
            if match:
                found.append(f"{location}: {rule.describe(match)}")
        return found


def pattern_regexes(patterns: Sequence[PatternSpec] | None) -> list[str]:
    """Die regulären Ausdrücke der angegebenen Muster (Namen werden aufgelöst)."""
    return [resolve_pattern(spec).regex for spec in patterns or [] if spec]
