"""``flowaudit:rechtsgrundlage``: Freitext (Schema 1.0) und strukturierte Fundstelle (1.1).

Normalform ist die ausgeschriebene Fassung („Artikel 73 Absatz 2 Buchstabe b
der Verordnung (EU) 2021/1060“), die Kurzform („Art. 73 Abs. 2 Buchst. b
VO (EU) 2021/1060“) dient der Anzeige.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from .mapping import xml_field

_ACT_LONG = (
    (re.compile(r"^Delegierte\s+VO\b"), "Delegierte Verordnung"),
    (re.compile(r"^Durchführungs-?VO\b"), "Durchführungsverordnung"),
    (re.compile(r"^DVO\b"), "Durchführungsverordnung"),
    (re.compile(r"^VO\b"), "Verordnung"),
    (re.compile(r"^RL\b"), "Richtlinie"),
)
_ACT_SHORT = (
    ("Delegierte Verordnung", "Delegierte VO"),
    ("Durchführungsverordnung", "Durchführungs-VO"),
    ("Verordnung", "VO"),
    ("Richtlinie", "RL"),
)
_GENITIVE = {
    "Verordnung": "der Verordnung",
    "Delegierte Verordnung": "der Delegierten Verordnung",
    "Durchführungsverordnung": "der Durchführungsverordnung",
    "Richtlinie": "der Richtlinie",
    "Beschluss": "des Beschlusses",
    "Entscheidung": "der Entscheidung",
}
#: (Feld, Kurzform, Langform) der Untergliederung in Zitierreihenfolge.
_SUBDIVISIONS = (
    ("paragraph", "Abs.", "Absatz"),
    ("subparagraph", "UAbs.", "Unterabsatz"),
    ("sentence", "S.", "Satz"),
    ("point", "Buchst.", "Buchstabe"),
    ("number", "Nr.", "Nummer"),
)


def act_long(act: str) -> str:
    """Ausgeschriebener Normname (``VO`` → ``Verordnung``)."""
    value = " ".join(act.split())
    for pattern, replacement in _ACT_LONG:
        if pattern.search(value):
            return pattern.sub(replacement, value, count=1)
    return value


def act_short(act: str) -> str:
    """Kurzer Normname für die Anzeige (``Verordnung`` → ``VO``)."""
    value = act_long(act)
    for long, short in _ACT_SHORT:
        if value.startswith(long):
            return short + value[len(long) :]
    return value


def _act_with_article(act: str) -> str:
    value = act_long(act)
    for head, genitive in _GENITIVE.items():
        if value == head or value.startswith(head + " "):
            return genitive + value[len(head) :]
    return value


@dataclass(frozen=True)
class LegalBasis:
    """Rechtsgrundlage; ``article``/``section``/``annex`` enthalten nur die Kennung."""

    text: str | None = xml_field("", "body")
    id: str | None = xml_field("id")
    act: str | None = xml_field("norm")
    article: str | None = xml_field("artikel")
    section: str | None = xml_field("paragraph")
    annex: str | None = xml_field("anhang")
    paragraph: str | None = xml_field("absatz")
    subparagraph: str | None = xml_field("unterabsatz")
    sentence: str | None = xml_field("satz")
    point: str | None = xml_field("buchstabe")
    number: str | None = xml_field("nummer")
    version: str | None = xml_field("fassung")
    eli: str | None = xml_field("eli")
    celex: str | None = xml_field("celex")
    url: str | None = xml_field("url")
    short_title: str | None = xml_field("kurzbezeichnung")
    note: str | None = xml_field("anmerkung")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)

    @property
    def is_structured(self) -> bool:
        """``True``, wenn mindestens ein Strukturfeld gesetzt ist."""
        return any(
            (
                self.act,
                self.article,
                self.section,
                self.annex,
                self.paragraph,
                self.subparagraph,
                self.sentence,
                self.point,
                self.number,
            )
        )

    def _administrative_rule(self, short: bool) -> str | None:
        """``VV zu § 44 LHO`` mit Nummer → „VV Nummer 4.2 zu § 44 LHO“."""
        if (
            self.act
            and self.act.startswith("VV zu ")
            and self.number
            and not (self.article or self.section or self.annex)
        ):
            return f"VV {'Nr.' if short else 'Nummer'} {self.number} {self.act[3:]}"
        return None

    def _parts(self, short: bool) -> list[str]:
        parts: list[str] = []
        if self.article:
            parts.append(f"{'Art.' if short else 'Artikel'} {self.article}")
        elif self.section:
            parts.append(f"§ {self.section}")
        elif self.annex:
            parts.append(f"Anhang {self.annex}")
        for name, short_label, long_label in _SUBDIVISIONS:
            value = getattr(self, name)
            if value:
                parts.append(f"{short_label if short else long_label} {value}")
        return parts

    def citation(self) -> str:
        """Ausgeschriebene Normalform; ohne Struktur der Freitext."""
        if not self.is_structured:
            return (self.text or "").strip()
        if rule := self._administrative_rule(short=False):
            return rule
        parts = self._parts(short=False)
        if self.act:
            linked = (self.article or self.annex) and parts
            parts.append(_act_with_article(self.act) if linked else act_long(self.act))
        return " ".join(parts)

    def short_citation(self) -> str:
        """Kurzform für die Anzeige."""
        if not self.is_structured:
            return (self.text or "").strip()
        if rule := self._administrative_rule(short=True):
            return rule
        parts = self._parts(short=True)
        if self.act:
            parts.append(act_short(self.act))
        return " ".join(parts)

    @property
    def display(self) -> str:
        """Lesbare Angabe: Freitext, sonst Kurzform."""
        return (self.text or "").strip() or self.short_citation()

    def normalized(self) -> LegalBasis:
        """Norm in Langform, Textinhalt = ausgeschriebene Normalform."""
        if not self.is_structured:
            return self
        result = replace(self, act=act_long(self.act) if self.act else None)
        return replace(result, text=result.citation())
