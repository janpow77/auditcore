"""Synthetisches Prüfkorpus für die Schwärzung (Prüfplan K01–K09).

Alle Daten sind erfunden. Jede Datei wird im Speicher erzeugt, damit das
Korpus reproduzierbar bleibt und keine Binärdateien im Repository liegen.
Zu jedem Fall gehört die Soll-Liste: was geschwärzt werden muss
(``expected``) und was stehen bleiben muss (``keep``).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pymupdf as fitz

STANDARD_PATTERNS = [
    "iban",
    "email",
    "telefon",
    "steuer_id",
    "ust_id",
    "kreditkarte",
    "geburtsdatum",
    "ip_adresse",
    "aktenzeichen",
]


@dataclass
class Case:
    """Ein Prüffall: eine Zeile Text, die erwarteten Treffer und was bleiben muss."""

    line: str
    expected: list[tuple[str, str]] = field(default_factory=list)  # (Muster, Text)
    keep: list[str] = field(default_factory=list)
    note: str = ""


# ── K02: Varianten je Muster (Trefferquote) ─────────────────────
# Nur Formate, die das Muster laut Hinweistext unterstützen soll.
K02: list[Case] = [
    Case(
        "Konto DE89 3704 0044 0532 0130 00 bei der Bank", [("iban", "DE89 3704 0044 0532 0130 00")]
    ),
    Case("Konto DE89370400440532013000 bei der Bank", [("iban", "DE89370400440532013000")]),
    Case(
        "Konto AT61 1904 3002 3457 3201 in Wien", [("iban", "AT61 1904 3002 3457 3201")], note="V13"
    ),
    Case(
        "Konto FR14 2004 1010 0505 0001 3M02 606 in Paris",
        [("iban", "FR14 2004 1010 0505 0001 3M02 606")],
    ),
    Case(
        "Mail an max.muster@beispiel-firma.example bitte",
        [("email", "max.muster@beispiel-firma.example")],
    ),
    Case("Mail an erika+akte@example.org bitte", [("email", "erika+akte@example.org")]),
    Case("Mail an info@sub.domain.example.com bitte", [("email", "info@sub.domain.example.com")]),
    Case("Telefon +49 611 32-1234 erreichbar", [("telefon", "+49 611 32-1234")]),
    Case("Telefon 069 1234567 erreichbar", [("telefon", "069 1234567")]),
    Case("Telefon 0611/321234 erreichbar", [("telefon", "0611/321234")]),
    Case("Telefon 0171-1234567 erreichbar", [("telefon", "0171-1234567")]),
    Case("Steuer-ID 86095742719 laut Bescheid", [("steuer_id", "86095742719")]),
    Case("USt-IdNr. DE123456789 der Firma", [("ust_id", "DE123456789")]),
    Case("USt-IdNr. DE 123456789 der Firma", [("ust_id", "DE 123456789")]),
    Case("Karte 4111 1111 1111 1111 gültig", [("kreditkarte", "4111 1111 1111 1111")]),
    Case("Karte 4111-1111-1111-1111 gültig", [("kreditkarte", "4111-1111-1111-1111")]),
    Case("Karte 4111111111111111 gültig", [("kreditkarte", "4111111111111111")]),
    Case("geboren am 14.03.1978 in Kassel", [("geburtsdatum", "14.03.1978")]),
    Case("geboren am 1.2.1980 in Kassel", [("geburtsdatum", "1.2.1980")]),
    Case("Zugriff von 192.168.0.1 protokolliert", [("ip_adresse", "192.168.0.1")]),
    Case("Zugriff von 10.0.0.255 protokolliert", [("ip_adresse", "10.0.0.255")]),
    Case("Vorgang AZ-1234/26 in Bearbeitung", [("aktenzeichen", "AZ-1234/26")]),
    Case("Vorgang VB 12/2025 in Bearbeitung", [("aktenzeichen", "VB 12/2025")]),
]

# Formate, die das Muster nicht abdeckt, die in Akten aber vorkommen.
# Werden in den Kennzahlen getrennt ausgewiesen, nicht als Fehler gewertet.
K02_ERWEITERT: list[Case] = [
    Case("Mail an jörg@müller.de bitte", [("email", "jörg@müller.de")], note="Umlaut-Domain"),
    Case(
        "Telefon +49 (0) 69 12345 erreichbar",
        [("telefon", "+49 (0) 69 12345")],
        note="(0)-Schreibweise",
    ),
    Case(
        "Steuer-ID 86 095 742 719 laut Bescheid",
        [("steuer_id", "86 095 742 719")],
        note="gruppiert",
    ),
    Case(
        "Konto de89 3704 0044 0532 0130 00 bei der Bank",
        [("iban", "de89 3704 0044 0532 0130 00")],
        note="klein geschrieben",
    ),
]

# ── K03: Fachtext, der stehen bleiben muss (Genauigkeit) ─────────
# Datumsangaben fehlen bewusst: Das Datumsmuster trifft laut Hinweis alle Daten.
K03: list[Case] = [
    Case("Rechtsgrundlage VO (EU) 2021/1060 Art. 74", keep=["2021/1060"], note="V5"),
    Case("Gemäß VO (EU) Nr. 1303/2013 und 2023/67", keep=["1303/2013", "2023/67"], note="V5"),
    Case("Art. 74 Abs. 1 Buchst. a der Verordnung", keep=["74"]),
    Case("Rechnung Nr. 2024-0815 vom Lieferanten", keep=["2024-0815"], note="V5"),
    Case("Betrag 1.500,00 EUR netto", keep=["1.500,00"]),
    Case("Software Version 1.2.3.4 installiert", keep=["1.2.3.4"], note="V5"),
    Case("Kapitel 3.2.1.4 der Richtlinie", keep=["3.2.1.4"], note="V5"),
    Case("Haushaltsstelle 0701 686 11 belastet", keep=["0701", "686"], note="V5"),
    Case("Belegnummer 12345678901234 erfasst", keep=["12345678901234"], note="V5"),
    Case("Förderkennzeichen EFRE-2021-0042 bewilligt", keep=["EFRE-2021-0042"], note="V5"),
    Case("Postleitzahl 65185 Wiesbaden", keep=["65185"]),
    Case("Seite 1 von 12 der Anlage", keep=["12"]),
    Case("Kundennummer 0815 4711 im System", keep=["0815", "4711"], note="V5"),
]


def pdf_from_lines(lines: list[str], fontsize: float = 11, one_per_page: bool = False) -> bytes:
    doc = fitz.open()
    page = None
    y = 0.0
    for i, line in enumerate(lines):
        if page is None or one_per_page or y > 780:
            page = doc.new_page()
            y = 72.0
        page.insert_text((60, y), line, fontsize=fontsize)
        y += fontsize * 2
        del i
    if page is None:
        doc.new_page()
    out = doc.tobytes()
    doc.close()
    return out


def cases_pdf(cases: list[Case]) -> bytes:
    """Ein Fall je Seite — Fundstellen lassen sich so eindeutig zuordnen."""
    return pdf_from_lines([c.line for c in cases], one_per_page=True)


# ── K04: Layout ─────────────────────────────────────────────────
def two_columns_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((60, 100), "Links: Erika", fontsize=11)
    page.insert_text((320, 100), "Musterfrau rechts", fontsize=11)
    out = doc.tobytes()
    doc.close()
    return out


def wrapped_paragraph_pdf(text: str, width: float = 220) -> bytes:
    """Fließtext mit automatischem Zeilenumbruch."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(60, 60, 60 + width, 800), text, fontsize=11)
    out = doc.tobytes()
    doc.close()
    return out


# ── K06: versteckte Inhalte ──────────────────────────────────────
def hidden_content_pdf(secret: str) -> bytes:
    """Das Geheimnis steckt im Seitentext und in allen Nebenablagen."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), f"Kontakt: {secret}", fontsize=11)
    doc.set_metadata({"author": secret, "title": f"Akte {secret}", "subject": secret})
    doc.set_xml_metadata(
        '<?xpacket begin=""?><x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
        'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description '
        f'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>{secret}</dc:creator>'
        '</rdf:Description></rdf:RDF></x:xmpmeta><?xpacket end="w"?>'
    )
    page.add_text_annot((300, 300), f"Rückfrage an {secret}")
    doc.set_toc([[1, secret, 1]])
    page.insert_link(
        {"kind": fitz.LINK_URI, "from": fitz.Rect(72, 500, 200, 515), "uri": f"mailto:{secret}"}
    )
    widget = fitz.Widget()
    widget.field_name = "kontakt"
    widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
    widget.field_value = secret
    widget.rect = fitz.Rect(72, 400, 300, 420)
    page.add_widget(widget)
    doc.embfile_add("anlage.txt", f"Anlage {secret}".encode())
    out = doc.tobytes()
    doc.close()
    return out


def single_hidden_pdf(secret: str, where: str) -> bytes:
    """Wie hidden_content_pdf, aber nur eine Nebenablage zusätzlich zum Seitentext."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), f"Kontakt: {secret}", fontsize=11)
    if where == "metadata":
        doc.set_metadata({"author": secret, "title": f"Akte {secret}"})
    elif where == "annotation":
        page.add_text_annot((300, 300), f"Rückfrage an {secret}")
    elif where == "toc":
        doc.set_toc([[1, secret, 1]])
    elif where == "link":
        page.insert_link(
            {"kind": fitz.LINK_URI, "from": fitz.Rect(72, 500, 200, 515), "uri": f"mailto:{secret}"}
        )
    elif where == "widget":
        widget = fitz.Widget()
        widget.field_name = "kontakt"
        widget.field_type = fitz.PDF_WIDGET_TYPE_TEXT
        widget.field_value = secret
        widget.rect = fitz.Rect(72, 400, 300, 420)
        page.add_widget(widget)
    elif where == "attachment":
        doc.embfile_add("anlage.txt", f"Anlage {secret}".encode())
    elif where == "white_text":
        page.insert_text((72, 200), secret, fontsize=11, color=(1, 1, 1))
    elif where == "outside_cropbox":
        page.insert_text((72, 830), secret, fontsize=11)
        page.set_cropbox(fitz.Rect(0, 0, 595, 700))
    else:  # pragma: no cover
        raise ValueError(where)
    out = doc.tobytes()
    doc.close()
    return out


def revisions(pdf: bytes) -> list[bytes]:
    """Jede gespeicherte Fassung einer Datei (Schnitt hinter jedem ``%%EOF``)."""
    cuts, start = [], 0
    while (i := pdf.find(b"%%EOF", start)) != -1:
        start = i + 5
        cuts.append(pdf[:start])
    return cuts or [pdf]


def old_revision_pdf(secret: str, visible: str) -> bytes:
    """Ältere Fassung enthält ``secret``, die sichtbare Fassung nur ``visible``."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "akte.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), secret, fontsize=11)
        doc.save(path)
        doc.close()
        doc = fitz.open(path)
        page = doc[0]
        page.add_redact_annot(page.search_for(secret)[0], fill=(1, 1, 1))
        page.apply_redactions()
        page.insert_text((72, 120), visible, fontsize=11)
        doc.save(path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()
        return path.read_bytes()


# ── K07: Bilder und Scans ───────────────────────────────────────
def scanned_pdf(text: str) -> bytes:
    """Seite nur als Bild — ohne Textebene."""
    src = fitz.open()
    page = src.new_page(width=400, height=200)
    page.insert_text((20, 100), text, fontsize=20)
    pix = page.get_pixmap(dpi=100)
    src.close()
    doc = fitz.open()
    out_page = doc.new_page(width=400, height=200)
    out_page.insert_image(out_page.rect, stream=pix.tobytes("png"))
    out = doc.tobytes()
    doc.close()
    return out


def text_over_image_pdf(secret: str) -> bytes:
    """Fundstelle liegt über einem Bild — die Bildpixel darunter müssen weg."""
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 200, 40), False)
    pix.set_rect(pix.irect, (200, 30, 30))  # rote Fläche
    doc = fitz.open()
    page = doc.new_page()
    page.insert_image(fitz.Rect(60, 60, 460, 140), stream=pix.tobytes("png"))
    page.insert_text((80, 105), secret, fontsize=14)
    out = doc.tobytes()
    doc.close()
    return out


# ── K08: Namen für die KI-Erkennung ─────────────────────────────
K08_NAMES = [
    "Erika Musterfrau",
    "Max Mustermann",
    "Hans-Peter Schulze",
    "Dr. Anna Becker",
    "Klaus Koch",
    "Maria von Weizsäcker",
    "Jürgen Wagner",
    "Fatma Yılmaz",
    "Piotr Nowak",
    "Sabine Müller-Lüdenscheidt",
    "Thomas Fischer",
    "Claudia Weber",
]

K08_SENTENCES = [
    "Die Antragstellerin {0} hat den Förderantrag fristgerecht eingereicht.",
    "Nach Rücksprache mit {0} wurde der Termin verschoben.",
    "Herr {0} bestätigte den Eingang der Unterlagen.",
    "{0} ist als Projektleitung benannt.",
    "Die Unterlagen wurden von {0} unterzeichnet und an die Behörde gesandt.",
    "Für Rückfragen steht {0} zur Verfügung.",
]


def ner_text() -> tuple[str, list[str]]:
    parts: list[str] = []
    for i, name in enumerate(K08_NAMES):
        parts.append(K08_SENTENCES[i % len(K08_SENTENCES)].format(name))
    return " ".join(parts), list(K08_NAMES)


# ── K09: große Dokumente ─────────────────────────────────────────
def big_pdf(pages: int, lines_per_page: int = 45, dense: bool = True) -> bytes:
    doc = fitz.open()
    for p in range(pages):
        page = doc.new_page()
        y = 50.0
        for j in range(lines_per_page):
            if dense:
                line = (
                    f"Zeile {j}: Erika Musterfrau, DE89 3704 0044 0532 0130 00, erika@example.org"
                )
            elif j == 0:
                line = f"Seite {p + 1}: Ansprechpartnerin Erika Musterfrau"
            else:
                line = f"Seite {p + 1} Zeile {j}: Sachverhalt ohne personenbezogene Angaben."
            page.insert_text((50, y), line, fontsize=8)
            y += 16
    out = doc.tobytes()
    doc.close()
    return out


# ── Forensik ─────────────────────────────────────────────────────
def leaks(pdf: bytes, secret: str) -> list[str]:
    """Alle Stellen, an denen ``secret`` in der Datei noch lesbar ist."""
    found: list[str] = []
    doc = fitz.open(stream=pdf, filetype="pdf")
    try:
        for page in doc:
            if secret in page.get_text():
                found.append(f"Seitentext S. {page.number + 1}")
            seen = f"Seitentext S. {page.number + 1}" in found
            if not seen and secret in page.get_text(clip=page.mediabox):
                found.append(f"Text außerhalb der CropBox S. {page.number + 1}")
            for widget in page.widgets() or []:
                if secret in str(widget.field_value or ""):
                    found.append("Formularfeld")
            for annot in page.annots() or []:
                if secret in (annot.info.get("content") or ""):
                    found.append("Kommentar")
            for link in page.get_links():
                if secret in str(link.get("uri") or ""):
                    found.append("Link")
        if any(secret in str(v or "") for v in (doc.metadata or {}).values()):
            found.append("Metadaten")
        if secret in (doc.get_xml_metadata() or ""):
            found.append("XMP")
        if any(secret in str(entry[1]) for entry in doc.get_toc()):
            found.append("Lesezeichen")
        for name in doc.embfile_names():
            if secret.encode() in doc.embfile_get(name):
                found.append("Anhang")
    finally:
        doc.close()
    # Rohbytes nach dem Entpacken aller Streams (ohne pikepdf: über fitz)
    raw = _raw_bytes(pdf)
    hex_forms = (secret.encode().hex().encode(), secret.encode().hex().upper().encode())
    if (
        secret.encode("latin-1", "ignore") in raw
        or secret.encode("utf-16-be") in raw
        or any(h in raw for h in hex_forms)
    ):
        found.append("Rohbytes")
    return found


def _raw_bytes(pdf: bytes) -> bytes:
    """Alle Objekte und entpackten Streams der Datei als ein Bytefeld."""
    parts: list[bytes] = []
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        for x in range(1, doc.xref_length()):
            try:
                parts.append(doc.xref_object(x, compressed=True).encode("latin-1", "replace"))
                if doc.xref_is_stream(x):
                    parts.append(doc.xref_stream(x) or b"")
            except Exception:  # noqa: S112 - defekte Objekte zählen nicht als Fund
                continue
    return b"\n".join(parts)
