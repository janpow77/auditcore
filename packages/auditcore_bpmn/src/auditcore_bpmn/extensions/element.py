"""Alle FlowAudit-Angaben an einem BPMN-Element lesen und schreiben."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields
from typing import TypeVar
from xml.etree import ElementTree as ET

from ..namespaces import BPMN_NS, FLOWAUDIT_NAMESPACE, local_name, namespace_of, q
from .legal_basis import LegalBasis
from .mapping import JsonObject, read_element, to_dict, write_element
from .types import (
    Actor,
    AuditFinding,
    AuditReference,
    AuditStep,
    Control,
    CrossReference,
    Deadline,
    DiagramInfo,
    EsiRequirement,
    EsiRequirements,
    Evidence,
    InternalNote,
    Marker,
    Risk,
    Source,
)

#: Mehrfach vorkommende Elemente: XML-Name → (Feld in :class:`Extensions`, Datenklasse).
REPEATED: dict[str, tuple[str, type]] = {
    "rechtsgrundlage": ("legal_bases", LegalBasis),
    "kennzeichen": ("markers", Marker),
    "pruefbezug": ("audit_references", AuditReference),
    "kontrolle": ("controls", Control),
    "risiko": ("risks", Risk),
    "nachweis": ("evidence", Evidence),
    "frist": ("deadlines", Deadline),
    "verweis": ("cross_references", CrossReference),
    "pruefschritt": ("audit_steps", AuditStep),
    "feststellung": ("findings", AuditFinding),
    "quelle": ("sources", Source),
}
#: Einmal vorkommende Elemente: XML-Name → (Feld, Datenklasse).
SINGLE: dict[str, tuple[str, type]] = {
    "diagrammInfo": ("diagram_info", DiagramInfo),
    "akteur": ("actor", Actor),
    "esiAnforderungen": ("esi", EsiRequirements),
}
#: Schreibreihenfolge in ``extensionElements``.
ORDER = (
    "diagrammInfo",
    "akteur",
    "rechtsgrundlage",
    "interneNotiz",
    "kennzeichen",
    "pruefbezug",
    "kontrolle",
    "risiko",
    "nachweis",
    "frist",
    "verweis",
    "pruefschritt",
    "feststellung",
    "quelle",
    "esiAnforderungen",
)


@dataclass(frozen=True)
class Extensions:
    """Alle FlowAudit-Angaben an einem BPMN-Element."""

    legal_bases: tuple[LegalBasis, ...] = ()
    internal_note: str | None = None
    markers: tuple[Marker, ...] = ()
    audit_references: tuple[AuditReference, ...] = ()
    actor: Actor | None = None
    controls: tuple[Control, ...] = ()
    risks: tuple[Risk, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    audit_steps: tuple[AuditStep, ...] = ()
    findings: tuple[AuditFinding, ...] = ()
    sources: tuple[Source, ...] = ()
    deadlines: tuple[Deadline, ...] = ()
    cross_references: tuple[CrossReference, ...] = ()
    esi: EsiRequirements | None = None
    diagram_info: DiagramInfo | None = None

    @property
    def is_empty(self) -> bool:
        """``True`` ohne jede FlowAudit-Angabe."""
        return self == Extensions()

    def marker_types(self) -> tuple[str, ...]:
        """Typen aller Kennzeichen."""
        return tuple(marker.type for marker in self.markers)

    def to_dict(self) -> JsonObject:
        """JSON-fähige Darstellung ohne leere Werte."""
        result: JsonObject = {}
        for item in fields(self):
            value = getattr(self, item.name)
            if value in (None, (), ""):
                continue
            if isinstance(value, tuple):
                result[item.name] = [to_dict(entry) for entry in value]
            else:
                result[item.name] = value if isinstance(value, str) else to_dict(value)
        return result


def extension_elements(element: ET.Element) -> ET.Element | None:
    """``bpmn:extensionElements`` eines Elements oder ``None``."""
    return element.find(q(BPMN_NS, "extensionElements"))


def _flowaudit_children(container: ET.Element) -> Iterable[tuple[str, ET.Element]]:
    for child in container:
        if namespace_of(child.tag) == FLOWAUDIT_NAMESPACE:
            yield local_name(child.tag), child


V = TypeVar("V")


def _of(values: list[object], cls: type[V]) -> tuple[V, ...]:
    return tuple(value for value in values if isinstance(value, cls))


def _first(values: list[object], cls: type[V]) -> V | None:
    return next((value for value in values if isinstance(value, cls)), None)


def read_extensions(element: ET.Element) -> Extensions:
    """Liest alle FlowAudit-Angaben aus ``bpmn:extensionElements`` von ``element``."""
    container = extension_elements(element)
    if container is None:
        return Extensions()
    found: list[object] = []
    notes: list[str] = []
    for name, child in _flowaudit_children(container):
        if name in REPEATED:
            found.append(read_element(REPEATED[name][1], child))
        elif name in SINGLE:
            found.append(read_element(SINGLE[name][1], child))
        elif name in ("interneNotiz", "notiz"):
            notes += [note] if (note := read_element(InternalNote, child).text) else []
    return Extensions(
        legal_bases=_of(found, LegalBasis),
        internal_note=notes[0] if notes else None,
        markers=_of(found, Marker),
        audit_references=_of(found, AuditReference),
        actor=_first(found, Actor),
        controls=_of(found, Control),
        risks=_of(found, Risk),
        evidence=_of(found, Evidence),
        audit_steps=_of(found, AuditStep),
        findings=_of(found, AuditFinding),
        sources=_of(found, Source),
        deadlines=_of(found, Deadline),
        cross_references=_of(found, CrossReference),
        esi=_first(found, EsiRequirements),
        diagram_info=_first(found, DiagramInfo),
    )


def legacy_esi(element: ET.Element) -> EsiRequirements | None:
    """Altattribute ``esiProfile``/``esiCoreRequirements`` (Format ``KA1:K1,K2;KA2``)."""
    profile = element.get("esiProfile")
    raw = element.get("esiCoreRequirements")
    if not (profile or raw):
        return None
    requirements = []
    for entry in (raw or "").split(";"):
        code, _, criteria = entry.strip().partition(":")
        if code.strip():
            requirements.append(
                EsiRequirement(code.strip(), tuple(c.strip() for c in criteria.split(",") if c.strip()))
            )
    return EsiRequirements(profile or "ESI", tuple(requirements), origin="legacy-attribute")


def _new_children(extensions: Extensions) -> dict[str, list[ET.Element]]:
    children: dict[str, list[ET.Element]] = {name: [] for name in ORDER}
    for name, (attribute, _cls) in SINGLE.items():
        value = getattr(extensions, attribute)
        if value is not None:
            children[name].append(write_element(value, name))
    if extensions.internal_note:
        children["interneNotiz"].append(write_element(InternalNote(extensions.internal_note), "interneNotiz"))
    for name, (attribute, _cls) in REPEATED.items():
        children[name] = [write_element(entry, name) for entry in getattr(extensions, attribute)]
    return children


def _container(element: ET.Element) -> ET.Element:
    container = extension_elements(element)
    if container is None:
        container = ET.Element(q(BPMN_NS, "extensionElements"))
        position = sum(1 for child in element if child.tag == q(BPMN_NS, "documentation"))
        element.insert(position, container)
    return container


def write_extensions(element: ET.Element, extensions: Extensions, *, replace: Iterable[str] | None = None) -> None:
    """Schreibt FlowAudit-Angaben in ``bpmn:extensionElements`` von ``element``.

    Ersetzt werden die FlowAudit-Kinder der in ``replace`` genannten lokalen
    Namen (Standard: alle in ``extensions`` gesetzten Arten; ``notiz`` fällt
    mit ``interneNotiz``). Fremde Erweiterungen und nicht genannte
    FlowAudit-Elemente bleiben erhalten. ``extensionElements`` wird bei Bedarf
    nach ``documentation`` angelegt und entfernt, wenn es danach leer ist.
    """
    children = _new_children(extensions)
    targets = set(replace) if replace is not None else {name for name, items in children.items() if items}
    if "interneNotiz" in targets:
        targets.add("notiz")
    if extension_elements(element) is None and not any(children.get(name) for name in targets):
        return
    container = _container(element)
    for name, child in list(_flowaudit_children(container)):
        if name in targets:
            container.remove(child)
    ordered = [child for name in ORDER if name in targets for child in children[name]]
    for offset, child in enumerate(ordered):
        container.insert(offset, child)
    if len(container) == 0:
        element.remove(container)
