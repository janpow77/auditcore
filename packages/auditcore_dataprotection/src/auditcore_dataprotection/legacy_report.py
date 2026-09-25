"""Legacy-exact HTML report of ``regulierung@a5d48ea`` (``export.baue_bericht_html``).

The report is assembled section by section; every section returns the HTML
fragments of the source in the same order, so the joined document stays
byte-identical.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from html import escape
from typing import Any

from .legacy_scoring import REGIME_DSGVO, REGIME_JI, legacy_norm, legacy_profile
from .rules import RuleProfile

_STYLE = [
    "<style>",
    "@page { size: A4; margin: 2cm 2cm 2cm 2.5cm; }",
    "body { font-family: Arial, sans-serif; font-size: 10pt; color: #000; }",
    "h1 { font-size: 15pt; margin-bottom: 2mm; }",
    "h2 { font-size: 12pt; margin-top: 7mm; border-bottom: 0.5pt solid #888; }",
    "h3 { font-size: 10.5pt; margin-top: 4mm; }",
    "table { width: 100%; border-collapse: collapse; margin-top: 2mm; }",
    "th, td { border: 0.5pt solid #999; padding: 1.5mm; text-align: left;"
    " vertical-align: top; font-size: 9pt; }",
    "th { background: #e8eaf0; }",
    ".klein { font-size: 8pt; color: #444; }",
    ".hinweis { background: #f4f4f4; padding: 2mm; margin-top: 2mm; }",
    "</style></head><body>",
]
_SUBJECT_ROWS = (
    ("Zweck", "zweck"),
    ("Rechtsgrundlage", "ermaechtigungsgrundlage"),
    ("Kategorien betroffener Personen", "kategorien_betroffene"),
    ("Kategorien der Daten", "kategorien_daten"),
    ("Empfänger", "kategorien_empfaenger"),
)


def format_datetime_de(value: object) -> str:
    """``dd.mm.YYYY HH:MM`` of a datetime; a dash for anything else (source format)."""
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    return "–"


def _row(label: str, value: str, style: str = "") -> str:
    return f"<tr><th{style}>{label}</th><td>{value}</td></tr>"


def _yes_no(value: object) -> str:
    return "Ja" if value else "Nein"


@dataclass(frozen=True)
class _Context:
    """Record, regime and profiles the report sections share."""

    record: Mapping[str, Any]
    regime: str
    profile: RuleProfile
    dsgvo: RuleProfile

    def norm(self, key: str) -> str:
        """Norm of the record's regime."""
        return legacy_norm(self.regime, key)


def _head(ctx: _Context, tenant_label: str) -> list[str]:
    return [
        "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'>",
        *_STYLE,
        "<h1>Datenschutz-Folgenabschätzung</h1>",
        f"<p class='klein'>{escape(ctx.norm('dsfa'))} &middot; "
        f"{escape(ctx.profile.regime_title)}"
        f"{' &middot; ' + escape(tenant_label) if tenant_label else ''}</p>",
    ]


def _subject(ctx: _Context) -> list[str]:
    """Section 1: the activity as recorded when the assessment was made."""
    record = ctx.record
    snapshot = record.get("taetigkeit_abbild") or {}
    status = record.get("status")
    status_text = ctx.dsgvo.status_texts.get(str(status), status)
    return [
        "<h2>1. Gegenstand der Verarbeitung</h2>",
        "<table>",
        _row(
            "Verarbeitungstätigkeit",
            escape(str(record.get("taetigkeit_name"))),
            " style='width:32%'",
        ),
        *(_row(label, escape(str(snapshot.get(key) or "–"))) for label, key in _SUBJECT_ROWS),
        _row("Übermittlung in ein Drittland", _yes_no(snapshot.get("drittlandtransfer"))),
        _row(
            "Fassung",
            f"Nummer {record.get('version')}, Stand {status_text};"
            f" beruht auf Fassung {record.get('vvt_version')} des Verzeichnisses von "
            "Verarbeitungstätigkeiten",
        ),
        "</table>",
        "<p class='klein'>Die Angaben stammen aus dem Verzeichnis von "
        f"Verarbeitungstätigkeiten nach {escape(ctx.norm('verzeichnis'))} und sind mit dem "
        "Stand wiedergegeben, auf dem diese Abschätzung beruht.</p>",
    ]


def _ji_notice() -> str:
    return (
        "<div class='hinweis'>Die Verarbeitung dient der Verhütung, "
        "Verfolgung oder Ahndung von Straftaten oder Ordnungswidrigkeiten. "
        "Nach § 40 Absatz 1 HDSIG gilt dafür der Dritte Teil des HDSIG; "
        "Rechtsgrundlage der Abschätzung ist § 62 HDSIG. "
        + escape(legacy_profile(REGIME_JI).regime_notice)
        + " Die Regelbeispiele des Artikels 35 Absatz 3 DSGVO, die Liste nach "
        "Absatz 4 und der Standpunkt der betroffenen Personen nach Absatz 9 "
        "werden deshalb weiter angewandt und mitzitiert.</div>"
    )


def _answer_rows(ctx: _Context, block: str, title: str) -> list[str]:
    """One table per question block; answers are shown by truthiness like the source."""
    answers = ctx.record.get("antworten") or {}
    questions = [q for q in ctx.dsgvo.questions if q.block == block]
    if not questions:
        return []
    parts = [
        f"<h3>{escape(title)}</h3>",
        "<table><tr><th style='width:52%'>Frage</th><th style='width:8%'>Antwort</th>"
        "<th style='width:20%'>Fundstelle</th><th>Begründung</th></tr>",
    ]
    for question in questions:
        answer = answers.get(question.key) or {}
        given = answer.get("ja") if isinstance(answer, dict) else answer
        justification = (answer.get("begruendung") if isinstance(answer, dict) else "") or ""
        parts.append(
            f"<tr><td>{escape(question.text)}</td>"
            f"<td>{'Ja' if given else 'Nein'}</td>"
            f"<td class='klein'>{escape(question.legal_basis)}</td>"
            f"<td>{escape(str(justification))}</td></tr>"
        )
    parts.append("</table>")
    return parts


def _screening(ctx: _Context) -> list[str]:
    """Section 2: every question, the result and the FRIA hint."""
    screening = (ctx.record.get("vorschlag") or {}).get("schwellwert") or {}
    parts = ["<h2>2. Schwellwertanalyse</h2>"]
    if ctx.regime == REGIME_JI:
        parts.append(_ji_notice())
    for block, title in ctx.dsgvo.blocks:
        parts.extend(_answer_rows(ctx, block, title))
    parts += [
        "<div class='hinweis'>",
        f"<b>Ergebnis:</b> {escape(str(screening.get('begruendung') or '–'))}",
        "</div>",
    ]
    if screening.get("fria_erforderlich"):
        parts.append(
            "<p><b>Hinweis:</b> Es handelt sich um ein Hochrisiko-KI-System nach "
            "Anhang III der Verordnung (EU) 2024/1689. Die Grundrechte-Folgenabschätzung "
            "nach Artikel 27 dieser Verordnung ist zusätzlich zu erstellen; sie darf "
            "nach Artikel 27 Absatz 4 mit dieser Abschätzung verbunden werden.</p>"
        )
    return parts


def _necessity(ctx: _Context) -> list[str]:
    """Section 3: necessity, proportionality and the data subjects' view."""
    record = ctx.record
    return [
        "<h2>3. Notwendigkeit und Verhältnismäßigkeit</h2>",
        "<table>",
        "<tr><th style='width:28%'>Notwendigkeit der Verarbeitung "
        "in Bezug auf den Zweck</th><td>"
        f"{escape(record.get('notwendigkeit') or '–')}</td></tr>",
        "<tr><th>Verhältnismäßigkeit, insbesondere geprüfte mildere Mittel</th><td>"
        f"{escape(record.get('verhaeltnismaessigkeit') or '–')}</td></tr>",
        "<tr><th>Standpunkt der betroffenen Personen oder ihrer Vertreter</th><td>"
        f"{escape(record.get('standpunkt_betroffene') or 'nicht eingeholt')}</td></tr>",
        "</table>",
        f"<p class='klein'>{escape(ctx.norm('notwendigkeit'))} verlangt die Bewertung "
        "der Notwendigkeit und Verhältnismäßigkeit der Verarbeitungsvorgänge in "
        f"Bezug auf den Zweck. Standpunkt der betroffenen Personen: "
        f"{escape(ctx.norm('standpunkt'))}.</p>",
    ]


def _dimension_cell(ctx: _Context, scenario: Mapping[str, Any]) -> str:
    """Dimension title (unknown keys stay readable) and whether it stems from the SDM."""
    key = scenario.get("dimension", "")
    text = escape(str(ctx.dsgvo.dimensions.get(key, key)))
    dimension = scenario.get("dimension", "")
    if not dimension:
        return text
    if dimension in ctx.dsgvo.sdm_dimensions:
        return text + " <span class='klein'>(SDM)</span>"
    return text + " <span class='klein'>(Rechte und Freiheiten)</span>"


def _scenario_row(ctx: _Context, scenario: Mapping[str, Any]) -> str:
    measures = ", ".join(scenario.get("massnahmen_bezeichnungen") or []) or "–"
    return (
        "<tr>"
        f"<td>{_dimension_cell(ctx, scenario)}</td>"
        f"<td>{escape(str(scenario.get('beschreibung') or ''))}</td>"
        f"<td>Schwere {scenario.get('brutto_schwere')}, Wahrscheinlichkeit "
        f"{scenario.get('brutto_wahrscheinlichkeit')} = {scenario.get('brutto')} "
        f"({escape(str(scenario.get('brutto_stufe')))})</td>"
        f"<td class='klein'>{escape(measures)}</td>"
        f"<td>Schwere {scenario.get('netto_schwere')}, Wahrscheinlichkeit "
        f"{scenario.get('netto_wahrscheinlichkeit')} = {scenario.get('netto')} "
        f"({escape(str(scenario.get('netto_stufe')))})</td>"
        "</tr>"
    )


def _risk_explanation(ctx: _Context) -> str:
    return (
        "<p class='klein'>Bewertung auf einer Skala von 1 bis 4 je Schwere und "
        "Wahrscheinlichkeit; das Produkt ergibt einen Wert von 1 bis 16. "
        "Bis 4 gering, 5 bis 9 mittel, ab 10 hoch. Die mit „SDM“ "
        "gekennzeichneten Schutzziele sind die Gewährleistungsziele des "
        "Standard-Datenschutzmodells der Datenschutzkonferenz (V3.0); "
        "„Rechte und Freiheiten“ steht daneben und fasst die materiellen "
        "Grundrechtsfolgen nach Art. 35 Abs. 1 DSGVO zusammen.</p>"
        "<p class='klein'><b>Zur Minderung durch Maßnahmen.</b> Die im "
        f"Katalog nach {escape(ctx.norm('sicherheit'))} hinterlegten Stufen sind "
        "eine <i>Obergrenze für den Systemvorschlag</i> und keine "
        "rechnerische Zusicherung: Sie treten nur ein, wenn die "
        "Fachabteilung keinen eigenen Restwert einträgt. Welche Wirkung "
        "eine Maßnahme im Einzelfall tatsächlich hat, beurteilt die "
        "Fachabteilung und begründet es; die Anwendung beurteilt auch "
        "nicht, ob eine Maßnahme umgesetzt ist.</p>"
    )


def _risk(ctx: _Context) -> list[str]:
    """Section 4: scenarios before and after measures."""
    risk = (ctx.record.get("vorschlag") or {}).get("risiko") or {}
    parts = ["<h2>4. Risiken für die Rechte und Freiheiten und vorgesehene Maßnahmen</h2>"]
    if not (risk and risk.get("szenarien")):
        parts.append(
            "<div class='hinweis'>Es ist noch kein Risikoszenario erfasst. Die "
            "Bewertung der Risiken und die vorgesehenen Abhilfemaßnahmen gehören "
            f"zum Mindestinhalt ({escape(ctx.norm('risiko'))}, "
            f"{escape(ctx.norm('massnahmen'))}); "
            "ohne sie ist keine Freigabe möglich.</div>"
        )
        return parts
    parts.append(
        "<table><tr><th style='width:16%'>Schutzziel</th><th style='width:26%'>Szenario</th>"
        "<th>Vor Maßnahmen</th><th>Maßnahmen</th><th>Nach Maßnahmen</th></tr>"
    )
    parts.extend(_scenario_row(ctx, scenario) for scenario in risk["szenarien"])
    parts.append("</table>")
    parts.append(_risk_explanation(ctx))
    return parts


def _dpo_rows(ctx: _Context) -> list[str]:
    """DPO involvement, the conclusion drawn from it and the leadership submission."""
    record = ctx.record
    vote = record.get("dsb_votum")
    parts = [
        f"<tr><th>Beteiligung der oder des Datenschutzbeauftragten</th><td>"
        f"{format_datetime_de(record.get('dsb_beteiligt_am'))}, Votum: "
        f"{escape(ctx.dsgvo.vote_texts.get(vote or '', 'noch offen'))}</td></tr>",
        _row("Stellungnahme", escape(str(record.get("dsb_stellungnahme") or "–"))),
    ]
    if record.get("dsb_folgerung"):
        label = (
            "Abweichung von der Stellungnahme"
            if vote == "abgelehnt"
            else "Umgang mit der Stellungnahme"
        )
        parts.append(
            f"<tr><th>{label}</th><td>{escape(str(record.get('dsb_folgerung')))}</td></tr>"
        )
    if record.get("leitung_vorgelegt_am"):
        parts.append(
            "<tr><th>Der Behördenleitung vorgelegt</th><td>"
            f"{escape(str(record.get('leitung_vorgelegt_an') or '–'))} am "
            f"{format_datetime_de(record.get('leitung_vorgelegt_am'))}</td></tr>"
        )
    if vote == "abgelehnt":
        parts.append(
            "<tr><th>Hinweis</th><td class='klein'>Die Abschätzung ist trotz "
            "ablehnender Stellungnahme freigegeben worden. Die oder der "
            "Datenschutzbeauftragte berät und entscheidet nicht (Art. 38 Abs. 3 "
            "DSGVO); die Verantwortung für die Verarbeitung trägt der "
            "Verantwortliche (Art. 24 DSGVO).</td></tr>"
        )
    return parts


def _lifecycle(ctx: _Context) -> list[str]:
    record = ctx.record
    releaser = record.get("freigeber")
    released = (
        f"{escape(str(releaser))} am {format_datetime_de(record.get('freigegeben_am'))}"
        if releaser
        else "noch nicht freigegeben"
    )
    return [
        _row(
            "Erstellt",
            f"{escape(str(record.get('ersteller')))} am "
            f"{format_datetime_de(record.get('erstellt_am'))}",
        ),
        "<tr><th>Freigegeben</th><td>" + released + "</td></tr>",
        "</table>",
        "<p class='klein'>Die Beteiligung der oder des Datenschutzbeauftragten beruht "
        f"auf {escape(ctx.norm('dsb'))}. Freigegeben wird durch eine zweite Person; "
        "freigegebene Fassungen sind unveränderlich. Die Abschätzung ist zu "
        f"überprüfen, wenn sich das Risiko ändert ({escape(ctx.norm('ueberpruefung'))}).</p>",
        "</body></html>",
    ]


def _decision(ctx: _Context) -> list[str]:
    """Section 5: proposal, decision, DPO involvement and lifecycle."""
    record = ctx.record
    proposal = record.get("vorschlag") or {}
    parts = [
        "<h2>5. Ergebnis und Entscheidung</h2>",
        "<table>",
        f"<tr><th style='width:32%'>Vorschlag des Systems</th>"
        f"<td>{escape(str(proposal.get('empfehlung_text') or '–'))}</td></tr>",
        _row("Begründung", escape(str(proposal.get("begruendung") or "–"))),
        _row("Entscheidung", escape(str(record.get("entscheidung") or "noch offen"))),
    ]
    if record.get("abweichung"):
        parts.append(
            "<tr><th>Abweichung vom Vorschlag</th><td>"
            f"{escape(str(record.get('abweichung_begruendung') or ''))}</td></tr>"
        )
    return parts + _dpo_rows(ctx) + _lifecycle(ctx)


def legacy_report_html(record: Mapping[str, Any], tenant_label: str = "") -> str:
    """``export.baue_bericht_html`` for a record shaped like ``verwaltung.als_json``
    plus ``taetigkeit_abbild``; datetimes as :class:`datetime`."""
    regime = record.get("rechtsregime") or REGIME_DSGVO
    ctx = _Context(record, regime, legacy_profile(regime), legacy_profile(REGIME_DSGVO))
    parts = [
        *_head(ctx, tenant_label),
        *_subject(ctx),
        *_screening(ctx),
        *_necessity(ctx),
        *_risk(ctx),
        *_decision(ctx),
    ]
    return "".join(parts)
