"""Meldungstexte der Prüfbehörden-, Funktionstrennungs- und Sammlungsregeln."""

from __future__ import annotations

from .severity import ERROR, NOTE, WARNING

TEXTS: tuple[tuple[str, str, str, str, str], ...] = (
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
)
