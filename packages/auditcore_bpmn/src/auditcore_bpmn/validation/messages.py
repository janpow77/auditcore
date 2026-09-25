"""Meldungskatalog der Prüfregeln: stabile IDs, Schweregrad, Gruppe und Texte (de/en).

Die IDs sind Teil der öffentlichen Schnittstelle und ändern sich nicht;
entfallende Regeln werden nicht neu vergeben. Platzhalter in geschweiften
Klammern füllt :meth:`ValidationIssue.message`; ein Parameter ``name_en``
geht für Englisch dem Parameter ``name`` vor.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

#: Schweregrade (Datenwerte): Fehler, Warnung, Hinweis.
ERROR = "fehler"
WARNING = "warnung"
NOTE = "hinweis"
SEVERITIES = (ERROR, WARNING, NOTE)
SEVERITY_LABELS: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        ERROR: MappingProxyType({"de": "Fehler", "en": "Error"}),
        WARNING: MappingProxyType({"de": "Warnung", "en": "Warning"}),
        NOTE: MappingProxyType({"de": "Hinweis", "en": "Note"}),
    }
)


class _Defaults(dict[str, object]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(frozen=True)
class RuleMessage:
    """Meldungsvorlage einer Regel."""

    id: str
    severity: str
    group: str
    de: str
    en: str

    def render(self, language: str, params: Mapping[str, object]) -> str:
        """Text in ``language`` mit eingesetzten Parametern."""
        template = self.en if language == "en" else self.de
        suffix = "_en" if language == "en" else "_de"
        values = _Defaults(params)
        for key, value in params.items():
            if key.endswith(suffix):
                values[key[: -len(suffix)]] = value
        return template.format_map(values)


_MESSAGES = [
    # Struktur
    (
        "BPMN-S001",
        ERROR,
        "structure",
        "Das Wurzelelement ist nicht bpmn:definitions im BPMN-2.0-Namensraum.",
        "The root element is not bpmn:definitions in the BPMN 2.0 namespace.",
    ),
    ("BPMN-S002", ERROR, "structure", "Das Dokument enthält keinen Prozess.", "The document contains no process."),
    (
        "BPMN-S003",
        ERROR,
        "structure",
        "Die Element-ID „{id}“ ist mehrfach vergeben.",
        "Element ID '{id}' is used more than once.",
    ),
    (
        "BPMN-S010",
        ERROR,
        "structure",
        "Prozess „{name}“ hat kein Startereignis.",
        "Process '{name}' has no start event.",
    ),
    ("BPMN-S011", ERROR, "structure", "Prozess „{name}“ hat kein Endereignis.", "Process '{name}' has no end event."),
    (
        "BPMN-S012",
        WARNING,
        "structure",
        "„{name}“ ist mit keinem Sequenz- oder Nachrichtenfluss verbunden (verwaist).",
        "'{name}' is not connected by any sequence or message flow (orphaned).",
    ),
    (
        "BPMN-S013",
        WARNING,
        "structure",
        "„{name}“ hat keinen eingehenden Sequenzfluss.",
        "'{name}' has no incoming sequence flow.",
    ),
    (
        "BPMN-S014",
        WARNING,
        "structure",
        "„{name}“ hat keinen ausgehenden Sequenzfluss.",
        "'{name}' has no outgoing sequence flow.",
    ),
    (
        "BPMN-S015",
        ERROR,
        "structure",
        "Startereignis „{name}“ hat einen eingehenden Sequenzfluss.",
        "Start event '{name}' has an incoming sequence flow.",
    ),
    (
        "BPMN-S016",
        ERROR,
        "structure",
        "Endereignis „{name}“ hat einen ausgehenden Sequenzfluss.",
        "End event '{name}' has an outgoing sequence flow.",
    ),
    (
        "BPMN-S020",
        ERROR,
        "structure",
        "Sequenzfluss „{id}“ ist nicht verbunden (Quelle oder Ziel fehlt).",
        "Sequence flow '{id}' is not connected (source or target missing).",
    ),
    (
        "BPMN-S021",
        ERROR,
        "structure",
        "Sequenzfluss „{id}“ verweist auf das unbekannte Element „{ref}“.",
        "Sequence flow '{id}' refers to unknown element '{ref}'.",
    ),
    (
        "BPMN-S022",
        ERROR,
        "structure",
        "Sequenzfluss „{id}“ überschreitet die Grenze eines Prozesses oder Unterprozesses.",
        "Sequence flow '{id}' crosses a process or sub-process boundary.",
    ),
    (
        "BPMN-S023",
        ERROR,
        "structure",
        "Nachrichtenfluss „{id}“ verbindet Elemente desselben Pools.",
        "Message flow '{id}' connects elements of the same pool.",
    ),
    (
        "BPMN-S024",
        ERROR,
        "structure",
        "Nachrichtenfluss „{id}“ ist nicht verbunden oder verweist auf ein unbekanntes Element.",
        "Message flow '{id}' is not connected or refers to an unknown element.",
    ),
    (
        "BPMN-S030",
        WARNING,
        "structure",
        "Gateway „{name}“ hat bedingte ausgehende Flüsse, aber keinen Default-Fluss.",
        "Gateway '{name}' has conditional outgoing flows but no default flow.",
    ),
    (
        "BPMN-S031",
        ERROR,
        "structure",
        "Der Default-Fluss „{flow}“ von „{name}“ ist kein ausgehender Fluss dieses Elements.",
        "Default flow '{flow}' of '{name}' is not an outgoing flow of this element.",
    ),
    (
        "BPMN-S032",
        NOTE,
        "structure",
        "Gateway „{name}“ verzweigt ohne Bedingungen und ohne Default-Fluss.",
        "Gateway '{name}' splits without conditions and without a default flow.",
    ),
    (
        "BPMN-S033",
        NOTE,
        "structure",
        "Gateway „{name}“ hat genau einen Ein- und einen Ausgang und ist entbehrlich.",
        "Gateway '{name}' has exactly one incoming and one outgoing flow and is redundant.",
    ),
    (
        "BPMN-S034",
        ERROR,
        "structure",
        "Ereignisbasiertes Gateway „{name}“ führt zu „{ziel}“; "
        "zulässig sind nur fangende Zwischenereignisse und Empfangsaufgaben.",
        "Event-based gateway '{name}' leads to '{ziel}'; "
        "only catching intermediate events and receive tasks are allowed.",
    ),
    (
        "BPMN-S035",
        ERROR,
        "structure",
        "Paralleles Gateway „{name}“ hat bedingte ausgehende Flüsse.",
        "Parallel gateway '{name}' has conditional outgoing flows.",
    ),
    (
        "BPMN-S040",
        ERROR,
        "structure",
        "Randereignis „{name}“ hat keinen ausgehenden Sequenzfluss.",
        "Boundary event '{name}' has no outgoing sequence flow.",
    ),
    (
        "BPMN-S041",
        ERROR,
        "structure",
        "Randereignis „{name}“ hat einen eingehenden Sequenzfluss.",
        "Boundary event '{name}' has an incoming sequence flow.",
    ),
    (
        "BPMN-S042",
        ERROR,
        "structure",
        "Randereignis „{name}“ ist an keine bekannte Aktivität angeheftet.",
        "Boundary event '{name}' is not attached to a known activity.",
    ),
    ("BPMN-S050", WARNING, "structure", "Aufgabe „{id}“ hat keinen Namen.", "Task '{id}' has no name."),
    (
        "BPMN-S051",
        NOTE,
        "structure",
        "Verzweigendes Gateway „{id}“ hat keine Beschriftung (Frage).",
        "Splitting gateway '{id}' has no label (question).",
    ),
    (
        "BPMN-S060",
        WARNING,
        "structure",
        "Link-Wurfereignis „{name}“ (Link „{link}“) hat kein passendes Fangereignis im Diagramm.",
        "Link throw event '{name}' (link '{link}') has no matching catch event in the diagram.",
    ),
    (
        "BPMN-S061",
        WARNING,
        "structure",
        "Aufrufaktivität „{name}“ nennt kein aufgerufenes Element.",
        "Call activity '{name}' names no called element.",
    ),
    (
        "BPMN-S070",
        ERROR,
        "structure",
        "Datenassoziation „{id}“ verweist auf das unbekannte Element „{ref}“.",
        "Data association '{id}' refers to unknown element '{ref}'.",
    ),
    (
        "BPMN-S071",
        ERROR,
        "structure",
        "Assoziation „{id}“ verweist auf das unbekannte Element „{ref}“.",
        "Association '{id}' refers to unknown element '{ref}'.",
    ),
    # Fachlich
    ("BPMN-F001", NOTE, "content", "Aufgabe „{name}“ hat keine Rechtsgrundlage.", "Task '{name}' has no legal basis."),
    (
        "BPMN-F002",
        WARNING,
        "content",
        "Das Diagramm hat keine Diagramm-Infos (flowaudit:diagrammInfo).",
        "The diagram has no diagram information (flowaudit:diagrammInfo).",
    ),
    (
        "BPMN-F003",
        WARNING,
        "content",
        "Die Diagramm-Infos nennen keinen Status.",
        "The diagram information states no status.",
    ),
    (
        "BPMN-F004",
        ERROR,
        "content",
        "Der Status „{wert}“ ist unbekannt (zulässig: {zulaessig}).",
        "Status '{wert}' is unknown (allowed: {zulaessig}).",
    ),
    (
        "BPMN-F005",
        WARNING,
        "content",
        "Die Gültigkeit ist am {datum} abgelaufen (Stichtag {stichtag}).",
        "Validity expired on {datum} (reference date {stichtag}).",
    ),
    (
        "BPMN-F006",
        NOTE,
        "content",
        "Die Gültigkeit beginnt erst am {datum} (Stichtag {stichtag}).",
        "Validity only starts on {datum} (reference date {stichtag}).",
    ),
    (
        "BPMN-F007",
        ERROR,
        "content",
        "„gültig ab“ ({ab}) liegt nach „gültig bis“ ({bis}).",
        "'Valid from' ({ab}) is after 'valid until' ({bis}).",
    ),
    (
        "BPMN-F008",
        WARNING,
        "content",
        "Das Diagramm ist freigegeben, aber Freigabe durch oder am fehlt.",
        "The diagram is approved, but approver or approval date is missing.",
    ),
    (
        "BPMN-F009",
        ERROR,
        "content",
        "Das Feld „{feld}“ enthält kein gültiges Datum (JJJJ-MM-TT): „{wert}“.",
        "Field '{feld}' does not contain a valid date (YYYY-MM-DD): '{wert}'.",
    ),
    (
        "BPMN-F010",
        WARNING,
        "content",
        "Die strukturierte Rechtsgrundlage an „{name}“ nennt keine Norm.",
        "The structured legal basis at '{name}' names no legal act.",
    ),
    (
        "BPMN-F011",
        WARNING,
        "content",
        "Das Kennzeichen „{typ}“ an „{name}“ ist unbekannt.",
        "Marker '{typ}' at '{name}' is unknown.",
    ),
    (
        "BPMN-F012",
        WARNING,
        "content",
        "„{name}“ trägt das Kennzeichen Rechtsgrundlage, hat aber keine Rechtsgrundlage.",
        "'{name}' carries the legal-basis marker but has no legal basis.",
    ),
    (
        "BPMN-F013",
        WARNING,
        "content",
        "Die Farbe „{wert}“ in „{feld}“ ist keine #RRGGBB-Angabe.",
        "Colour '{wert}' in '{feld}' is not a #RRGGBB value.",
    ),
    (
        "BPMN-F014",
        WARNING,
        "content",
        "Der Fonds „{wert}“ ist im Profil „{profil}“ nicht vorgesehen.",
        "Fund '{wert}' is not provided for in profile '{profil}'.",
    ),
    (
        "BPMN-F015",
        WARNING,
        "content",
        "Die Förderperiode „{wert}“ passt nicht zum Profil „{profil}“ ({periode}).",
        "Programming period '{wert}' does not match profile '{profil}' ({periode}).",
    ),
    (
        "BPMN-F016",
        WARNING,
        "content",
        "Das Profil „{wert}“ ist unbekannt; geprüft wird mit „{profil}“.",
        "Profile '{wert}' is unknown; checking with '{profil}'.",
    ),
    (
        "BPMN-F017",
        WARNING,
        "content",
        "Der Wert „{wert}“ im Feld „{feld}“ ist unbekannt (zulässig: {zulaessig}).",
        "Value '{wert}' in field '{feld}' is unknown (allowed: {zulaessig}).",
    ),
    (
        "BPMN-F018",
        NOTE,
        "content",
        "Das Ist-Diagramm nennt kein Soll-Diagramm (bezugDiagramm).",
        "The actual-state diagram names no target diagram (bezugDiagramm).",
    ),
    ("BPMN-F020", NOTE, "content", "{art} „{name}“ hat keine Akteur-Rolle.", "{art} '{name}' has no actor role."),
    (
        "BPMN-F021",
        WARNING,
        "content",
        "Die Rolle „{rolle}“ an „{name}“ ist im Profil „{profil}“ unbekannt.",
        "Role '{rolle}' at '{name}' is unknown in profile '{profil}'.",
    ),
    (
        "BPMN-F022",
        NOTE,
        "content",
        "Die Rolle „{rolle}“ ({bezeichnung}) an „{name}“ ist für die Förderperiode {periode} nicht vorgesehen.",
        "Role '{rolle}' ({bezeichnung}) at '{name}' is not provided for in programming period {periode}.",
    ),
    (
        "BPMN-F023",
        ERROR,
        "content",
        "Die Kernanforderung „{ka}“ an „{name}“ ist im Katalog „{profil}“ nicht enthalten (vorhanden: {vorhanden}).",
        "Key requirement '{ka}' at '{name}' is not in catalogue '{profil}' (available: {vorhanden}).",
    ),
    (
        "BPMN-F024",
        ERROR,
        "content",
        "Das Bewertungskriterium „{bk}“ an „{name}“ passt nicht zur Kernanforderung {ka} (erwartet „{ka}.…“).",
        "Assessment criterion '{bk}' at '{name}' does not match key requirement {ka} (expected '{ka}.…').",
    ),
    (
        "BPMN-F025",
        WARNING,
        "content",
        "Das Bewertungskriterium „{bk}“ an „{name}“ ist im Katalog nicht enthalten.",
        "Assessment criterion '{bk}' at '{name}' is not in the catalogue.",
    ),
    (
        "BPMN-F026",
        WARNING,
        "content",
        "Die Prüfart „{wert}“ an „{name}“ ist unbekannt.",
        "Audit type '{wert}' at '{name}' is unknown.",
    ),
    (
        "BPMN-F027",
        WARNING,
        "content",
        "Der Verweis an „{name}“ hat die unbekannte Art „{wert}“ oder keinen Schlüssel.",
        "The reference at '{name}' has unknown type '{wert}' or no key.",
    ),
    # Prüfbehörden-Funktionen
    (
        "BPMN-P001",
        WARNING,
        "audit_authority",
        "Die Kontrolle „{kontrolle}“ an „{name}“ nennt keinen Nachweis.",
        "Control '{kontrolle}' at '{name}' names no evidence.",
    ),
    (
        "BPMN-P002",
        WARNING,
        "audit_authority",
        "„{name}“ hat keinen Aufbewahrungsort (flowaudit:nachweis).",
        "'{name}' has no storage location (flowaudit:nachweis).",
    ),
    (
        "BPMN-P003",
        WARNING,
        "audit_authority",
        "Die Frist „{frist}“ an „{name}“ hat keine Rechtsgrundlage.",
        "Deadline '{frist}' at '{name}' has no legal basis.",
    ),
    (
        "BPMN-P004",
        NOTE,
        "audit_authority",
        "Die Schlüsselkontrolle „{kontrolle}“ an „{name}“ ist noch nicht getestet (kein Prüfschritt).",
        "Key control '{kontrolle}' at '{name}' has not been tested (no test step).",
    ),
    (
        "BPMN-P005",
        WARNING,
        "audit_authority",
        "Das Risiko „{risiko}“ an „{name}“ ist keiner Kontrolle zugeordnet.",
        "Risk '{risiko}' at '{name}' is not linked to any control.",
    ),
    (
        "BPMN-P006",
        ERROR,
        "audit_authority",
        "Das Risiko „{risiko}“ verweist auf die unbekannte Kontrolle „{kontrolle}“.",
        "Risk '{risiko}' refers to unknown control '{kontrolle}'.",
    ),
    (
        "BPMN-P007",
        WARNING,
        "audit_authority",
        "Der Wert „{wert}“ im Feld „{feld}“ an „{name}“ ist unbekannt (zulässig: {zulaessig}).",
        "Value '{wert}' in field '{feld}' at '{name}' is unknown (allowed: {zulaessig}).",
    ),
    (
        "BPMN-P008",
        ERROR,
        "audit_authority",
        "Die ID „{id}“ ist für mehrere Kontrollen, Risiken, Prüfschritte oder Feststellungen vergeben.",
        "ID '{id}' is used for several controls, risks, test steps or findings.",
    ),
    (
        "BPMN-P009",
        WARNING,
        "audit_authority",
        "Die Feststellung an „{name}“ nennt keine Art (formell/finanziell) oder keine Beschreibung.",
        "The finding at '{name}' states no type (formal/financial) or no description.",
    ),
    (
        "BPMN-P010",
        NOTE,
        "audit_authority",
        "Prüfschritt „{schritt}“ an „{name}“: nicht erfüllt.",
        "Test step '{schritt}' at '{name}': not met.",
    ),
    (
        "BPMN-P011",
        WARNING,
        "audit_authority",
        '„{name}“ trägt das Kennzeichen Schlüsselkontrolle, hat aber keine Kontrolle mit schluesselkontrolle="true".',
        "'{name}' carries the key-control marker but has no control with schluesselkontrolle=\"true\".",
    ),
    (
        "BPMN-P012",
        WARNING,
        "audit_authority",
        "Der Prüfschritt „{schritt}“ verweist auf die unbekannte Kontrolle „{kontrolle}“.",
        "Test step '{schritt}' refers to unknown control '{kontrolle}'.",
    ),
    # Funktionstrennung (Regeln aus dem Profil; Meldungen hier)
    (
        "BPMN-FT-STELLEN",
        WARNING,
        "segregation",
        "{titel}: „{a}“ und „{b}“ liegen in derselben Stelle „{stelle}“.",
        "{titel}: '{a}' and '{b}' are in the same body '{stelle}'.",
    ),
    (
        "BPMN-FT-ROLLE",
        ERROR,
        "segregation",
        "{titel}: „{name}“ liegt bei der Rolle „{rolle}“.",
        "{titel}: '{name}' is assigned to role '{rolle}'.",
    ),
    (
        "BPMN-FT-VIERAUGEN",
        WARNING,
        "segregation",
        "{titel}: „{name}“ hat keine zweite Stelle oder Rolle "
        "(Nachfolger in anderer Lane oder Kontrolle einer anderen Rolle).",
        "{titel}: '{name}' has no second body or role (successor in another lane or control by another role).",
    ),
    # Sammlung
    (
        "BPMN-K001",
        ERROR,
        "collection",
        "Aufrufaktivität „{name}“ in „{diagramm}“ verweist auf „{ziel}“; "
        "kein Diagramm der Sammlung enthält diesen Prozess.",
        "Call activity '{name}' in '{diagramm}' refers to '{ziel}'; "
        "no diagram of the collection contains this process.",
    ),
    (
        "BPMN-K002",
        WARNING,
        "collection",
        "Link „{link}“ aus „{diagramm}“ hat in der Sammlung kein Fangereignis.",
        "Link '{link}' from '{diagramm}' has no catch event in the collection.",
    ),
    (
        "BPMN-K003",
        WARNING,
        "collection",
        "Die Prozess-ID „{prozess}“ kommt in mehreren Diagrammen vor ({diagramme}); Verweise sind mehrdeutig.",
        "Process ID '{prozess}' occurs in several diagrams ({diagramme}); references are ambiguous.",
    ),
    (
        "BPMN-K004",
        ERROR,
        "collection",
        "Ordner „{ordner}“ ist unbekannt oder bildet einen Zyklus.",
        "Folder '{ordner}' is unknown or forms a cycle.",
    ),
    (
        "BPMN-K005",
        ERROR,
        "collection",
        "Diagramm „{diagramm}“ verweist auf den unbekannten Tag „{tag}“.",
        "Diagram '{diagramm}' refers to unknown tag '{tag}'.",
    ),
    (
        "BPMN-K006",
        ERROR,
        "collection",
        "Die ID „{id}“ ist in der Sammlung mehrfach vergeben.",
        "ID '{id}' is used more than once in the collection.",
    ),
    (
        "BPMN-K007",
        WARNING,
        "collection",
        "Das Ist-Diagramm „{diagramm}“ verweist auf das unbekannte Soll-Diagramm „{bezug}“.",
        "Actual-state diagram '{diagramm}' refers to unknown target diagram '{bezug}'.",
    ),
    (
        "BPMN-K008",
        ERROR,
        "collection",
        "Der freigegebene Stand {version} von „{diagramm}“ wurde verändert (SHA-256 weicht ab).",
        "Approved version {version} of '{diagramm}' has been modified (SHA-256 differs).",
    ),
]

MESSAGES: Mapping[str, RuleMessage] = MappingProxyType(
    {rid: RuleMessage(rid, severity, group, de, en) for rid, severity, group, de, en in _MESSAGES}
)
