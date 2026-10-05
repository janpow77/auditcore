"""Datenmodelle für PDF-Verarbeitung, Seitenoperationen und Schwärzung."""

from __future__ import annotations

from dataclasses import dataclass, field

#: Technische Voreinstellung: Ab diesem Bildanteil an der Seitenfläche gilt eine Seite
#: als nicht prüfbar, weil Bildinhalte ohne OCR weder geschwärzt noch nachgeprüft werden.
#: Keine Fachregel; Anwendungen können den Wert über ``SanitizationPolicy`` bzw.
#: ``verify_redaction(image_coverage_threshold=...)`` setzen.
DEFAULT_IMAGE_COVERAGE_THRESHOLD = 0.25


@dataclass(frozen=True)
class PageInfo:
    """Metadaten und Eigenschaften einer einzelnen PDF-Seite."""

    page_number: int
    width: float
    height: float
    rotation: int = 0
    has_text: bool = True
    image_count: int = 0
    is_scanned: bool = False


@dataclass(frozen=True)
class DocumentInfo:
    """Struktur- und Metadatenübersicht eines PDF-Dokuments."""

    page_count: int
    metadata: dict[str, str] = field(default_factory=dict)
    is_encrypted: bool = False
    pages: list[PageInfo] = field(default_factory=list)
    attachments: list[str] = field(default_factory=list)
    has_signatures: bool = False
    scanned_page_numbers: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class RedactionBox:
    """Expliziter geometrischer Schwärzungsbereich auf einer Seite."""

    page_number: int
    rect: tuple[float, float, float, float]
    fill_color: tuple[float, float, float] = (0.0, 0.0, 0.0)
    label: str = ""


@dataclass(frozen=True)
class RedactionPattern:
    """Regulärer Ausdruck zur Erkennung sensibler Muster.

    Enthält der Ausdruck eine benannte Gruppe ``value``, wird nur diese Gruppe
    geschwärzt und gemeldet (z. B. das Datum hinter dem Kontextwort „geboren“).
    """

    name: str
    regex: str
    description: str = ""


@dataclass(frozen=True)
class RedactionFinding:
    """Gefundene Stelle, die für eine Schwärzung markiert wurde."""

    page_number: int
    rect: tuple[float, float, float, float]
    matched_text: str
    pattern_name: str | None = None
    source: str = "text"


@dataclass(frozen=True)
class SanitizationPolicy:
    """Richtlinie für begleitende Metadaten- und Struktur-Bereinigungen.

    Die ``strip_*``-Schalter entfernen eine Struktur vollständig. Steht ein Schalter
    auf ``False``, werden nur Einträge mit Treffer entfernt oder ersetzt; die
    Nachprüfung meldet alles, was danach noch einen Treffer enthält.
    """

    scrub_metadata: bool = True
    remove_all_metadata: bool = False
    strip_attachments: bool = True
    strip_annotations: bool = False
    clean_xmp: bool = True
    apply_existing_redactions: bool = True
    remove_xmp: bool = True
    strip_javascript: bool = True
    strip_outline: bool = False
    strip_form_fields: bool = False
    strip_links: bool = False
    strip_named_destinations: bool = False
    strip_page_labels: bool = False
    strip_alt_texts: bool = False
    redact_hidden_layers: bool = True
    image_coverage_threshold: float = DEFAULT_IMAGE_COVERAGE_THRESHOLD


@dataclass(frozen=True)
class RedactionReport:
    """Ergebnisbericht eines Schwärzungslaufs.

    ``verified`` ist nur ``True``, wenn die Nachprüfung keine Fundstelle meldet und
    kein Bereich als nicht prüfbar gilt (``unverifiable_pages``, ``unverifiable_items``).
    """

    success: bool
    findings_count: int
    findings: list[RedactionFinding] = field(default_factory=list)
    pages_redacted: list[int] = field(default_factory=list)
    metadata_fields_cleaned: list[str] = field(default_factory=list)
    attachments_removed: list[str] = field(default_factory=list)
    annotations_removed: int = 0
    scanned_pages_without_ocr: list[int] = field(default_factory=list)
    verified: bool = False
    verification_error: str | None = None
    structure_cleaned: list[str] = field(default_factory=list)
    unverifiable_pages: list[int] = field(default_factory=list)
    unverifiable_items: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class VerificationResult:
    """Ergebnis der unabhängigen Nachprüfung einer Schwärzung.

    ``clean`` bedeutet: keine Fundstelle in den geprüften Bereichen. Bereiche, die
    sich ohne OCR oder Dekodierung nicht prüfen lassen, stehen in ``unverifiable``;
    ``fully_verified`` verlangt beides.
    """

    clean: bool
    violations: list[str] = field(default_factory=list)
    details: dict[str, object] = field(default_factory=dict)
    unverifiable: list[str] = field(default_factory=list)
    unverifiable_pages: list[int] = field(default_factory=list)

    @property
    def fully_verified(self) -> bool:
        """Keine Fundstelle und kein nicht prüfbarer Bereich."""
        return self.clean and not self.unverifiable


_DATE = r"(?:0?[1-9]|[12]\d|3[01])\.\s?(?:0?[1-9]|1[0-2])\.\s?(?:19|20)\d{2}"
_OCTET = r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"

#: Vordefinierte Erkennungsmuster für sensible Daten (technische Voreinstellungen,
#: keine Fachregeln). Großbuchstaben-Teile sind mit ``(?-i:…)`` auch bei
#: unscharfer Suche groß zu schreiben; Ziffernfolgen sind gegen angrenzende Ziffern
#: abgegrenzt, damit z. B. PDF-Zeitstempel nicht als Telefonnummer gelten.
STANDARD_PATTERNS: dict[str, RedactionPattern] = {
    "iban": RedactionPattern(
        name="iban",
        regex=r"(?-i:\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,3})?\b)",
        description="IBAN: Ländercode, Prüfziffern, 12 bis 34 Zeichen in Vierergruppen",
    ),
    "email": RedactionPattern(
        name="email",
        regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        description="E-Mail-Adressen",
    ),
    "telefon": RedactionPattern(
        name="telefon",
        regex=(
            r"(?<![\w+])(?:\+49[\s/-]?(?:\(0\)\s?)?|\(?0)[1-9]\d{1,4}\)?"
            r"[\s/-]?\d{3,8}(?:[\s-]\d{1,5})?(?![\w-])"
        ),
        description=(
            "Deutsche Telefonnummern mit 0 oder +49, Vorwahl und mindestens dreistelliger "
            "Rufnummer; nicht innerhalb längerer Ziffern- oder Wortfolgen"
        ),
    ),
    "steuer_id": RedactionPattern(
        name="steuer_id",
        regex=r"(?<!\d)[1-9]\d(?:\s?\d{3}){3}(?!\d)",
        description="Steuerliche Identifikationsnummer: 11 Ziffern, erste Ziffer nicht 0",
    ),
    "ust_id": RedactionPattern(
        name="ust_id",
        regex=r"(?-i:\bDE\s?\d{9}\b)",
        description="Umsatzsteuer-Identifikationsnummer (DE)",
    ),
    "kreditkarte": RedactionPattern(
        name="kreditkarte",
        regex=r"(?<!\d)\d{4}([\s-]?)\d{4}\1\d{4}\1\d{4}(?!\d)",
        description="16-stellige Kartennummern in Vierergruppen mit einheitlichem Trenner",
    ),
    "datum": RedactionPattern(
        name="datum",
        regex=rf"(?<![\d.]){_DATE}(?!\d)",
        description="Jedes Datum im Format TT.MM.JJJJ (breit, nicht in DEFAULT_PATTERNS)",
    ),
    "geburtsdatum": RedactionPattern(
        name="geburtsdatum",
        regex=(
            r"(?i:\bgeb(?:\.-datum\b|\.|oren\b|urtsdatum\b|urtstag\b))"
            rf"(?:\s*(?i:am|:))?\s*(?P<value>{_DATE})(?!\d)"
        ),
        description=(
            "Datum TT.MM.JJJJ nur nach Kontextwort (geb., geboren, Geburtsdatum, "
            "Geburtstag, Geb.-Datum); geschwärzt wird nur das Datum"
        ),
    ),
    "ip_adresse": RedactionPattern(
        name="ip_adresse",
        regex=rf"(?<![\d.])(?:{_OCTET}\.){{3}}{_OCTET}(?!\.?\d)",
        description="IPv4-Adressen mit Oktetten 0 bis 255",
    ),
    "aktenzeichen": RedactionPattern(
        name="aktenzeichen",
        regex=r"(?-i:\b[A-Z]{1,4}[-/ ]?\d{1,6}[-/]\d{2,4}\b)",
        description="Aktenzeichen-Muster (breit, nicht in DEFAULT_PATTERNS)",
    ),
}

#: Konservative Standardauswahl: nur Muster mit eigener Struktur (Ländercode,
#: @-Zeichen, Vorwahl, Kontextwort). Breite Muster wie ``datum``, ``steuer_id``,
#: ``kreditkarte``, ``ip_adresse`` und ``aktenzeichen`` treffen auch fremde
#: Ziffernfolgen und werden nur auf ausdrückliche Anforderung verwendet.
DEFAULT_PATTERNS: tuple[str, ...] = ("iban", "email", "telefon", "ust_id", "geburtsdatum")
