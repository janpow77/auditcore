"""Altbestand anreichern: Vorschläge aus Beschriftungen, Dokumentation und Farben.

Viele vorhandene Diagramme tragen fachliche Angaben als Freitext in
``bpmn:documentation`` und in Beschriftungen („Stelle: Aufgabe“), Befunde als
Farbe. :func:`suggest` zieht daraus **Vorschläge**: Rechtsgrundlagen
(Normalform ausgeschrieben), Fundstellen, Prüfbezüge aus
Bewertungskriterien, Feststellungsbezüge („T15 F1“), Prüffelder,
Registerkürzel, Akteur-Rollen und Kennzeichen aus Farben.
:func:`apply_suggestions` übernimmt nur ausgewählte Vorschläge und ergänzt
vorhandene Angaben, ohne sie zu überschreiben.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, replace
from typing import TypeVar

from .citations import find_citations
from .extensions import Actor, AuditReference, CrossReference, Extensions, LegalBasis, Marker, Source, to_dict
from .model import BpmnDocument, as_document
from .namespaces import BIOC_NS, BPMNDI_NS, COLOR_NS, q
from .profiles import Profile, load_profile
from .serialize import serialize
from .writer import set_extensions

#: Farbe (Füllung, Rand) → Kennzeichen-Vorschlag.
COLOR_MARKERS = {
    ("#fce8e6", "#b3261e"): "feststellung",
    ("#ffcdd2", "#b71c1c"): "feststellung",
    ("#ffe0e0", "#cc0000"): "soll_ohne_regelung",
    ("#c8e6c9", "#1b5e20"): "ohne_befund",
    ("#bbdefb", "#0d47a1"): "offener_nachweis",
}
_CRITERIA = re.compile(r"Bewertungskriteri(?:um|en)\s+(?P<list>\d+\.\d+(?:\s*(?:,|und|sowie)\s*\d+\.\d+)*)")
_CRITERION_SHORT = re.compile(r"\bBK\s+(?P<list>\d+\.\d+)")
_FINDINGS = re.compile(r"Feststellung(?:en)?\s+(?P<list>T\d+\s+F\d+(?:\s*(?:,|und)\s*T\d+\s+F\d+)*)")
_CHECK_FIELD = re.compile(
    r"(?:(?P<doc>[A-ZÄÖÜ][\wÄÖÜäöüß\- ]*?[Cc]heckliste(?:\s+[\w.]+)*?(?:\s+V\s?[\d.]+)?),\s*)?"
    r"Prüffeld(?:er)?\s+(?P<nr>\d+(?:\.\d+)+)"
)
_REGISTER = re.compile(r"\[(?P<list>[A-Z]\d{1,2}(?:\s*,\s*[A-Z]\d{1,2})*)\]")
_LOCATION = re.compile(
    r"(?P<doc>[A-ZÄÖÜ][\wÄÖÜäöüß+\-]*(?:handbuch|richtlinie|leitfaden|Merkblatt|merkblatt)[\wÄÖÜäöüß+\-]*"
    r"(?:\s+(?!Kapitel|Abschnitt|Teil|Nummer|Anlage)[A-ZÄÖÜ\d][\w.+\-]*){0,4})(?:,\s*|\s+)"
    r"(?P<place>(?:Kapitel|Abschnitt|Teil|Nummer|Anlage)\s+[\w.]+(?:\s+(?:Nummer|Satz|Kapitel)\s+[\w.]+)*)"
    r"(?:\s*\((?P<pages>(?:PDF-)?Seiten?\s+[^)]{1,30})\))?"
)
_PREFIX = re.compile(r"^(?P<prefix>[^:\n]{2,60}):\s+\S")


SuggestionValue = LegalBasis | AuditReference | CrossReference | Source | Marker | Actor | str
Found = list[tuple[str, SuggestionValue]]


@dataclass(frozen=True)
class Suggestion:
    """Vorschlag für eine Erweiterung eines Elements samt Fundstelle im Text."""

    element_id: str
    kind: str
    value: SuggestionValue
    evidence: str
    origin: str

    def to_dict(self) -> dict[str, object]:
        """JSON-fähige Darstellung."""
        value = self.value if isinstance(self.value, str) else to_dict(self.value)
        return {
            "element_id": self.element_id,
            "kind": self.kind,
            "value": value,
            "evidence": self.evidence,
            "origin": self.origin,
        }


def _split(values: str) -> list[str]:
    return [part.strip() for part in re.split(r"\s*(?:,|und|sowie)\s*", values) if part.strip()]


def _criteria(match: re.Match[str]) -> Found:
    return [
        ("pruefbezug", AuditReference(key_requirement=bk.split(".")[0], assessment_criterion=bk))
        for bk in _split(match["list"])
    ]


def _findings(match: re.Match[str]) -> Found:
    return [
        ("verweis", CrossReference(kind="feststellung_ref", key=" ".join(r.split()))) for r in _split(match["list"])
    ]


def _check_fields(match: re.Match[str]) -> Found:
    document = " ".join(match["doc"].split()) if match["doc"] else None
    return [("verweis", CrossReference(kind="prueffeld", key=match["nr"], document=document))]


def _registers(match: re.Match[str]) -> Found:
    return [("verweis", CrossReference(kind="register", key=key)) for key in _split(match["list"])]


def _locations(match: re.Match[str]) -> Found:
    place = match["place"] + (f" ({match['pages']})" if match["pages"] else "")
    return [("quelle", Source(source_type="verfahrenshandbuch", location=f"{match['doc']}, {place}"))]


_TEXT_PATTERNS: tuple[tuple[re.Pattern[str], Callable[[re.Match[str]], Found]], ...] = (
    (_CRITERIA, _criteria),
    (_CRITERION_SHORT, _criteria),
    (_FINDINGS, _findings),
    (_CHECK_FIELD, _check_fields),
    (_REGISTER, _registers),
    (_LOCATION, _locations),
)


def suggestions_from_text(element_id: str, text: str, origin: str) -> Iterator[Suggestion]:
    """Vorschläge aus einem Text (Dokumentation oder Beschriftung)."""
    for hit in find_citations(text):
        yield Suggestion(element_id, "rechtsgrundlage", hit.legal_basis, hit.text, origin)
    for pattern, build in _TEXT_PATTERNS:
        for match in pattern.finditer(text):
            for kind, value in build(match):
                yield Suggestion(element_id, kind, value, match.group(0), origin)


def _actor_suggestions(document: BpmnDocument, profile: Profile) -> Iterator[Suggestion]:
    for element in (*document.participants, *document.lanes):
        code = profile.role_from_text(element.name) if element.extensions.actor is None else None
        if code:
            actor = Actor(role=code, display_name=(element.name or "").strip() or None)
            yield Suggestion(element.id, "akteur", actor, element.name or "", "name")
    for element in document.activities:
        match = _PREFIX.match((element.name or "").strip())
        code = profile.role_from_text(match["prefix"]) if match else None
        if match and code:
            yield Suggestion(element.id, "rolle_praefix", code, match["prefix"], "name")


def _color_suggestions(document: BpmnDocument) -> Iterator[Suggestion]:
    for shape in document.root.iter(q(BPMNDI_NS, "BPMNShape")):
        fill = (shape.get(q(BIOC_NS, "fill")) or shape.get(q(COLOR_NS, "background-color")) or "").lower()
        stroke = (shape.get(q(BIOC_NS, "stroke")) or shape.get(q(COLOR_NS, "border-color")) or "").lower()
        kind = COLOR_MARKERS.get((fill, stroke))
        target = shape.get("bpmnElement")
        if kind and target:
            yield Suggestion(target, "kennzeichen", Marker(type=kind), f"{fill}/{stroke}", "farbe")


def suggest(source: str | bytes | BpmnDocument, *, profile: Profile | None = None) -> list[Suggestion]:
    """Alle Vorschläge (das Diagramm bleibt unverändert); Duplikate je Element entfallen."""
    document = as_document(source)
    found: list[Suggestion] = []
    for element in document:
        if element.documentation:
            found += suggestions_from_text(element.id, element.documentation, "documentation")
        if element.name and element.type not in ("participant", "lane"):
            found += suggestions_from_text(element.id, element.name, "name")
    found += _actor_suggestions(document, profile or load_profile())
    found += _color_suggestions(document)
    unique: dict[tuple[str, str, str], Suggestion] = {}
    for item in found:
        unique.setdefault((item.element_id, item.kind, repr(item.value)), item)
    return list(unique.values())


V = TypeVar("V")


def _added(current: tuple[V, ...], value: V, key: Callable[[V], object]) -> tuple[V, ...] | None:
    """``current`` plus ``value`` oder ``None``, wenn ein gleichwertiger Eintrag existiert."""
    return None if key(value) in {key(entry) for entry in current} else (*current, value)


def _merge_legal(ext: Extensions, value: LegalBasis) -> Extensions | None:
    added = _added(ext.legal_bases, value, LegalBasis.citation)
    return replace(ext, legal_bases=added) if added else None


def _merge_reference(ext: Extensions, value: AuditReference) -> Extensions | None:
    added = _added(ext.audit_references, value, lambda v: (v.key_requirement, v.assessment_criterion))
    return replace(ext, audit_references=added) if added else None


def _merge_link(ext: Extensions, value: CrossReference) -> Extensions | None:
    added = _added(ext.cross_references, value, lambda v: (v.kind, v.key))
    return replace(ext, cross_references=added) if added else None


def _merge_source(ext: Extensions, value: Source) -> Extensions | None:
    added = _added(ext.sources, value, lambda v: v.location)
    return replace(ext, sources=added) if added else None


def _merge_marker(ext: Extensions, value: Marker) -> Extensions | None:
    added = _added(ext.markers, value, lambda v: v.type)
    return replace(ext, markers=added) if added else None


def _merge_one(ext: Extensions, value: SuggestionValue) -> tuple[Extensions | None, str]:
    if isinstance(value, Actor):
        return (replace(ext, actor=value) if ext.actor is None else None), "akteur"
    if isinstance(value, LegalBasis):
        return _merge_legal(ext, value), "rechtsgrundlage"
    if isinstance(value, AuditReference):
        return _merge_reference(ext, value), "pruefbezug"
    if isinstance(value, CrossReference):
        return _merge_link(ext, value), "verweis"
    if isinstance(value, Source):
        return _merge_source(ext, value), "quelle"
    if isinstance(value, Marker):
        return _merge_marker(ext, value), "kennzeichen"
    return None, ""


def _merge(extensions: Extensions, items: list[Suggestion]) -> tuple[Extensions, set[str]]:
    changed: set[str] = set()
    for item in items:
        merged, kind = _merge_one(extensions, item.value)
        if merged is not None:
            extensions = merged
            changed.add(kind)
    return extensions, changed


def apply_suggestions(source: str | bytes | BpmnDocument, selection: Iterable[Suggestion]) -> str:
    """Übernimmt ausgewählte Vorschläge; vorhandene Angaben bleiben, Doppeltes entfällt."""
    xml = serialize(source.parsed) if isinstance(source, BpmnDocument) else source
    grouped: dict[str, list[Suggestion]] = {}
    for item in selection:
        grouped.setdefault(item.element_id, []).append(item)
    for element_id, items in grouped.items():
        element = as_document(xml).elements.get(element_id)
        if element is None:
            continue
        extensions, changed = _merge(element.extensions, items)
        if changed:
            xml = set_extensions(xml, element_id, extensions, replace_kinds=sorted(changed))
    return xml if isinstance(xml, str) else xml.decode("utf-8")


def strip_role_prefix(name: str) -> str:
    """„Stelle: Antrag prüfen“ → „Antrag prüfen“."""
    match = _PREFIX.match(name.strip())
    return name.strip()[len(match["prefix"]) + 1 :].strip() if match else name
