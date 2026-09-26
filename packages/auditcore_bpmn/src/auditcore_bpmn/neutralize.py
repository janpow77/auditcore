"""Neutralisieren: Export ohne Stellen-, Personen- und Befundbezug.

:func:`neutralize` liefert das neutralisierte XML und einen Bericht, was
ersetzt oder entfernt wurde:

* Anzeigenamen von Lanes (und Pools mit Rolle) → Rollenbezeichnung (Akteur
  oder Rollen-Alias des Profils, sonst „Stelle n“). Ganze Lane-Namen werden
  in Beschriftungen und Aufgabenpräfixen („Name: …“) ersetzt; Anzeigenamen
  der Akteure und Namensteile zusammengesetzter Lane-Namen, die keine Rolle
  bezeichnen (z. B. „Beispielbank“ in „Beispielbank (ZGS)“), überall;
* von der Anwendung genannte Ersetzungen (z. B. Behördennamen) überall;
* E-Mail-Adressen, IBAN, Geldbeträge, Unternehmensnamen (Rechtsformzusatz),
  Anreden mit Namen und Kennnummern (SAP, MaStR, Aktenzeichen, Förderkennzeichen);
* interne Notizen, Prüfschritte, Feststellungen und Feststellungsbezüge
  (auch im Text, z. B. „Feststellung T15 F1“, „(F3)“), befundbezogene
  Kennzeichen und Rotfärbungen, Quellen aus Interviews und Arbeitspapieren
  sowie alle mit ``vertraulich="true"`` markierten Angaben;
* Personenfelder (``autor``, ``freigegebenDurch``, ``pruefer``).

Automatische Erkennung ersetzt keine Durchsicht; der Bericht nennt jede Stelle.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from .model import BpmnDocument
from .namespaces import BIOC_NS, BPMN_NS, BPMNDI_NS, COLOR_NS, FLOWAUDIT_NAMESPACE, local_name, namespace_of, q
from .profiles import Profile, load_profile
from .serialize import serialize
from .vocabulary import label
from .writer import copy_document

FINDING_MARKERS = frozenset(
    {
        "feststellung",
        "feststellung_formell",
        "feststellung_finanziell",
        "offener_nachweis",
        "ohne_befund",
        "soll_ohne_regelung",
    }
)
FINDING_COLORS = frozenset({"#fce8e6", "#b3261e", "#ffcdd2", "#b71c1c", "#ffe0e0", "#cc0000"})
INTERNAL_SOURCES = frozenset({"interview", "arbeitspapier", "durchlauftest"})
REMOVED_ELEMENTS = frozenset({"interneNotiz", "notiz", "pruefschritt", "feststellung"})
PERSON_ATTRIBUTES = ("autor", "freigegebenDurch", "pruefer")
#: FlowAudit-Attribute mit Codes oder Verweisen (werden nicht als Text bereinigt).
_CODE_ATTRIBUTES = frozenset(
    {
        "id",
        "typ",
        "art",
        "ka",
        "bk",
        "rolle",
        "status",
        "kontrollen",
        "kontrolle",
        "schemaVersion",
        "profil",
        "ergebnis",
        "einheit",
        "kategorie",
        "inhaerent",
        "kontrollrisiko",
        "restrisiko",
        "einstufung",
        "durchfuehrung",
        "vertraulich",
        "vertraulichkeit",
        "variante",
        "foerderperiode",
        "celex",
        "eli",
        "url",
        "gueltigAb",
        "gueltigBis",
        "freigegebenAm",
        "vksStichtag",
        "schluesselkontrolle",
    }
)
_DI_COLOR_ATTRIBUTES = (
    q(BIOC_NS, "fill"),
    q(BIOC_NS, "stroke"),
    q(COLOR_NS, "background-color"),
    q(COLOR_NS, "border-color"),
)

PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[E-Mail entfernt]"),
    ("iban", re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,7}(?: ?[A-Z0-9]{1,3})?\b"), "[IBAN entfernt]"),
    (
        "kennnummer",
        re.compile(
            r"\b(?:SAP|MaStR|Az\.|Aktenzeichen|Förderkennzeichen|FKZ|Projektnummer|Vorhabensnummer|Vorhabennummer)"
            r"(?:-Nr\.|-Nummer| Nr\.| Nummer)?[\s.:]*[A-Z0-9][A-Z0-9./-]{3,}"
        ),
        "[Kennnummer entfernt]",
    ),
    ("kennnummer", re.compile(r"\b(?:SEE|SME|ABR|SNB|EEG)\d{9,}\b"), "[Kennnummer entfernt]"),
    (
        "betrag",
        re.compile(
            r"(?:(?:€|EUR)\s?\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?(?:\s?(?:Mio\.|Mrd\.|Tsd\.))?)"
            r"|(?:\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?|\d+(?:,\d{1,2})?)\s?(?:Mio\.\s?|Mrd\.\s?|Tsd\.\s?)?(?:€|EUR|Euro)\b"
        ),
        "[Betrag entfernt]",
    ),
    (
        "unternehmen",
        re.compile(
            r"(?:[A-ZÄÖÜ][\wÄÖÜäöüß&.'-]*\s){0,5}[A-ZÄÖÜ][\wÄÖÜäöüß&.'-]*\s"
            r"(?:GmbH & Co\. KG|gGmbH|GmbH|mbH|AG|KG|OHG|e\.\s?V\.|eG|GbR|SE|UG(?: \(haftungsbeschränkt\))?|Ltd\.?)"
            r"(?=[\s,.;:)\]]|$)"
        ),
        "[Unternehmen]",
    ),
    (
        "person",
        re.compile(r"\b(?:Herr|Frau|Hr\.|Fr\.)\s+(?:Dr\.\s+|Prof\.\s+)?[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?"),
        "[Person]",
    ),
    (
        "feststellungsbezug",
        re.compile(
            r"(?:Feststellung(?:en)?|Themenvermerk(?:e)?)\s+T\d+(?:\s+F\d+)?"
            r"(?:(?:\s*,\s*|\s+und\s+)(?:T\d+\s+)?F?\d+)*"
        ),
        "",
    ),
    ("feststellungsbezug", re.compile(r"\s?\((?:F\d+(?:,\s*)?)+\)"), ""),
)


@dataclass(frozen=True)
class Replacement:
    """Eine Ersetzung oder Entfernung (Original nur auf Wunsch)."""

    element_id: str | None
    location: str
    kind: str
    new: str
    old: str | None = None


@dataclass
class NeutralizationResult:
    """Neutralisiertes XML und Bericht."""

    xml: str
    replacements: list[Replacement] = field(default_factory=list)

    def summary(self) -> dict[str, int]:
        """Anzahl der Ersetzungen je Art."""
        counts: dict[str, int] = {}
        for item in self.replacements:
            counts[item.kind] = counts.get(item.kind, 0) + 1
        return dict(sorted(counts.items()))

    def to_dict(self) -> dict[str, object]:
        """JSON-fähige Darstellung."""
        return {
            "summary": self.summary(),
            "replacements": [{k: v for k, v in vars(r).items() if v is not None} for r in self.replacements],
        }


def _removable(name: str, child: ET.Element) -> bool:
    return (
        name in REMOVED_ELEMENTS
        or (child.get("vertraulich") or "").lower() == "true"
        or (name == "kennzeichen" and child.get("typ") in FINDING_MARKERS)
        or (name == "quelle" and child.get("art") in INTERNAL_SOURCES)
        or (name == "verweis" and child.get("art") == "feststellung_ref")
    )


class _Neutralizer:
    def __init__(
        self, document: BpmnDocument, profile: Profile, replacements: Mapping[str, str], keep_originals: bool
    ) -> None:
        self.document = document
        self.profile = profile
        self.names = {old.strip(): new for old, new in replacements.items() if old.strip()}
        self.labels: dict[str, str] = {}
        self.report: list[Replacement] = []
        self.keep_originals = keep_originals
        self.counter = 0

    def log(self, element_id: str | None, location: str, kind: str, new: str, old: str | None = None) -> None:
        """Hält eine Ersetzung fest."""
        self.report.append(Replacement(element_id, location, kind, new, old if self.keep_originals else None))

    def role_name(self, name: str, role_code: str | None, *, numbered: bool) -> str | None:
        """Rollenbezeichnung einer Stelle oder „Stelle n“ (nur Lanes)."""
        role = self.profile.role(role_code or self.profile.role_from_text(name))
        if role is not None:
            return label(role.labels)
        if not numbered:
            return None
        self.counter += 1
        return f"Stelle {self.counter}"

    def _name_parts(self, name: str, new: str) -> None:
        parts = [p.strip() for p in re.split(r"[()–—,/]|\s-\s", name) if p.strip()]
        if len(parts) < 2:
            return
        for part in parts:
            if len(part) >= 3 and self.profile.role_from_text(part) is None:
                self.names.setdefault(part, new)

    def rename_bodies(self) -> None:
        """Ersetzt Namen von Lanes und Pools mit Rolle."""
        for element in (*self.document.participants, *self.document.lanes):
            old = (element.name or "").strip()
            actor = element.extensions.actor
            new = self.role_name(old, actor.role if actor else None, numbered=element.type == "lane")
            if new is None:
                continue
            if actor and actor.display_name:
                self.names.setdefault(actor.display_name, new)
            if old and old != new:
                self.labels.setdefault(old, new)
                self._name_parts(old, new)
                self.document.xml_element(element.id).set("name", new)
                self.log(element.id, "name", "anzeigename", new, old)

    def _replace_labels(self, value: str, element_id: str | None, location: str) -> str:
        stripped = value.strip()
        for old, new in self.labels.items():
            if stripped == old:
                self.log(element_id, location, "anzeigename", new, old)
                return new
            if stripped.startswith(old + ":"):
                self.log(element_id, location, "anzeigename", new, old)
                return new + stripped[len(old) :]
        return value

    def clean(self, value: str, element_id: str | None, location: str) -> str:
        """Bereinigt einen Text (Namen, Muster)."""
        result = self._replace_labels(value, element_id, location)
        for old in sorted(self.names, key=len, reverse=True):
            if old in result:
                result = result.replace(old, self.names[old])
                self.log(element_id, location, "anzeigename", self.names[old], old)
        for kind, pattern, replacement in PATTERNS:
            for match in pattern.finditer(result):
                self.log(element_id, location, kind, replacement, match.group(0))
            result = pattern.sub(replacement, result)
        if result != value:
            result = re.sub(r"[ \t]{2,}", " ", result).replace(" ,", ",").replace(" .", ".")
        return result

    def strip_extensions(self, node: ET.Element, element_id: str) -> None:
        """Entfernt vertrauliche und befundbezogene FlowAudit-Angaben."""
        container = node.find(q(BPMN_NS, "extensionElements"))
        if container is None:
            return
        for child in list(container):
            if namespace_of(child.tag) != FLOWAUDIT_NAMESPACE:
                continue
            name = local_name(child.tag)
            if _removable(name, child):
                container.remove(child)
                self.log(element_id, f"flowaudit:{name}", "entfernt", "")
            elif name == "akteur":
                self.remove_attributes(child, element_id, ("anzeigename",), "anzeigename")
            elif name == "diagrammInfo":
                self.strip_info(child, element_id)
        if len(container) == 0:
            node.remove(container)

    def remove_attributes(self, node: ET.Element, element_id: str | None, names: tuple[str, ...], kind: str) -> None:
        """Entfernt Attribute und hält es fest."""
        for attribute in names:
            if attribute in node.attrib:
                del node.attrib[attribute]
                self.log(element_id, f"@{attribute}", kind, "")

    def strip_info(self, info: ET.Element, element_id: str) -> None:
        """Bereinigt die Diagramm-Infos."""
        self.remove_attributes(info, element_id, PERSON_ATTRIBUTES, "person")
        for child in list(info):
            name = local_name(child.tag)
            if _removable(name, child):
                info.remove(child)
                self.log(element_id, f"diagrammInfo/flowaudit:{name}", "entfernt", "")

    def clean_node(self, node: ET.Element, owner_id: str | None) -> None:
        """Bereinigt Texte und Textattribute eines Knotens."""
        space = namespace_of(node.tag)
        if space not in (BPMN_NS, FLOWAUDIT_NAMESPACE):
            return
        self.remove_attributes(node, owner_id, ("pruefer",) if local_name(node.tag) == "pruefschritt" else (), "person")
        for attribute, value in list(node.attrib.items()):
            textual = attribute == "name" or (space == FLOWAUDIT_NAMESPACE and attribute not in _CODE_ATTRIBUTES)
            if textual:
                node.set(attribute, self.clean(value, owner_id, f"@{attribute}"))
        if node.text and node.text.strip() and len(node) == 0:
            node.text = self.clean(node.text, owner_id, local_name(node.tag))

    def clean_colors(self, node: ET.Element) -> None:
        """Entfernt befundbezogene Farben einer DI-Form."""
        for attribute in _DI_COLOR_ATTRIBUTES:
            if (node.get(attribute) or "").lower() in FINDING_COLORS:
                del node.attrib[attribute]
                self.log(node.get("bpmnElement"), "DI-Farbe", "befundfarbe", "")

    def clean_texts(self) -> None:
        """Bereinigt alle Texte des Dokuments."""
        owners: dict[ET.Element, str | None] = {}
        for parent in self.document.root.iter():
            owner = parent.get("id") or owners.get(parent)
            for child in parent:
                owners[child] = child.get("id") or owner
        for node in self.document.root.iter():
            if not isinstance(node.tag, str):
                continue
            if node.tag == q(BPMNDI_NS, "BPMNShape"):
                self.clean_colors(node)
            else:
                self.clean_node(node, owners.get(node, node.get("id")))

    def run(self) -> None:
        """Führt alle Schritte aus."""
        self.rename_bodies()
        for element in list(self.document):
            self.strip_extensions(self.document.xml_element(element.id), element.id)
        self.clean_texts()


def neutralize(
    source: str | bytes | BpmnDocument,
    *,
    profile: Profile | None = None,
    replacements: Mapping[str, str] | None = None,
    keep_originals: bool = False,
) -> NeutralizationResult:
    """Neutralisiert ein Diagramm; ``replacements`` ergänzt Namen, die die Anwendung kennt.

    ``keep_originals`` nimmt die ersetzten Originaltexte in den Bericht auf
    (nur für die interne Durchsicht, nicht zur Weitergabe).
    """
    document = copy_document(source)
    worker = _Neutralizer(document, profile or load_profile(), replacements or {}, keep_originals)
    worker.run()
    return NeutralizationResult(serialize(document.parsed), worker.report)
