"""KI-Namenserkennung mit Attrappen: Nachsuche, Grenze 10/50, Mustersatz.

spaCy ist in der CI nicht installiert; jede KI-Funktion hier ist eine
Attrappe mit fest vorgegebenen Treffern.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf as fitz
import pytest
import redaction_corpus as kc
from redaction_support import (
    cell_ner,
    count,
    fake_ner,
    findings,
    lines_pdf,
    make_pdf,
    no_frame,
    page_text,
    plan_texts,
    propagated,
)

from auditcore_pdf import redaction as R
from auditcore_pdf.redaction.ner_text import _hard_parts, _short_segments
from auditcore_pdf.redaction.page_text import _page_text

PROP = R.NER_PROPAGATED_ID
FRAME = "Gestern habe ich"


def _framed_or_cell(cell: str, framed: str):
    """Meldet ``cell`` als ganze Zelle und im Mustersatz nur ``framed``."""

    def run(texts):
        out = []
        for t in texts:
            if t.startswith(FRAME):
                out.append([m.span() for m in re.finditer(framed, t)])
            else:
                out.append([(0, len(t))] if t == cell else [])
        return out

    return run


def _prose(line: str, n: int, per_page: int = 40) -> list[list[str]]:
    return [[line] * min(per_page, n - i) for i in range(0, n, per_page)]


# ── Nachsuche eines belegten Namens ─────────────────────────────


def test_ner_name_found_once_is_searched_everywhere():
    # Ein belegter Name wird auf allen Seiten nachgesucht, auch wo die KI ihn
    # allein nicht erkennt; nicht nach einem Artikel, in längeren Wörtern und
    # beim Monatskürzel im Datum.
    def ner(texts):
        return [
            [m.span() for m in re.finditer("Jan Reiter", t)] if "sagte" in t else [] for t in texts
        ]

    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Das sagte Jan Reiter gestern.", fontsize=11)
    page = doc.new_page()
    for y, line in enumerate(("Reiter", "Reitergruppe", "Der Reiter kam.", "am 15. Jan. 2026")):
        page.insert_text((72, 72 + 20 * y), line, fontsize=11)
    pdf = doc.tobytes()
    plan = R.build_plan(pdf, R.Criteria(("ki_namen",), (), False, True), ner)
    found = sorted((c.page, c.source, c.text) for c in plan.candidates)
    assert found == [(1, "ki_namen", "Jan Reiter"), (2, PROP, "Reiter")]
    assert R.source_label(PROP) == "Namen (im Dokument nachgesucht)"


def test_ner_apply_roundtrip_with_fake():
    # Vorschau → alles auswählen → Anwenden mit derselben Attrappe.
    pdf = lines_pdf(["Projektleiter ist Thomas Berger."], ["Berger legte die Belege vor."])
    ner = fake_ner("Thomas Berger")
    crit = R.Criteria(("ki_namen",), (), False, True)
    plan = R.build_plan(pdf, crit, ner)
    sel = R.Selection(plan.sha256, crit, frozenset(c.id for c in plan.candidates), (), True)
    out, report = R.apply_plan(pdf, sel, ner)
    assert "Berger" not in page_text(out)
    assert report.by_source == {"ki_namen": 1, PROP: 1}


def test_ner_without_function_is_rejected():
    # Ohne KI-Funktion bricht das KI-Muster ab, statt still nichts zu finden.
    pdf = lines_pdf(["Projektleiter ist Thomas Berger."])
    with pytest.raises(R.RedactionError, match="nicht verfügbar"):
        findings(pdf, ["ki_namen"])


@pytest.mark.parametrize("width", [480, 260, 160])
def test_ner_k08_names_in_paragraph(width):
    # K08: Namen im umbrochenen Absatz werden über die Attrappe gefunden; die
    # KI bekommt den Absatz, nicht einzelne Zeilen.
    text, names = kc.ner_text()
    pdf = kc.wrapped_paragraph_pdf(text, width=width)
    shown = page_text(pdf).replace("\n", " ")
    # Namen mit Zeichen außerhalb der eingebauten Schrift („ı“) fehlen im Seitentext.
    names = [n for n in names if n.split()[-1] in shown]

    def ner(texts):
        rx = "|".join(r"\s+".join(map(re.escape, n.split())) for n in names)
        return [[m.span() for m in re.finditer(rx, t)] for t in texts]

    hits = " ".join(f.text for f in findings(pdf, ["ki_namen"], ner=ner))
    assert [n for n in names if n.split()[-1] not in hits] == []


def test_ner_cell_false_positive_is_not_multiplied():
    # Meldet die KI eine Zelle „Summe Netto“ als Person und bestätigt sie im
    # Mustersatz nicht, wird „Summe“ nicht im ganzen Dokument geschwärzt.
    pages = [["Summe Netto"]] * 6 + [["Summe und Belege stimmen."] * 3] * 6
    found = plan_texts(lines_pdf(*pages), cell_ner("Summe Netto"))
    assert count(found, "ki_namen", "Summe Netto") == 6
    assert not propagated(found)


def test_ner_cap_boundary():
    # Grenze bei unbestätigtem Zellbeleg: bis max(10, 4 × direkt) wird
    # nachgesucht, darüber nur mit Anrede.
    def pdf(n, addressed=0):
        return lines_pdf(["Jan Reiter"], ["Reiter kam."] * n + ["Herr Reiter kam."] * addressed)

    ner = cell_ner("Jan Reiter")
    assert count(plan_texts(pdf(10), ner), PROP, "Reiter") == 10
    assert count(plan_texts(pdf(11), ner), PROP, "Reiter") == 0
    assert count(plan_texts(pdf(11, 3), ner), PROP, "Reiter") == 3


def test_ner_frequent_name_from_sentence_or_list_has_no_cap():
    prose = [["Berger legte die Belege vor."] * 8 for _ in range(4)]
    cases = [
        (["Projektleiter ist Thomas Berger."], fake_ner("Thomas Berger")),
        (["Berger, Thomas"], cell_ner("Thomas Berger")),
        (["Thomas Berger"], fake_ner("Thomas Berger")),  # Zelle, Mustersatz bestätigt
    ]
    for head, ner in cases:
        found = plan_texts(lines_pdf(head, *prose), ner)
        assert count(found, PROP, "Berger") == 32, head


def test_ner_cross_cell_header_is_capped():
    # Zieht die KI zwei Spaltenköpfe über die Zellgrenze zu einer Person
    # zusammen, gilt die Grenze, auch wenn der Mustersatz das Paar bestätigt.
    def build(doc, page):
        page.insert_text((40, 60), "Telefon", fontsize=8)
        page.insert_text((300, 60), "Begünstigter", fontsize=8)
        for _ in range(2):
            q = doc.new_page()
            for y in range(6):
                q.insert_text((72, 72 + 16 * y), "Begünstigter ist die Stadt.", fontsize=9)

    def ner(texts):
        out = []
        for t in texts:
            m = re.search(r"Telefon\s+Begünstigter", t)
            out.append([m.span()] if m else [])
        return out

    assert not propagated(plan_texts(make_pdf(build), ner))


def test_ner_frame_only_where_cap_matters():
    # Den Mustersatz bekommt die KI nur für Wörter, die sonst an der Grenze scheitern.
    framed = []
    base = cell_ner("Jan Reiter", "Eva Stahl")

    def ner(texts):
        framed.extend(t for t in texts if t.startswith(FRAME))
        return base(texts)

    plan_texts(
        lines_pdf(["Jan Reiter"], ["Eva Stahl"], ["Reiter kam."] * 11 + ["Stahl kam."] * 3), ner
    )
    assert framed == ["Gestern habe ich Jan Reiter getroffen."]


def test_ner_header_row_is_no_sentence_context():
    pdf = lines_pdf(["Ort Telefon Begünstigter Betrag"], *[["Betrag wurde gezahlt."] * 6] * 2)
    found = plan_texts(pdf, no_frame(fake_ner("Begünstigter Betrag")))
    assert count(found, "ki_namen", "Begünstigter Betrag") == 1
    assert not propagated(found)


def test_ner_sentence_context_needs_no_frame():
    prose = [["Berger legte die Belege vor."] * 8 for _ in range(4)]
    for head in ("Projektleiter ist Thomas Berger.", "Thomas Berger ist Projektleiter."):
        found = plan_texts(lines_pdf([head], *prose), no_frame(fake_ner("Thomas Berger")))
        assert count(found, PROP, "Berger") == 32, head


@pytest.mark.parametrize(
    "header",
    [
        "Vorhaben Träger inkl. Anschrift",
        "Vorhaben Träger einschl. Anschrift",
        "Vorhaben Träger in EUR",
        "Vorhaben Träger je Ort",
    ],
)
def test_ner_header_function_words_are_no_sentence(header):
    pdf = lines_pdf([header], *[["Träger wurde benannt."] * 6] * 2)
    assert not propagated(plan_texts(pdf, no_frame(fake_ner("Vorhaben Träger"))))


@pytest.mark.parametrize("mentions, expected", [(30, 30), (50, 50), (51, 0)])
def test_ner_label_before_name_is_confirmed_in_part(mentions, expected):
    # Meldet die KI das Etikett mit und bestätigt der Mustersatz nur den
    # Namen, gilt die höhere Untergrenze 50.
    ner = _framed_or_cell("Auftragnehmer Thomas Berger", "Thomas Berger")
    prose = _prose("Berger legte die Belege vor.", mentions)
    pdf = lines_pdf(["Auftragnehmer Thomas Berger"], *prose, ["Auftragnehmer kam."] * 12)
    found = plan_texts(pdf, ner)
    assert count(found, PROP, "Berger") == expected
    assert count(found, PROP, "Auftragnehmer") == 0


def test_ner_whole_cell_confirmed_in_several_parts():
    ner = _framed_or_cell("Thomas Berger Anna Schmidt", "Thomas Berger|Anna Schmidt")
    pdf = lines_pdf(["Thomas Berger Anna Schmidt"], ["Schmidt legte die Belege vor."] * 30)
    assert count(plan_texts(pdf, ner), PROP, "Schmidt") == 30


def test_ner_frame_span_is_clamped_to_the_cell():
    def ner(texts):
        out = []
        for t in texts:
            if t.startswith(FRAME):
                out.append([(t.index("ich"), t.index(" getroffen") + 4)])
            else:
                out.append([(0, len(t))] if t == "Thomas Berger" else [])
        return out

    pdf = lines_pdf(["Thomas Berger"], ["Berger legte die Belege vor."] * 30)
    assert count(plan_texts(pdf, ner), PROP, "Berger") == 30


@pytest.mark.parametrize(
    "head, line",
    [
        ("Projektleiterin ist Petra Preis.", "Frau Preis legte die Belege vor."),
        ("Projektleiterin ist Petra Preis.", "Preis legte die Belege vor."),
        ("Projektleiter ist Wolfgang Menge.", "Herr Menge legte die Belege vor."),
        ("Projektleiterin ist Anna Schmidt-Mai.", "Frau Schmidt-Mai legte die Belege vor."),
        ("Projektleiterin ist Anna Schmidt-Mai.", "Schmidt-Mai legte die Belege vor."),
    ],
)
def test_ner_surnames_like_table_or_month_words(head, line):
    person = head.split(" ist ")[1].rstrip(".")
    found = plan_texts(lines_pdf([head], [line] * 20), no_frame(fake_ner(person)))
    word = line.split()[1] if line.startswith(("Frau", "Herr")) else line.split()[0]
    assert count(found, PROP, word) == 20


@pytest.mark.parametrize("person", ["Dr. Menge", "Frau Menge", "Prof. Dr. Rabatt"])
def test_ner_table_word_surname_after_title(person):
    word = person.split()[-1]
    pdf = lines_pdf(
        [f"Die Prüfung führte {person} durch."], [f"Rückfrage bei {word} ist erledigt."] * 30
    )
    found = plan_texts(pdf, no_frame(fake_ner(person)))
    assert count(found, PROP, word) == 30


def test_ner_list_form_with_table_word_surname():
    found = plan_texts(lines_pdf(["Preis, Petra"]), fake_ner("Petra Preis"))
    assert count(found, "ki_namen", "Preis, Petra") == 1


def test_ner_confirmed_cell_does_not_free_table_words():
    pdf = lines_pdf(["Menge Thomas Berger"], ["Berger kam."] * 12 + ["Menge kam."] * 12)
    found = plan_texts(pdf, fake_ner("Menge Thomas Berger"))
    assert count(found, PROP, "Berger") == 12
    assert count(found, PROP, "Menge") == 0


def test_ner_table_word_from_cell_kept_with_salutation():
    pdf = lines_pdf(["Wolfgang Menge"], ["Herr Menge kam."] * 3 + ["Menge kam."] * 3)
    assert count(plan_texts(pdf, cell_ner("Wolfgang Menge")), PROP, "Menge") == 3


@pytest.mark.parametrize(
    "head",
    ["Lukas Fischer unterschreibt.", "Antrag von Lukas Fischer", "Rechnung an Lukas Fischer"],
)
def test_ner_short_sentences_are_context(head):
    pdf = lines_pdf([head], ["Fischer legte die Belege vor."] * 30)
    found = plan_texts(pdf, no_frame(fake_ner("Lukas Fischer")))
    assert count(found, PROP, "Fischer") == 30


def test_ner_sentence_context_only_from_neighbouring_lines():
    prose = [["Berger legte die Belege vor."] * 30]
    ner = no_frame(fake_ner("Thomas Berger"))
    wrapped = lines_pdf(["Projektleiter ist", "Thomas Berger."], *prose)
    assert count(plan_texts(wrapped, ner), PROP, "Berger") == 30
    after = lines_pdf(["Thomas Berger", "hat die Belege geprüft."], *prose)
    assert count(plan_texts(after, ner), PROP, "Berger") == 30
    for form in (
        ["Auftragnehmer Thomas Berger", "Kundennummer", "Belegart", "Die Belege liegen vor."],
        ["Auftragnehmer Thomas Berger", "Kundennummer", "die Belege liegen vor."],
        ["die Belege liegen vor.", "Kundennummer", "Auftragnehmer Thomas Berger"],
    ):
        assert count(plan_texts(lines_pdf(form, *prose), ner), PROP, "Berger") == 0, form


def test_ner_sentence_context_across_wide_word_gaps():
    # Zerlegt MuPDF eine Zeile wegen großer Wortabstände, zählt sie trotzdem als eine Zeile.
    def build(doc, page):
        x = 72
        for w in ["Thomas", "Berger", "Referat", "Recht", "prüfte", "die", "Unterlagen"]:
            page.insert_text((x, 72), w, fontsize=9)
            x += fitz.get_text_length(w, fontsize=9) + 14
        doc.new_page().insert_textbox(
            fitz.Rect(50, 50, 545, 800), "Berger legte die Belege vor. " * 30, fontsize=9
        )

    with fitz.open(stream=make_pdf(build), filetype="pdf") as doc:
        pt = _page_text(doc[0])
        assert len({n for n in pt.lines if n >= 0}) > 1  # mehrere Fragmente
    found = plan_texts(make_pdf(build), no_frame(fake_ner("Thomas Berger")))
    assert count(found, PROP, "Berger") == 30


@pytest.mark.parametrize(
    "head", ["Summe Netto nach Skonto", "Rabatt Skonto bei Zahlung", "Netto, Brutto"]
)
def test_ner_header_of_table_words_is_no_name(head):
    words = head.replace(",", "").split()
    pdf = lines_pdf([head], *[[f"{w} wurde geprüft." for w in words] * 10] * 3)
    ner = fake_ner(" ".join(words[:2]), " ".join(reversed(words[:2])))
    assert not propagated(plan_texts(pdf, ner))


def test_ner_table_word_as_label_is_partial_confirmation():
    # „Summe Thomas Berger“: Bestätigt der Mustersatz nur „Thomas Berger“,
    # gilt die Untergrenze 50 wie bei jedem Etikett.
    ner = _framed_or_cell("Summe Thomas Berger", "Thomas Berger")
    for n, expected in ((40, 40), (60, 0)):
        found = plan_texts(lines_pdf(["Summe Thomas Berger"], *_prose("Berger kam.", n)), ner)
        assert count(found, PROP, "Berger") == expected, n


def test_ner_table_header_words_are_never_propagated():
    pdf = lines_pdf(["Pos Menge"], ["Menge und Preis stimmen."] * 30)
    found = plan_texts(pdf, fake_ner("Pos Menge"))
    assert count(found, "ki_namen", "Pos Menge") == 1
    assert not propagated(found)


def test_ner_partial_frame_hit_is_no_confirmation():
    ner = _framed_or_cell("Thomas Berger", "Thomas")
    found = plan_texts(
        lines_pdf(["Thomas Berger"], ["Berger kam."] * 11, ["Thomas kam."] * 11), ner
    )
    assert count(found, PROP, "Berger") == 0
    assert count(found, PROP, "Thomas") == 0


@pytest.mark.parametrize(
    "title",
    [
        "Herr",
        "Frau",
        "Hr.",
        "Fr.",
        "Dr.",
        "Prof.",
        "Dr. med.",
        "Dr.-Ing.",
        "Dipl.-Ing.",
        "Prof. Dr.-Ing. Dr. h. c.",
        "Dr. rer. nat. habil.",
        "Dipl.-Ing. (FH)",
        "Dipl.-Ök.",
    ],
)
def test_ner_salutation_kept_above_cap(title):
    pdf = lines_pdf(["Jan Reiter"], ["Reiter kam."] * 11 + [f"Laut {title} Reiter fehlt nichts."])
    assert count(plan_texts(pdf, cell_ner("Jan Reiter")), PROP, "Reiter") == 1


def test_ner_cap_grows_with_distinct_direct_hits():
    # Drei verschiedene direkte Belege heben die Grenze auf 4 × 3 = 12.
    heads = [["Jan Reiter"], ["Eva Reiter"], ["Max Reiter"]]
    ner = cell_ner("Jan Reiter", "Eva Reiter", "Max Reiter")
    assert count(plan_texts(lines_pdf(*heads, ["Reiter kam."] * 12), ner), PROP, "Reiter") == 12
    assert count(plan_texts(lines_pdf(*heads, ["Reiter kam."] * 13), ner), PROP, "Reiter") == 0


# ── Namen über zwei Spalten ─────────────────────────────────────


def _columns_pdf(mentions: int) -> bytes:
    def build(doc, page):
        page.insert_text((40, 60), "Klaus", fontsize=8)
        page.insert_text((300, 60), "Wagner", fontsize=8)
        q = doc.new_page()
        q.insert_textbox(
            fitz.Rect(50, 50, 545, 800), "Wagner legte die Belege vor. " * mentions, fontsize=9
        )

    return make_pdf(build)


def _columns_ner(confirm: bool):
    def run(texts):
        out = []
        for t in texts:
            m = re.search(r"Klaus\s+Wagner", t)
            framed = t.startswith(FRAME)
            out.append([m.span()] if m and (confirm or not framed) else [])
        return out

    return run


@pytest.mark.parametrize(
    "mentions, confirm, expected",
    [(30, True, 30), (50, True, 50), (51, True, 0), (30, False, 0), (10, False, 10)],
)
def test_ner_column_split_name_confirmed_has_higher_floor(mentions, confirm, expected):
    found = plan_texts(_columns_pdf(mentions), _columns_ner(confirm))
    assert count(found, PROP, "Wagner") == expected


def test_ner_column_split_confirmation_per_word():
    def build(doc, page):
        page.insert_text((40, 60), "Klaus", fontsize=8)
        page.insert_text((300, 60), "Wagner", fontsize=8)
        for text in ["Klaus legte die Belege vor. " * 20] + [
            "Wagner legte die Belege vor. " * 50
        ] * 4:
            doc.new_page().insert_textbox(fitz.Rect(50, 50, 545, 800), text, fontsize=9)

    found = plan_texts(make_pdf(build), _columns_ner(True))
    assert count(found, PROP, "Klaus") == 20
    assert count(found, PROP, "Wagner") == 0


def test_ner_contact_words_are_no_name_parts():
    pdf = lines_pdf(["Telefon, Telefax"], ["Telefon und Telefax sind besetzt."] * 4)
    found = plan_texts(pdf, fake_ner("Telefon Telefax", "Telefax Telefon"))
    assert not propagated(found)
    assert count(found, "ki_namen", "Telefon, Telefax") == 0
    # Zusammengesetzt: Der Mustersatz bekommt nur den Namen.
    framed = []
    base = cell_ner(
        "Telefon-Nr Thomas Berger", "Telefon/Fax Thomas Berger", "Telefon: Thomas Berger"
    )

    def ner(texts):
        framed.extend(t for t in texts if t.startswith(FRAME))
        return base(texts)

    found = plan_texts(
        lines_pdf(
            ["Telefon-Nr Thomas Berger"],
            ["Telefon/Fax Thomas Berger"],
            ["Telefon: Thomas Berger"],
            ["Berger kam."] * 13,
            ["Telefon-Nr fehlt."] * 3,
        ),
        ner,
    )
    assert framed == ["Gestern habe ich Thomas Berger getroffen."]
    assert count(found, PROP, "Telefon-Nr") == 0


def test_ner_double_names_are_propagated():
    pdf = lines_pdf(
        ["Anna Meyer-Lüdenscheidt", "Hans-Peter Schulze"], ["Meyer-Lüdenscheidt", "Hans-Peter"]
    )
    ner = fake_ner("Anna Meyer-Lüdenscheidt", "Hans-Peter Schulze")
    found = [t for t in plan_texts(pdf, ner) if t[0] == 2]
    assert sorted(t for _p, _s, t in found) == ["Hans-Peter", "Meyer-Lüdenscheidt"]
    assert {s for _p, s, _t in found} == {PROP}


def test_ner_keeps_initials_and_foreign_letters():
    pdf = lines_pdf(["i. A. Stahl", "Ömer Çelik", "Atreides"], ["Stahl", "Çelik"])
    found = plan_texts(pdf, fake_ner("A. Stahl", "Ömer Çelik", "Atreides"))
    assert [t for _p, _s, t in found] == ["A. Stahl", "Atreides", "Ömer Çelik", "Stahl", "Çelik"]


def test_ner_propagation_exceptions():
    pdf = lines_pdf(
        ["Jan Heide"],
        [
            "Der Heide blühte.",
            "am 15. Jan. 2026",
            "Jan. 2027",
            "Protokoll: Jan.",
            "Herr von der Heide",
        ],
    )
    found = [t for t in plan_texts(pdf, fake_ner("Jan Heide")) if t[0] == 2]
    assert [t for _p, _s, t in found] == ["Heide", "Jan"], found


# ── Fehlerhafte KI-Funktionen ───────────────────────────────────


def _raise(texts):
    raise RuntimeError("Modell nicht geladen")


def _raise_value(texts):
    raise ValueError("Text zu lang")


def _raise_lazy(texts):
    yield []
    raise RuntimeError("Modell nicht geladen")


def _raise_inner(texts):
    def spans():
        yield (0, 1)
        raise RuntimeError("Modell nicht geladen")

    return [spans() for _ in texts]


@pytest.mark.parametrize(
    "bad, error",
    [
        (lambda texts: [[(0, -1)] for _ in texts], None),  # leerer Span: verworfen
        (lambda texts: [[] for _ in texts[1:]], "ungültiges Ergebnis"),
        (lambda texts: [None for _ in texts], "ungültiges Ergebnis"),
        (lambda texts: [[("a", "b")] for _ in texts], "ungültiges Ergebnis"),
        (lambda texts: None, "ungültiges Ergebnis"),
        (_raise, "fehlgeschlagen"),
        (_raise_value, "fehlgeschlagen"),
        (_raise_lazy, "fehlgeschlagen"),
        (_raise_inner, "fehlgeschlagen"),
        (lambda texts: 5, "ungültiges Ergebnis"),
    ],
)
def test_ner_malformed_result(bad, error):
    # Eine fehlerhafte KI-Funktion belegt nicht die ganze Seite. Falsche Form
    # oder ein Absturz bricht ab; still leere Treffer gibt es nicht.
    pdf = lines_pdf(["Antrag der Stadt Ulm", "Kosten und Belege"], ["Kosten", "Belege"])
    if error is None:
        assert plan_texts(pdf, bad) == []
    else:
        with pytest.raises(R.RedactionNerError, match=error):
            plan_texts(pdf, bad)


def test_ner_failure_on_apply_is_ner_error():
    # Auch beim Anwenden, das die Suche wiederholt, ergibt ein KI-Fehler RedactionNerError.
    pdf = lines_pdf(["Antrag der Stadt Ulm"])
    crit = R.Criteria(("ki_namen",), (), False, True)
    plan = R.build_plan(pdf, crit, fake_ner("Stadt Ulm"))
    sel = R.Selection(plan.sha256, crit, frozenset(c.id for c in plan.candidates), (), True)
    with pytest.raises(R.RedactionNerError, match="KI-Namenserkennung"):
        R.apply_plan(pdf, sel, _raise)


def test_ner_spans_beyond_segment_are_clamped():
    def bad(texts):
        return [[(-3, len(t) + 50)] if t == "Reiter" else [] for t in texts]

    def build(doc, page):
        page.insert_text((40, 80), "Reiter", fontsize=9)
        page.insert_text((300, 80), "Kostenstelle", fontsize=9)

    plan = R.build_plan(make_pdf(build), R.Criteria(("ki_namen",), (), False, True), bad)
    assert [c.text for c in plan.candidates] == ["Reiter"]


def test_ner_span_split_at_cell_borders():
    text = "Jan\x00Reiter\x00Stahl, Armin"
    assert [text[a:b] for a, b in _hard_parts(text, 0, len(text))] == [
        "Jan",
        "Reiter",
        "Stahl, Armin",
    ]


def test_short_segments_edges():
    assert _short_segments("") == []
    assert _short_segments("\x00") == []
    text = "Prof. Dr. Rainer Zufall\x00 \x00Heide, Erika\x00"
    assert [text[a:b] for a, b in _short_segments(text)] == ["Rainer Zufall", "Heide, Erika"]
    assert _short_segments("eins zwei drei vier fünf sechs sieben") == []
    assert _hard_parts("Jan", -5, 99) == [(0, 3)]


# ── spaCy-Adapter mit Attrappe ──────────────────────────────────


@dataclass
class _Ent:
    start_char: int
    end_char: int
    label_: str


@dataclass
class _Doc:
    ents: list[_Ent]


class _FakeSpacy:
    """Attrappe einer spaCy-Pipeline: Personen nach festen Wörtern."""

    def __init__(self, *names: str):
        self.names = names
        self.calls: list[list[str]] = []

    def pipe(self, texts):
        texts = list(texts)
        self.calls.append(texts)
        for t in texts:
            ents = [_Ent(m.start(), m.end(), "PER") for n in self.names for m in re.finditer(n, t)]
            ents += [_Ent(m.start(), m.end(), "LOC") for m in re.finditer("Kassel", t)]
            yield _Doc(ents)


def test_spacy_ner_adapter_reports_only_persons():
    nlp = _FakeSpacy("Erika Musterfrau")
    ner = R.spacy_ner(nlp)
    assert ner(["Erika Musterfrau aus Kassel", "Kassel"]) == [[(0, 16)], []]
    pdf = lines_pdf(["Es erschien Erika Musterfrau aus Kassel."])
    found = plan_texts(pdf, ner)
    assert count(found, "ki_namen", "Erika Musterfrau") == 1
    assert not any(t == "Kassel" for _p, _s, t in found)
    assert nlp.calls
