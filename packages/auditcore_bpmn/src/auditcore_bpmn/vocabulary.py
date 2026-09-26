"""Kontrollierte Vokabulare des FlowAudit-Schemas 1.1 (Deutsch und Englisch).

Die Listen sind allgemeingültig für alle Fonds mit geteilter Mittelverwaltung
und alle Prüfbehörden. Landes-, behörden- oder programmspezifische Namen
stehen hier nie; Anzeigenamen liefert die Anwendung, Aliasse ein Profil.
Python-Bezeichner sind englisch, Codes und Bezeichnungen fachlich (deutsch/englisch).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

Labels = Mapping[str, str]
LANGUAGES = ("de", "en")


def label(labels: Labels | None, language: str = "de") -> str:
    """Bezeichnung in ``language``; Rückfall Deutsch, dann erster Eintrag."""
    if not labels:
        return ""
    return labels.get(language) or labels.get("de") or next(iter(labels.values()))


def _freeze(data: dict[str, tuple[str, str]]) -> Mapping[str, Labels]:
    return MappingProxyType({code: MappingProxyType({"de": de, "en": en}) for code, (de, en) in data.items()})


DIAGRAM_STATUS = _freeze(
    {
        "entwurf": ("Entwurf", "Draft"),
        "in_pruefung": ("in Prüfung", "under review"),
        "freigegeben": ("freigegeben", "approved"),
        "archiviert": ("archiviert", "archived"),
    }
)

MARKERS = _freeze(
    {
        "rechtsgrundlage": ("Rechtsgrundlage", "Legal basis"),
        "pruefpunkt": ("Prüfpunkt", "Check point"),
        "frist": ("Frist", "Deadline"),
        "vier_augen": ("Vier-Augen-Prinzip", "Four-eyes principle"),
        "dokument": ("Dokument", "Document"),
        "risiko": ("Risiko", "Risk"),
        "system": ("IT-System", "IT system"),
        "zahlung": ("Zahlung", "Payment"),
        "bewilligung": ("Bewilligung", "Approval of support"),
        "schluesselkontrolle": ("Schlüsselkontrolle", "Key control"),
        "checkliste": ("Checkliste", "Checklist"),
        "bescheid": ("Bescheid", "Decision"),
        "stellungnahme": ("Stellungnahme", "Opinion"),
        "gremium": ("Gremium", "Committee"),
        "interessenkonflikt": ("Interessenkonflikt", "Conflict of interest"),
        "veroeffentlichung": ("Veröffentlichung", "Publication"),
        "feststellung": ("Feststellung", "Finding"),
        "feststellung_formell": ("formelle Feststellung", "Formal finding"),
        "feststellung_finanziell": ("finanzielle Feststellung", "Financial finding"),
        "offener_nachweis": ("offener Nachweis", "Open evidence"),
        "ohne_befund": ("ohne Befund", "No finding"),
        "soll_ohne_regelung": ("Soll ohne Regelung (Lücke)", "Target without rule (gap)"),
    }
)

#: Farben, die aus Kennzeichen abgeleitet werden (Füllung, Rand).
MARKER_COLORS: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "feststellung": ("#fce8e6", "#b3261e"),
        "feststellung_formell": ("#fce8e6", "#b3261e"),
        "feststellung_finanziell": ("#fce8e6", "#b3261e"),
        "soll_ohne_regelung": ("#ffe0e0", "#cc0000"),
        "ohne_befund": ("#c8e6c9", "#1b5e20"),
        "offener_nachweis": ("#bbdefb", "#0d47a1"),
    }
)
#: Vorrang bei mehreren farbgebenden Kennzeichen am selben Element.
COLOR_PRIORITY = (
    "feststellung_finanziell",
    "feststellung_formell",
    "feststellung",
    "soll_ohne_regelung",
    "offener_nachweis",
    "ohne_befund",
)

AUDIT_TYPES = _freeze(
    {
        "verwk": ("Verwaltungskontrolle (VerwK)", "Management verification"),
        "systempruefung": ("Systemprüfung", "System audit"),
        "vorhabenpruefung": ("Vorhabenprüfung", "Audit of operations"),
        "rechnungslegungspruefung": ("Prüfung der Rechnungslegung", "Audit of accounts"),
    }
)

FUNDS = _freeze(
    {
        "efre": ("Europäischer Fonds für regionale Entwicklung (EFRE)", "ERDF"),
        "esf_plus": ("Europäischer Sozialfonds Plus (ESF+)", "ESF+"),
        "esf": ("Europäischer Sozialfonds (ESF)", "ESF"),
        "kf": ("Kohäsionsfonds", "Cohesion Fund"),
        "jtf": ("Fonds für einen gerechten Übergang (JTF)", "Just Transition Fund"),
        "emfaf": ("Europäischer Meeres-, Fischerei- und Aquakulturfonds (EMFAF)", "EMFAF"),
        "emff": ("Europäischer Meeres- und Fischereifonds (EMFF)", "EMFF"),
        "eler": ("Europäischer Landwirtschaftsfonds für die Entwicklung des ländlichen Raums (ELER)", "EAFRD"),
        "amif": ("Asyl-, Migrations- und Integrationsfonds (AMIF)", "AMIF"),
        "isf": ("Fonds für die innere Sicherheit (ISF)", "ISF"),
        "bmvi": ("Instrument für Grenzverwaltung und Visumpolitik (BMVI)", "BMVI"),
        "interreg": ("Interreg (Europäische territoriale Zusammenarbeit)", "Interreg"),
    }
)

PROGRAMMING_PERIODS = _freeze(
    {
        "2014-2020": ("Förderperiode 2014–2020", "Programming period 2014-2020"),
        "2021-2027": ("Förderperiode 2021–2027", "Programming period 2021-2027"),
        "2028-2034": ("Förderperiode 2028–2034", "Programming period 2028-2034"),
    }
)


@dataclass(frozen=True)
class Role:
    """Rolle (Stelle) mit optionaler Periodenbindung über Anfangsjahre der Perioden."""

    code: str
    labels: Labels
    from_year: int | None = None
    until_year: int | None = None

    def applies_to(self, period: str | None) -> bool:
        """``True``, wenn die Rolle in der Förderperiode vorgesehen ist (unbekannte Periode: ja)."""
        start = period_start(period)
        if start is None:
            return True
        if self.from_year is not None and start < self.from_year:
            return False
        return not (self.until_year is not None and start > self.until_year)


def period_start(period: str | None) -> int | None:
    """Anfangsjahr aus ``JJJJ-JJJJ``; sonst ``None``."""
    if not period or len(period) != 9 or period[4] != "-":
        return None
    try:
        return int(period[:4])
    except ValueError:
        return None


def _roles(*entries: tuple[str, str, str, int | None, int | None]) -> Mapping[str, Role]:
    return MappingProxyType(
        {code: Role(code, MappingProxyType({"de": de, "en": en}), start, end) for code, de, en, start, end in entries}
    )


ROLES: Mapping[str, Role] = _roles(
    ("vb", "Verwaltungsbehörde", "Managing authority", None, None),
    ("zgs", "Zwischengeschaltete Stelle", "Intermediate body", None, None),
    (
        "rfs",
        "Stelle mit Rechnungsführungsfunktion (Art. 76 CPR)",
        "Body carrying out the accounting function",
        2021,
        None,
    ),
    ("bb", "Bescheinigungsbehörde", "Certifying authority", None, 2014),
    ("pb", "Prüfbehörde", "Audit authority", None, None),
    ("pbs", "Programmbeteiligte Stelle", "Body involved in the programme", None, None),
    ("kom", "Europäische Kommission", "European Commission", None, None),
    ("beg", "Begünstigte", "Beneficiary", None, None),
    ("bga", "Begleitausschuss", "Monitoring committee", None, None),
    ("gs", "Gemeinsames Sekretariat (Interreg)", "Joint secretariat (Interreg)", None, None),
    ("gdp", "Gruppe von Prüfern (Interreg)", "Group of auditors (Interreg)", None, None),
    ("fb", "Fachbehörde/Bewilligungsstelle", "Granting body", None, None),
    ("ftd", "Fachtechnische Dienststelle", "Technical body", None, None),
    ("gut", "Gutachter/Sachverständige", "Expert/assessor", None, None),
    ("gre", "Gremium", "Committee", None, None),
    ("fr", "Fachreferat", "Specialist unit", None, None),
    ("ds", "Datenschutz", "Data protection", None, None),
    ("it", "IT-System", "IT system", None, None),
    ("sonstige", "Sonstige Stelle", "Other body", None, None),
)

CONTROL_TYPES = _freeze({"praeventiv": ("präventiv", "preventive"), "aufdeckend": ("aufdeckend", "detective")})
EXECUTION_MODES = _freeze(
    {
        "manuell": ("manuell", "manual"),
        "it_gestuetzt": ("IT-gestützt", "IT-supported"),
        "automatisiert": ("automatisiert", "automated"),
    }
)
RISK_CATEGORIES = _freeze(
    {
        "allgemein": ("allgemeines Risiko", "general risk"),
        "betrug": ("Betrugsrisiko", "fraud risk"),
        "interessenkonflikt": ("Interessenkonflikt", "conflict of interest"),
        "doppelfinanzierung": ("Doppelfinanzierung", "double funding"),
    }
)
RISK_LEVELS = _freeze({"niedrig": ("niedrig", "low"), "mittel": ("mittel", "medium"), "hoch": ("hoch", "high")})
TEST_RESULTS = _freeze(
    {
        "erfuellt": ("erfüllt", "met"),
        "nicht_erfuellt": ("nicht erfüllt", "not met"),
        "nicht_anwendbar": ("nicht anwendbar", "not applicable"),
        "offen": ("offen", "open"),
    }
)
FINDING_TYPES = _freeze(
    {
        "formell": ("formelle Feststellung", "formal finding"),
        "finanziell": ("finanzielle Feststellung", "financial finding"),
    }
)
FINDING_SEVERITIES = _freeze(
    {
        "gering": ("gering", "minor"),
        "mittel": ("mittel", "moderate"),
        "schwerwiegend": ("schwerwiegend", "serious"),
    }
)
FINDING_STATUS = _freeze(
    {
        "offen": ("offen", "open"),
        "in_umsetzung": ("in Umsetzung", "in progress"),
        "umgesetzt": ("umgesetzt", "implemented"),
        "nicht_umgesetzt": ("nicht umgesetzt", "not implemented"),
        "entfallen": ("entfallen", "withdrawn"),
    }
)
SOURCE_TYPES = _freeze(
    {
        "verfahrenshandbuch": ("Verfahrenshandbuch", "Procedures manual"),
        "interview": ("Interview", "Interview"),
        "durchlauftest": ("Durchlauftest", "Walk-through test"),
        "arbeitspapier": ("Arbeitspapier", "Working paper"),
        "sonstige": ("sonstige Quelle", "other source"),
    }
)
DEADLINE_UNITS = _freeze(
    {
        "tage": ("Tage", "days"),
        "arbeitstage": ("Arbeitstage", "working days"),
        "wochen": ("Wochen", "weeks"),
        "monate": ("Monate", "months"),
        "jahre": ("Jahre", "years"),
    }
)
CONFIDENTIALITY = _freeze(
    {
        "offen": ("offen", "public"),
        "intern": ("intern", "internal"),
        "vs_nfd": ("VS – Nur für den Dienstgebrauch", "restricted"),
    }
)
VARIANTS = _freeze({"soll": ("Soll", "target"), "ist": ("Ist", "actual")})
FUNCTIONING_CATEGORIES = _freeze(
    {
        "1": (
            "Gute Funktionsfähigkeit. Keine oder lediglich geringfügige Verbesserungen erforderlich.",
            "Works well. No or only minor improvement needed.",
        ),
        "2": (
            "Funktionsfähigkeit vorhanden. Bestimmte Verbesserungen erforderlich.",
            "Works. Some improvement needed.",
        ),
        "3": (
            "Funktionsfähigkeit teilweise gegeben. Erhebliche Verbesserungen erforderlich.",
            "Works partially. Substantial improvement needed.",
        ),
        "4": ("Funktionsfähigkeit im Wesentlichen nicht vorhanden.", "Essentially does not work."),
    }
)

#: Arten stabiler fachlicher Schlüssel für Verweise (``flowaudit:verweis/@art``).
CROSS_REFERENCE_KINDS = ("prueffeld", "feststellung_ref", "register")
