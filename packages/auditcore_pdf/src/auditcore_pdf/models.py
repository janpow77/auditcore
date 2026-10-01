"""Datenmodelle für PDF-Verarbeitung, Seitenoperationen und Schwärzung."""

from __future__ import annotations

from dataclasses import dataclass, field


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
    """Regulärer Ausdruck zur Erkennung sensibler Muster."""

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
    """Richtlinie für begleitende Metadaten- und Struktur-Bereinigungen."""

    scrub_metadata: bool = True
    remove_all_metadata: bool = False
    strip_attachments: bool = True
    strip_annotations: bool = False
    clean_xmp: bool = True
    apply_existing_redactions: bool = True


@dataclass(frozen=True)
class RedactionReport:
    """Ergebnisbericht eines Schwärzungslaufs."""

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


@dataclass(frozen=True)
class VerificationResult:
    """Ergebnis der unabhängigen Nachprüfung einer Schwärzung."""

    clean: bool
    violations: list[str] = field(default_factory=list)
    details: dict[str, object] = field(default_factory=dict)


#: Vordefinierte Erkennungsmuster für sensible Daten
STANDARD_PATTERNS: dict[str, RedactionPattern] = {
    "iban": RedactionPattern(
        name="iban",
        regex=r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4})+(?:\s?[A-Z0-9]{1,3})?\b",
        description="Internationale Bankkontonummer (IBAN)",
    ),
    "email": RedactionPattern(
        name="email",
        regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        description="E-Mail-Adressen",
    ),
    "telefon": RedactionPattern(
        name="telefon",
        regex=r"(?:\+49|0)\s?(?:\d{2,5}[\s/-]?){1,3}\d{2,8}",
        description="Telefonnummern im deutschen Format",
    ),
    "steuer_id": RedactionPattern(
        name="steuer_id",
        regex=r"\b\d{11}\b",
        description="11-stellige steuerliche Identifikationsnummer",
    ),
    "ust_id": RedactionPattern(
        name="ust_id",
        regex=r"\bDE\s?\d{9}\b",
        description="Umsatzsteuer-Identifikationsnummer (DE)",
    ),
    "kreditkarte": RedactionPattern(
        name="kreditkarte",
        regex=r"\b(?:\d{4}[\s-]?){3}\d{4}\b",
        description="16-stellige Kreditkartennummern",
    ),
    "geburtsdatum": RedactionPattern(
        name="geburtsdatum",
        regex=r"\b(?:0?[1-9]|[12]\d|3[01])\.(?:0?[1-9]|1[0-2])\.(?:19|20)\d{2}\b",
        description="Datumsangaben im Format TT.MM.JJJJ",
    ),
    "ip_adresse": RedactionPattern(
        name="ip_adresse",
        regex=r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        description="IPv4-Adressen",
    ),
    "aktenzeichen": RedactionPattern(
        name="aktenzeichen",
        regex=r"\b[A-Z]{1,4}[-/ ]?\d{1,6}[-/]\d{2,4}\b",
        description="Aktenzeichen-Muster",
    ),
}
