"""Gemeinsamer Zustand einer Prüfung und Konfiguration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

from ..model import ACTIVITIES, BpmnDocument, BpmnElement
from ..profiles import Profile, ProfileRegistry
from ..vocabulary import label


@dataclass(frozen=True)
class ValidationConfig:
    """Einstellungen der Prüfung; alle Angaben optional."""

    reference_date: date | None = None
    profile: Profile | None = None
    registry: ProfileRegistry | None = None
    disabled: frozenset[str] = frozenset()
    #: Elementtypen, für die eine Rechtsgrundlage erwartet wird (``BPMN-F001``).
    legal_basis_types: frozenset[str] = ACTIVITIES
    groups: tuple[str, ...] = ("structure", "content", "audit_authority", "segregation")


@dataclass
class ValidationContext:
    """Dokument, Profil, Stichtag und Flussindex einer Prüfung."""

    document: BpmnDocument
    profile: Profile
    profile_origin: str
    reference_date: date
    config: ValidationConfig
    _outgoing: dict[str, list[BpmnElement]] = field(default_factory=dict, repr=False)
    _incoming: dict[str, list[BpmnElement]] = field(default_factory=dict, repr=False)

    @classmethod
    def create(cls, document: BpmnDocument, config: ValidationConfig) -> ValidationContext:
        """Kontext mit Profil aus Konfiguration oder Diagramm-Infos."""
        if config.profile is not None:
            profile, origin = config.profile, "config"
        else:
            profile, origin = (config.registry or ProfileRegistry()).for_diagram(document.diagram_info)
        context = cls(document, profile, origin, config.reference_date or date.today(), config)
        for flow in document.sequence_flows:
            context._outgoing.setdefault(flow.source or "", []).append(flow)
            context._incoming.setdefault(flow.target or "", []).append(flow)
        return context

    def outgoing(self, element_id: str) -> list[BpmnElement]:
        """Ausgehende Sequenzflüsse (indexiert)."""
        return self._outgoing.get(element_id, [])

    def incoming(self, element_id: str) -> list[BpmnElement]:
        """Eingehende Sequenzflüsse (indexiert)."""
        return self._incoming.get(element_id, [])

    @property
    def period(self) -> str | None:
        """Förderperiode aus den Diagramm-Infos, sonst aus dem Profil."""
        info = self.document.diagram_info
        return (info.programming_period if info else None) or self.profile.programming_period

    @property
    def info_owner(self) -> str | None:
        """Element, das die Diagramm-Infos trägt."""
        return self.document.diagram_info_owner

    @property
    def info_title(self) -> str:
        """Titel aus den Diagramm-Infos oder „Diagramm“."""
        info = self.document.diagram_info
        return (info.title if info else None) or "Diagramm"

    def body_of(self, element: BpmnElement) -> tuple[str, str] | None:
        """Stelle (Schlüssel, Anzeige): Akteur mit Rolle und Anzeigename, sonst Lane bzw. Pool."""
        where, actor = self.document.actor_of(element)
        if actor is not None:
            role = self.profile.role(actor.role)
            shown = actor.display_name or (label(role.labels) if role else actor.role)
            return f"{actor.role}|{actor.display_name or ''}", str(shown or "")
        return (where.id, where.label) if where is not None else None

    def successors(self, element: BpmnElement, through_gateways: bool = True) -> Iterable[BpmnElement]:
        """Nachfolgende Aktivitäten (Gateways werden übersprungen)."""
        queue = [f.target for f in self.outgoing(element.id) if f.target]
        seen: set[str] = set()
        while queue:
            current = queue.pop(0)
            if current in seen or current not in self.document.elements:
                continue
            seen.add(current)
            node = self.document.elements[current]
            if through_gateways and node.category == "gateway":
                queue.extend(f.target for f in self.outgoing(node.id) if f.target)
            elif node.is_activity:
                yield node
