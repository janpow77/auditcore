"""Erzeugt die DOCX-Fixtures für Charakterisierung und Tests (einmalig, dann eingecheckt).

Aufruf aus dem Paketverzeichnis mit einer Umgebung, die ``lxml`` enthält::

    python tools/build_fixtures.py

Zwei Arten von Fixtures entstehen:

* ``tests/fixtures/public/*.docx`` – amtliche Rechtstexte (§ 5 Abs. 1 UrhG,
  gemeinfrei) aus den eingecheckten Originalquellen unter ``public/sources``:
  KassenSichV in der Fassung vom 1. Juni 2025 (gesetze-im-internet.de,
  archiviert durch das Internet Archive) und vom 6. Mai 2026 (XML-Download
  gesetze-im-internet.de) sowie der Wortlaut von Artikel 15 aus BGBl. 2025 I
  Nr. 301 (Seite 55, eingecheckt als Einzelseite des amtlichen PDF).
  Je Absatz entsteht genau ein Word-Absatz; Aufzählungen werden im Absatz
  mit einem Leerzeichen zusammengeführt. Der Text wird nicht verändert.
* ``tests/fixtures/synthetic/*.docx`` – frei erfundene Checklisten und Texte
  mit gezielten OOXML-Merkmalen (Inhaltssteuerelemente, Kontrollkästchen,
  verborgener/kursiver Text, nachverfolgte Änderungen). Keine Echtdaten.

Alle DOCX-Dateien werden byte-reproduzierbar geschrieben (feste ZIP-Zeiten).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from lxml import etree, html

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "tests" / "fixtures" / "public"
SYNTHETIC = ROOT / "tests" / "fixtures" / "synthetic"
FIXED_TIME = (2026, 9, 23, 0, 0, 0)

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14_NS = "http://schemas.microsoft.com/office/word/2010/wordml"

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/'
    'vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)
RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)


def write_docx(path: Path, body: str, *, extra: dict[str, bytes] | None = None) -> None:
    """Minimales, gültiges WordprocessingML-Paket mit fester ZIP-Zeit."""
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:w14="{W14_NS}"><w:body>{body}'
        "<w:sectPr/></w:body></w:document>"
    )
    etree.fromstring(document.encode())  # Wohlgeformtheit sicherstellen
    parts = {
        "[Content_Types].xml": CONTENT_TYPES.encode(),
        "_rels/.rels": RELS.encode(),
        "word/document.xml": document.encode(),
        **(extra or {}),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in parts.items():
            info = zipfile.ZipInfo(name, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)


def run(text: str, *, hidden: bool = False, italic: bool = False) -> str:
    props = ("<w:vanish/>" if hidden else "") + ("<w:i/>" if italic else "")
    rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def paragraph(content: str, *, style: str = "", outline: int | None = None) -> str:
    ppr = ""
    if style or outline is not None:
        inner = (f'<w:pStyle w:val="{style}"/>' if style else "") + (
            f'<w:outlineLvl w:val="{outline}"/>' if outline is not None else ""
        )
        ppr = f"<w:pPr>{inner}</w:pPr>"
    return f"<w:p>{ppr}{content}</w:p>"


def cell(content: str) -> str:
    return f"<w:tc><w:p>{content}</w:p></w:tc>"


def checkbox_cell(label: str, checked: bool) -> str:
    """Inhaltssteuerelement mit w14:checkbox wie in Word-Checklisten."""
    state = "1" if checked else "0"
    symbol = "☒" if checked else "☐"
    return (
        '<w:tc><w:p><w:sdt><w:sdtPr><w:tag w:val="checkbox"/>'
        f'<w14:checkbox><w14:checked w14:val="{state}"/></w14:checkbox></w:sdtPr>'
        f"<w:sdtContent>{run(symbol)}</w:sdtContent></w:sdt>{run(' ' + label)}</w:p></w:tc>"
    )


def row(*cells: str, tag: str = "") -> str:
    if tag:
        return (
            f'<w:sdt><w:sdtPr><w:tag w:val="{escape(tag)}"/></w:sdtPr>'
            f"<w:sdtContent><w:tr>{''.join(cells)}</w:tr></w:sdtContent></w:sdt>"
        )
    return f"<w:tr>{''.join(cells)}</w:tr>"


def table(*rows: str) -> str:
    return f"<w:tbl>{''.join(rows)}</w:tbl>"


def simple_checklist(questions: list[str]) -> str:
    """Drei Spalten wie im Originaltest: Kästchen, Frage, Bemerkung."""
    return table(*(row(cell(run("☐")), cell(run(q)), cell("")) for q in questions))


# --------------------------------------------------------------------------- synthetisch


def build_synthetic() -> dict[str, str]:
    files: dict[str, str] = {}

    def put(name: str, body: str) -> None:
        write_docx(SYNTHETIC / name, body)
        files[name] = "synthetisch"

    put(
        "cl_basis_alt.docx",
        simple_checklist(["Frage unverändert", "Frage wird geändert", "Frage entfällt"]),
    )
    put(
        "cl_basis_neu.docx",
        simple_checklist(["Frage unverändert", "Frage wird deutlich geändert", "Neue Frage"]),
    )
    put("cl_100_alt.docx", simple_checklist([f"Prüffrage {i}" for i in range(100)]))
    put(
        "cl_100_neu.docx",
        simple_checklist(
            [f"Prüffrage {i} ergänzt" if i % 10 == 0 else f"Prüffrage {i}" for i in range(100)]
        ),
    )
    put(
        "cl_publizitaet_alt.docx",
        simple_checklist(
            [
                "Wurde die Vergabe dokumentiert?",
                "Liegt der Zuwendungsbescheid vor?",
                "Wurde die Publizitaet geprueft?",
            ]
        ),
    )
    put(
        "cl_publizitaet_neu.docx",
        simple_checklist(
            [
                "Wurde die Vergabe vollstaendig dokumentiert?",
                "Liegt der Zuwendungsbescheid vor?",
                "Wurde die Publizitaet geprueft?",
            ]
        ),
    )

    # Stabile Kennungen, Abschnittszeilen, Antworten, Bemerkungen, Hinweise.
    def rich(version: str) -> str:
        new = version == "neu"
        rows = [
            row(cell(run("Kapitel 1 – Förderfähigkeit"))),
            row(
                cell(run("1.1 Liegt ein wirksamer Zuwendungsbescheid vor?")),
                checkbox_cell("ja", True),
                checkbox_cell("nein", False),
                cell(
                    run(
                        "Bescheid vom 03.02.2025"
                        if not new
                        else "Bescheid vom 03.02.2025, Änderungsbescheid liegt vor"
                    )
                ),
                tag="VP-1.1",
            ),
            row(
                cell(
                    run("1.2 Sind die Ausgaben förderfähig nach Art. 63 VO (EU) 2021/1060?")
                    + run(" Hinweis: Anlage 3 beachten", italic=True)
                ),
                checkbox_cell("ja", not new),
                checkbox_cell("nein", new),
                cell(run("")),
                tag="VP-1.2",
            ),
            row(
                cell(run("1.3 Wurde die Kostenplausibilisierung dokumentiert?")),
                checkbox_cell("ja", True),
                checkbox_cell("nein", False),
                cell(run("") + run("verborgene Arbeitsnotiz", hidden=True)),
                tag="VP-1.3",
            ),
            row(cell(run("Kapitel 2 – Vergabe"))),
            row(
                cell(
                    run(
                        "2.1 Wurde der Auftragswert ordnungsgemäß geschätzt?"
                        if not new
                        else "2.1 Wurde der Auftragswert vor Einleitung des Verfahrens "
                        "ordnungsgemäß geschätzt?"
                    )
                ),
                checkbox_cell("ja", True),
                checkbox_cell("nein", False),
                cell(run("Schätzung in Akte")),
                tag="VP-2.1",
            ),
        ]
        if not new:
            rows.append(
                row(
                    cell(run("2.2 Liegt ein Vergabevermerk vor?")),
                    checkbox_cell("ja", False),
                    checkbox_cell("nein", False),
                    cell(run("")),
                    tag="VP-2.2",
                )
            )
        else:
            rows.append(
                row(
                    cell(run("2.3 Wurde die Eignung der Bieter geprüft?")),
                    checkbox_cell("ja", False),
                    checkbox_cell("nein", True),
                    cell(run("Eignungsnachweise fehlen")),
                    tag="VP-2.3",
                )
            )
        # Reihenfolge im neuen Dokument umgestellt: Kapitel 2 vor Kapitel 1.
        if new:
            rows = rows[4:] + rows[:4]
        return table(*rows)

    put("cl_rich_alt.docx", rich("alt"))
    put("cl_rich_neu.docx", rich("neu"))

    # Nachverfolgte Änderungen: w:ins/w:del werden vor dem Lesen angenommen.
    tracked_old = table(
        *(
            row(cell(run("☐")), cell(run(q)), cell(""))
            for q in ["Wurde die Belegprüfung durchgeführt?", "Sind die Belege vollständig?"]
        )
    )
    tracked_new = table(
        row(
            cell(run("☐")),
            cell(
                run("Wurde die ")
                + '<w:del w:id="1" w:author="Muster" w:date="2026-01-01T00:00:00Z">'
                + "<w:r><w:delText>Belegprüfung</w:delText></w:r></w:del>"
                + '<w:ins w:id="2" w:author="Muster" w:date="2026-01-01T00:00:00Z">'
                + run("stichprobenartige Belegprüfung")
                + "</w:ins>"
                + run(" durchgeführt?")
            ),
            cell(""),
        ),
        row(cell(run("☐")), cell(run("Sind die Belege vollständig?")), cell("")),
    )
    put("cl_tracked_alt.docx", tracked_old)
    put("cl_tracked_neu.docx", tracked_new)

    # Checkliste mit Kontrollkästchen als Zeichen (☒/☐) und kurzer erster Spalte.
    put(
        "cl_symbole_alt.docx",
        table(
            row(cell(run("Nr.")), cell(run("Prüffrage")), cell(run("☐ ja")), cell(run("☐ nein"))),
            row(
                cell(run("1")),
                cell(run("Ist das Vorhaben abgeschlossen?")),
                cell(run("☒ ja")),
                cell(run("☐ nein")),
            ),
            row(
                cell(run("2")),
                cell(run("Ist der Verwendungsnachweis geprüft?")),
                cell(run("☐ ja")),
                cell(run("☒ nein")),
            ),
        ),
    )
    put(
        "cl_symbole_neu.docx",
        table(
            row(cell(run("Nr.")), cell(run("Prüffrage")), cell(run("☐ ja")), cell(run("☐ nein"))),
            row(
                cell(run("1")),
                cell(run("Ist das Vorhaben abgeschlossen?")),
                cell(run("☐ ja")),
                cell(run("☒ nein")),
            ),
            row(
                cell(run("2")),
                cell(run("Ist der Verwendungsnachweis geprüft?")),
                cell(run("☒ ja")),
                cell(run("☐ nein")),
            ),
        ),
    )
    put("cl_leer.docx", table(row(cell(run("☐")), cell(run("ab")), cell(""))))

    # Fließtext: Umstellung, echte Streichung, Überschriften, redaktionelle Änderungen.
    def text(paragraphs: list[str]) -> str:
        return "".join(paragraph(run(p)) for p in paragraphs)

    put(
        "tx_verschoben_alt.docx",
        text(
            [
                "Die Pruefbehoerde prueft das Vorhaben.",
                "Der Beguenstigte legt die Belege vor.",
                "Die Auszahlung erfolgt danach.",
            ]
        ),
    )
    put(
        "tx_verschoben_neu.docx",
        text(
            [
                "Der Beguenstigte legt die Belege vor.",
                "Die Pruefbehoerde prueft das Vorhaben.",
                "Die Auszahlung erfolgt danach.",
            ]
        ),
    )
    put(
        "tx_streichung_alt.docx",
        text(
            ["Die Pruefbehoerde prueft das Vorhaben.", "Eine Auftragsvergabe erfolgte beschraenkt."]
        ),
    )
    put("tx_streichung_neu.docx", text(["Die Pruefbehoerde prueft das Vorhaben."]))

    def structured(new: bool) -> str:
        parts = [
            paragraph(run("Richtlinie zur Förderung von Mustervorhaben"), style="Title"),
            paragraph(run("Abschnitt 1 Allgemeines"), style="Heading1"),
            paragraph(run("1. Zweck der Förderung ist die Unterstützung kleiner Vorhaben.")),
            paragraph(
                run(
                    "2. Gefördert werden Ausgaben, die nach dem 1. Januar 2026 entstehen."
                    if not new
                    else "2. Gefördert werden Ausgaben, die nach dem 1. Juli 2026 entstehen."
                )
            ),
            paragraph(run("Abschnitt 2 Verfahren"), style="berschrift2"),
            paragraph(
                run(
                    "Anträge sind schriftlich zu stellen."
                    if not new
                    else "Anträge sind schriftlich zu stellen!"
                )
            ),
            paragraph(run("Die Bewilligungsbehörde entscheidet nach pflichtgemäßem Ermessen.")),
            paragraph(run("Zuständigkeit"), outline=1),
            paragraph(
                run(
                    "a) Zuständig ist die Bewilligungsbehörde."
                    if not new
                    else "b) Zuständig ist die Bewilligungsbehörde."
                )
            ),
            paragraph(run("§ 3 Inkrafttreten")),
            paragraph(run("Diese Richtlinie tritt am Tag nach ihrer Bekanntmachung in Kraft.")),
        ]
        if new:
            parts.insert(
                7,
                paragraph(
                    run(
                        "Die Bewilligungsbehörde kann Nachweise in elektronischer Form verlangen; "
                        "sie legt das Format fest."
                    )
                ),
            )
        else:
            parts.insert(
                4,
                paragraph(run("3. Eine Kumulierung mit anderen Förderungen ist ausgeschlossen.")),
            )
        return "".join(parts)

    put("tx_struktur_alt.docx", structured(False))
    put("tx_struktur_neu.docx", structured(True))

    # Ersetzungsblock für die monotone Zuordnung (SequenceMatcher "replace").
    put(
        "tx_block_alt.docx",
        text(
            [
                "Einleitung bleibt gleich.",
                "Die Verwaltungsbehörde führt Verwaltungskontrollen nach Art. 74 durch.",
                "Die Prüfbehörde führt Vorhabenprüfungen nach Art. 77 durch.",
                "Die Kommission erhält den Kontrollbericht.",
                "Schluss bleibt gleich.",
            ]
        ),
    )
    put(
        "tx_block_neu.docx",
        text(
            [
                "Einleitung bleibt gleich.",
                "Die Verwaltungsbehörde führt risikobasierte Verwaltungskontrollen "
                "nach Art. 74 durch.",
                "Ein vollständig neuer Absatz über Stichproben.",
                "Die Prüfbehörde führt Vorhabenprüfungen nach Art. 77 Abs. 2 durch.",
                "Schluss bleibt gleich.",
            ]
        ),
    )
    put("tx_leer.docx", paragraph(""))
    # detect_mode: Tabelle mit 6 Zeilen und nur wenigen Absätzen → Checkliste.
    put(
        "mix_tabelle.docx",
        paragraph(run("Kurze Einleitung"))
        + table(
            *(row(cell(run("☐")), cell(run(f"Mischfrage Nummer {i}?")), cell("")) for i in range(6))
        ),
    )

    # Artikelgesetz, frei erfunden: Stammgesetz und Änderungsbefehle aller Arten.
    stamm = [
        (
            "§ 1 Zweck",
            [
                "Dieses Gesetz regelt die Förderung von Mustervorhaben.",
                "Es gilt für Zuwendungen des Landes.",
            ],
        ),
        (
            "§ 2 Begriffsbestimmungen",
            [
                "Zuwendungsempfänger ist, wer eine Zuwendung erhält.",
                "Vorhaben ist jede abgrenzbare Maßnahme.",
                "Ausgaben sind Zahlungen des Zuwendungsempfängers.",
            ],
        ),
        (
            "§ 3 Verfahren",
            [
                "Der Antrag ist bei der Bewilligungsbehörde zu stellen.",
                "Die Frist beträgt drei Monate.",
            ],
        ),
        ("§ 4 Übergangsregelung", ["Für laufende Vorhaben gilt das bisherige Recht."]),
    ]
    put(
        "al_stamm.docx",
        "".join(
            paragraph(run(heading), style="Heading2")
            + "".join(paragraph(run(f"({i}) {text_}")) for i, text_ in enumerate(absaetze, 1))
            for heading, absaetze in stamm
        ),
    )
    befehle = [
        "Artikel 1",
        "Änderung des Mustergesetzes",
        "Das Mustergesetz wird wie folgt geändert:",
        "In § 1 Absatz 2 werden die Wörter „des Landes“ durch die Wörter "
        "„des Landes und des Bundes“ ersetzt.",
        "In § 3 Absatz 2 wird die Angabe „drei Monate“ durch die Angabe „sechs Monate“ ersetzt.",
        "§ 2 Absatz 3 wird wie folgt gefasst:",
        "„(3) Ausgaben sind tatsächlich getätigte Zahlungen des Zuwendungsempfängers.“",
        "Nach § 3 Absatz 1 wird folgender Absatz 2 eingefügt:",
        "„(2) Der Antrag kann elektronisch gestellt werden.“",
        "§ 4 wird aufgehoben.",
        "In § 9 Absatz 1 werden die Wörter „alt“ durch die Wörter „neu“ ersetzt.",
        "In § 2 Absatz 1 werden die Wörter „nicht vorhanden“ durch die Wörter „egal“ ersetzt.",
        "In § 1 Satz 1 wird das Wort „regelt“ durch das Wort „ordnet“ ersetzt.",
        "Nach § 2 wird folgender § 2a eingefügt:",
        "„§ 2a Datenschutz“",
        "§ 3 Absatz 7 wird aufgehoben.",
        "§ 5 wird wie folgt gefasst:",
        "Artikel 2",
        "Inkrafttreten",
        "Dieses Gesetz tritt am Tag nach der Verkündung in Kraft.",
    ]
    put("al_befehle.docx", "".join(paragraph(run(b)) for b in befehle))
    put(
        "al_befehle_letzter_ohne_text.docx",
        paragraph(run("§ 1 Absatz 1 wird wie folgt gefasst:")),
    )
    put("al_stamm_ohne_paragrafen.docx", paragraph(run("Nur Fließtext ohne Paragrafen.")))
    return files


# --------------------------------------------------------------------------- Fehlerfälle

ERRORS = ROOT / "tests" / "fixtures" / "errors"

def blank_pdf() -> bytes:
    """Gültiges PDF (mit Querverweistabelle) mit einer leeren Seite ohne Textebene."""
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Resources<<>>>>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


def build_errors() -> dict[str, str]:
    ERRORS.mkdir(parents=True, exist_ok=True)
    (ERRORS / "kaputt.docx").write_bytes(b"PK\x03\x04 keine gueltige ZIP-Datei")
    (ERRORS / "kaputt.pdf").write_bytes(b"not a real pdf")
    (ERRORS / "notiz.txt").write_text("Nur Text.\n", encoding="utf-8")
    (ERRORS / "leer.pdf").write_bytes(blank_pdf())
    with zipfile.ZipFile(ERRORS / "ohne_document.docx", "w") as archive:
        archive.writestr(zipfile.ZipInfo("word/styles.xml", FIXED_TIME), b"<styles/>")
    with zipfile.ZipFile(ERRORS / "xml_fehler.docx", "w") as archive:
        archive.writestr(zipfile.ZipInfo("word/document.xml", FIXED_TIME), b"<w:document><w:body>")
    # Interne und externe Entität: Das Original löst beide auf (lxml-Standard).
    doctype = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<!DOCTYPE w:document [<!ENTITY intern "Entitätstext">'
        '<!ENTITY extern SYSTEM "file:///etc/hostname">]>'
    )
    for name, entity in (
        ("entitaet_intern.docx", "&intern;"),
        ("entitaet_extern.docx", "&extern;"),
    ):
        document = (
            f'{doctype}<w:document xmlns:w="{W_NS}"><w:body>'
            f"<w:p><w:r><w:t>Absatz mit {entity} am Ende.</w:t></w:r></w:p>"
            "</w:body></w:document>"
        )
        with zipfile.ZipFile(ERRORS / name, "w") as archive:
            archive.writestr(zipfile.ZipInfo("word/document.xml", FIXED_TIME), document.encode())
    return {p.name: "synthetisch" for p in ERRORS.iterdir()}


# --------------------------------------------------------------------------- amtliche Texte


BLOCK_TAGS = {"dt", "dd", "dl", "div", "p", "DT", "DD", "DL", "LA", "P"}


def _flat(element: etree._Element) -> str:
    """Text eines Elements; Listenpunkte und Blöcke durch Leerzeichen getrennt."""
    pieces: list[str] = []

    def walk(node: etree._Element) -> None:
        block = isinstance(node.tag, str) and node.tag in BLOCK_TAGS
        if block:
            pieces.append(" ")
        if node.text:
            pieces.append(node.text)
        for child in node:
            walk(child)
            if child.tail:
                pieces.append(child.tail)
        if block:
            pieces.append(" ")

    walk(element)
    return re.sub(r"\s+", " ", "".join(pieces)).strip()


def _normative(absatz: str) -> bool:
    """juris-Dokumentationshinweise „(+++ … +++)“ sind kein Normtext."""
    return bool(absatz) and not absatz.startswith("(+++")


def gii_html_norms(path: Path) -> list[tuple[str, list[str]]]:
    """Normen aus der HTML-Vollansicht von gesetze-im-internet.de."""
    tree = html.fromstring(path.read_bytes().decode("iso-8859-1"))
    norms: list[tuple[str, list[str]]] = []
    for norm in tree.xpath('//div[@class="jnnorm"]'):
        enbez = norm.xpath('.//span[@class="jnenbez"]')
        if not enbez or not _flat(enbez[0]).startswith("§"):
            continue
        titel = norm.xpath('.//span[@class="jnentitel"]')
        heading = " ".join(filter(None, [_flat(enbez[0]), _flat(titel[0]) if titel else ""]))
        absaetze = [_flat(a) for a in norm.xpath('.//div[@class="jurAbsatz"]')]
        norms.append((heading, [a for a in absaetze if _normative(a)]))
    return norms


def gii_xml_norms(path: Path) -> list[tuple[str, list[str]]]:
    """Normen aus dem XML-Download von gesetze-im-internet.de (gii-norm.dtd)."""
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    tree = etree.parse(str(path), parser)
    norms: list[tuple[str, list[str]]] = []
    for norm in tree.getroot().iter("norm"):
        enbez = norm.findtext("metadaten/enbez") or ""
        if not enbez.startswith("§"):
            continue
        titel = (
            _flat(norm.find("metadaten/titel")) if norm.find("metadaten/titel") is not None else ""
        )
        heading = " ".join(filter(None, [enbez, titel]))
        absaetze = [_flat(p) for p in norm.findall("textdaten/text/Content/P")]
        norms.append((heading, [a for a in absaetze if _normative(a)]))
    return norms


def law_docx(path: Path, norms: list[tuple[str, list[str]]]) -> None:
    body = "".join(
        paragraph(run(heading), style="Heading2") + "".join(paragraph(run(a)) for a in absaetze)
        for heading, absaetze in norms
    )
    write_docx(path, body)


ARTIKEL_15 = [
    "Artikel 15",
    "Änderung der Kassensicherungsverordnung",
    (
        "Die Kassensicherungsverordnung vom 26. September 2017 (BGBl. I S. 3515), "
        "die zuletzt durch Artikel 2 der Verordnung vom 30. Juli 2021 (BGBl. I S. 3295) "
        "geändert worden ist, wird wie folgt geändert:"
    ),
    (
        "In § 11 Absatz 1 Satz 1 wird die Angabe „§ 9 des BSI-Gesetzes“ durch die Angabe "
        "„§ 52 des BSI-Gesetzes“ ersetzt."
    ),
]


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def build_public() -> dict[str, str]:
    sources = PUBLIC / "sources"
    alt = gii_html_norms(sources / "kassensichv_gii_2025-06-01.html")
    neu = gii_xml_norms(sources / "kassensichv_gii_2026-05-06.xml")
    assert [h for h, _ in alt][:2] == [
        "§ 1 Elektronische Aufzeichnungssysteme",
        "§ 2 Protokollierung von digitalen Grundaufzeichnungen",
    ], alt[:2]
    assert [h for h, _ in neu][0] == "§ 1 Elektronische Aufzeichnungssysteme", neu[:1]
    law_docx(PUBLIC / "KassenSichV_2025-06-01.docx", alt)
    law_docx(PUBLIC / "KassenSichV_2026-05-06.docx", neu)
    # Der Wortlaut von Artikel 15 muss in der amtlichen Seite enthalten sein
    # (ohne Leerraum verglichen, da pdftotext Zeilen umbricht).
    page = subprocess.run(
        ["pdftotext", "-layout", str(PUBLIC / "bgbl-2025-I-301-seite55.pdf"), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for line in ARTIKEL_15:
        assert _squash(line) in _squash(page), line
    write_docx(
        PUBLIC / "BGBl-2025-I-301-Art15.docx", "".join(paragraph(run(p)) for p in ARTIKEL_15)
    )
    return {
        "KassenSichV_2025-06-01.docx": "sources/kassensichv_gii_2025-06-01.html",
        "KassenSichV_2026-05-06.docx": "sources/kassensichv_gii_2026-05-06.xml",
        "BGBl-2025-I-301-Art15.docx": "bgbl-2025-I-301-seite55.pdf",
    }


def main() -> None:
    synthetic = build_synthetic()
    public = build_public()
    errors = build_errors()
    manifest = {
        "synthetic": {
            name: hashlib.sha256((SYNTHETIC / name).read_bytes()).hexdigest()
            for name in sorted(synthetic)
        },
        "errors": {
            name: hashlib.sha256((ERRORS / name).read_bytes()).hexdigest()
            for name in sorted(errors)
        },
        "public": {
            name: {
                "sha256": hashlib.sha256((PUBLIC / name).read_bytes()).hexdigest(),
                "derived_from": source,
            }
            for name, source in sorted(public.items())
        },
    }
    (ROOT / "tests" / "fixtures" / "docx-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"synthetic": len(synthetic), "public": len(public)}))


if __name__ == "__main__":
    main()
