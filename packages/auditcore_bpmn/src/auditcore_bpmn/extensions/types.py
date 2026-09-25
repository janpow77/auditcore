"""Datenklassen der FlowAudit-Elemente (Schema 1.1) mit ihrer XML-Abbildung.

Python-Feldnamen sind englisch; die XML-Namen (zweites Argument von
:func:`xml_field`) sind die verbindlichen deutschen Namen des Schemas
(``docs/bpmn/flowaudit-schema-1.1.md``). Werte werden beim Lesen nicht
verworfen, auch wenn sie ungültig sind; das melden die Prüfregeln.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..namespaces import FLOWAUDIT_SCHEMA_VERSION
from .legal_basis import LegalBasis
from .mapping import xml_field, xml_items


@dataclass(frozen=True)
class InternalNote:
    """``flowaudit:interneNotiz`` (Altform ``flowaudit:notiz`` wird gelesen)."""

    text: str | None = xml_field("", "body")


@dataclass(frozen=True)
class Marker:
    """``flowaudit:kennzeichen``: fachliches Kennzeichen (Overlay-Symbol)."""

    type: str = xml_field("typ", default="")
    text: str | None = xml_field("text")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)


@dataclass(frozen=True)
class AuditReference:
    """``flowaudit:pruefbezug``: Kernanforderung (KA) und Bewertungskriterium (BK)."""

    key_requirement: str | None = xml_field("ka")
    assessment_criterion: str | None = xml_field("bk")
    audit_type: str | None = xml_field("art")
    note: str | None = xml_field("anmerkung")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)

    @property
    def key_requirement_number(self) -> int | None:
        """KA als Zahl oder ``None``."""
        try:
            return int(str(self.key_requirement).strip())
        except (TypeError, ValueError):
            return None

    @property
    def display(self) -> str:
        """Anzeige „KA 2 · BK 2.3“."""
        parts = [f"KA {self.key_requirement}"] if self.key_requirement else []
        if self.assessment_criterion:
            parts.append(f"BK {self.assessment_criterion}")
        return " · ".join(parts)


@dataclass(frozen=True)
class Actor:
    """``flowaudit:akteur`` an Pool oder Lane."""

    role: str | None = xml_field("rolle")
    display_name: str | None = xml_field("anzeigename")


@dataclass(frozen=True)
class EsiRequirement:
    """Eine ESI-Anforderung mit Kriterien."""

    code: str = xml_field("code", default="")
    criteria: tuple[str, ...] = xml_items("kriterium", "texts")


@dataclass(frozen=True)
class EsiRequirements:
    """``flowaudit:esiAnforderungen`` bzw. Altattribute ``esiProfile``/``esiCoreRequirements``."""

    profile: str | None = xml_field("profil")
    requirements: tuple[EsiRequirement, ...] = xml_items("esiAnforderung", "elements", EsiRequirement)
    #: ``"flowaudit-1.1"`` oder ``"legacy-attribute"`` (nicht im XML).
    origin: str = field(default="flowaudit-1.1", metadata={"kind": "internal"})


@dataclass(frozen=True)
class Control:
    """``flowaudit:kontrolle`` an Aktivitäten und Gateways."""

    id: str | None = xml_field("id")
    label: str | None = xml_field("bezeichnung")
    key_control: bool | None = xml_field("schluesselkontrolle", bool_value=True)
    control_type: str | None = xml_field("art")
    execution: str | None = xml_field("durchfuehrung")
    frequency: str | None = xml_field("haeufigkeit")
    evidence: str | None = xml_field("nachweis")
    responsible: str | None = xml_field("verantwortlich")
    description: str | None = xml_field("beschreibung", "text")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)


@dataclass(frozen=True)
class Risk:
    """``flowaudit:risiko``; ``controls`` verweist auf ``flowaudit:kontrolle/@id``."""

    id: str | None = xml_field("id")
    label: str | None = xml_field("bezeichnung")
    category: str | None = xml_field("kategorie")
    inherent: str | None = xml_field("inhaerent")
    control_risk: str | None = xml_field("kontrollrisiko")
    residual: str | None = xml_field("restrisiko")
    controls: tuple[str, ...] = xml_items("kontrollen", "tokens")
    description: str | None = xml_field("beschreibung", "text")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)


@dataclass(frozen=True)
class Evidence:
    """``flowaudit:nachweis`` an Datenobjekten und Datenspeichern (Prüfpfad)."""

    document_type: str | None = xml_field("dokumentart")
    storage_location: str | None = xml_field("aufbewahrungsort")
    it_system: str | None = xml_field("itSystem")
    retention_period: str | None = xml_field("aufbewahrungsfrist")
    note: str | None = xml_field("anmerkung")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)


@dataclass(frozen=True)
class AuditStep:
    """``flowaudit:pruefschritt``: Durchlauf- oder Kontrolltest an einem Element."""

    id: str | None = xml_field("id")
    case: str | None = xml_field("fall")
    document: str | None = xml_field("beleg")
    result: str | None = xml_field("ergebnis")
    date: str | None = xml_field("datum")
    tester: str | None = xml_field("pruefer")
    control: str | None = xml_field("kontrolle")
    sample_size: str | None = xml_field("stichprobe")
    population: str | None = xml_field("grundgesamtheit")
    remark: str | None = xml_field("bemerkung", "text")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)


@dataclass(frozen=True)
class AuditFinding:
    """``flowaudit:feststellung``: Prüffeststellung (formell oder finanziell)."""

    id: str | None = xml_field("id")
    reference: str | None = xml_field("kennung")
    finding_type: str | None = xml_field("art")
    severity: str | None = xml_field("einstufung")
    key_requirement: str | None = xml_field("ka")
    assessment_criterion: str | None = xml_field("bk")
    deadline: str | None = xml_field("frist")
    status: str | None = xml_field("status")
    description: str | None = xml_field("beschreibung", "text")
    recommendation: str | None = xml_field("empfehlung", "text")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)


@dataclass(frozen=True)
class Source:
    """``flowaudit:quelle``: Beleg der Darstellung (Handbuch, Interview, Durchlauftest …)."""

    source_type: str | None = xml_field("art")
    location: str | None = xml_field("fundstelle")
    date: str | None = xml_field("datum")
    reference: str | None = xml_field("referenz")
    text: str | None = xml_field("", "body")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)


@dataclass(frozen=True)
class CrossReference:
    """``flowaudit:verweis``: stabiler fachlicher Schlüssel (Prüffeld, Feststellungsbezug, Register)."""

    kind: str | None = xml_field("art")
    key: str | None = xml_field("schluessel")
    document: str | None = xml_field("dokument")
    confidential: bool | None = xml_field("vertraulich", bool_value=True)


@dataclass(frozen=True)
class Deadline:
    """``flowaudit:frist`` an Zeitgeber-Ereignissen und Aufgaben."""

    value: str | None = xml_field("wert")
    unit: str | None = xml_field("einheit")
    basis: str | None = xml_field("bezug")
    note: str | None = xml_field("anmerkung")
    legal_bases: tuple[LegalBasis, ...] = xml_items("rechtsgrundlage", "elements", LegalBasis)

    @property
    def display(self) -> str:
        """Anzeige „80 tage (Bezug)“."""
        parts = " ".join(part for part in (self.value, self.unit) if part)
        return parts + (f" ({self.basis})" if self.basis else "")


@dataclass(frozen=True)
class DiagramInfo:
    """``flowaudit:diagrammInfo`` am Hauptelement (Kollaboration oder erster Prozess)."""

    schema_version: str | None = xml_field("schemaVersion", default=FLOWAUDIT_SCHEMA_VERSION)
    profile: str | None = xml_field("profil")
    title: str | None = xml_field("titel")
    subtitle: str | None = xml_field("untertitel")
    process_owner: str | None = xml_field("prozessverantwortlich")
    process_type: str | None = xml_field("prozesstyp")
    version: str | None = xml_field("version")
    status: str | None = xml_field("status")
    valid_from: str | None = xml_field("gueltigAb")
    valid_until: str | None = xml_field("gueltigBis")
    author: str | None = xml_field("autor")
    approved_by: str | None = xml_field("freigegebenDurch")
    approved_on: str | None = xml_field("freigegebenAm")
    header_color: str | None = xml_field("kopfzeilenfarbe")
    header_text_color: str | None = xml_field("kopfzeilenTextfarbe")
    programming_period: str | None = xml_field("foerderperiode")
    programme: str | None = xml_field("programm")
    cci: str | None = xml_field("cci")
    confidentiality: str | None = xml_field("vertraulichkeit")
    variant: str | None = xml_field("variante")
    reference_diagram: str | None = xml_field("bezugDiagramm")
    system_cutoff_date: str | None = xml_field("vksStichtag")
    description: str | None = xml_field("beschreibung", "text")
    keywords: tuple[str, ...] = xml_items("schlagwort", "texts")
    funds: tuple[str, ...] = xml_items("fonds", "texts")
    legal_bases: tuple[LegalBasis, ...] = xml_items("rechtsgrundlage", "elements", LegalBasis)
    audit_references: tuple[AuditReference, ...] = xml_items("pruefbezug", "elements", AuditReference)
    risks: tuple[Risk, ...] = xml_items("risiko", "elements", Risk)
    findings: tuple[AuditFinding, ...] = xml_items("feststellung", "elements", AuditFinding)
    sources: tuple[Source, ...] = xml_items("quelle", "elements", Source)
    cross_references: tuple[CrossReference, ...] = xml_items("verweis", "elements", CrossReference)
