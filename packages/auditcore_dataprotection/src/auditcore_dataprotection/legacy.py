"""Behavior-compatible adapter for the source application ``regulierung``.

These functions reproduce the characterized outputs of
``regulierung@a5d48ea`` exactly, including behavior this library corrects in
its own contract (see ``docs/behavior-changes.md``): unknown questions are
skipped, truthy strings count as "yes", empty surveys yield
``nur_schwellwert`` and explicit residual values are not range-checked.

They exist so an existing consumer can switch to the installed package
without changing results, and so the differences to the corrected contract
stay testable. New consumers should use :mod:`auditcore_dataprotection.calculation`
and :mod:`auditcore_dataprotection.assessment` instead.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from html import escape
from typing import Any

from .errors import ValidationError
from .rules import (
    EFFECT_FRIA,
    EFFECT_HARD,
    EFFECT_POINT,
    RECOMMENDATION_CONSULTATION,
    RECOMMENDATION_RELEASE,
    RECOMMENDATION_RELEASE_WITH_CONDITIONS,
    RECOMMENDATION_SCREENING_ONLY,
    RuleProfile,
    load_profile,
)

LEGACY_PROFILE_VERSION = "2026.09.1"
REGIME_DSGVO = "dsgvo"
REGIME_JI = "hdsig_ji"
PFLICHT = "pflicht"
KEINE_PFLICHT = "keine_pflicht"
#: Legacy keyword heuristic of the source application (KPAnG enforcement).
REGIME_KEYWORDS = ("ordnungswidrigkeit", "bußgeld", "bussgeld", "owi", "vollzug", "kpang")
PLACEHOLDER_EMPTY = "(noch einzutragen)"
_PLACEHOLDER_EXEMPT = frozenset({"dsb_anrede", "dsb_titel", "plz", "dsb_plz"})


@cache
def legacy_profile(regime: str) -> RuleProfile:
    """Packaged source profile; unknown regimes fall back to DSGVO like the source."""
    key = "regulierung.hdsig_ji" if regime == REGIME_JI else "regulierung.dsgvo"
    return load_profile(key, LEGACY_PROFILE_VERSION)


def _questions() -> dict[str, Any]:
    return {q.key: q for q in legacy_profile(REGIME_DSGVO).questions}


def _measures() -> dict[str, Any]:
    return {m.key: m for m in legacy_profile(REGIME_DSGVO).measures}


def legacy_reference(question_key: str, regime: str = REGIME_DSGVO) -> str:
    """``katalog.fundstelle``: DSGVO basis, in JI additionally the HDSIG counterpart."""
    if regime != REGIME_JI:
        return str(_questions()[question_key].legal_basis)
    return str(legacy_profile(REGIME_JI).question(question_key).reference)


def legacy_norm(regime: str, key: str) -> str:
    """``katalog.norm``: unknown regimes use the DSGVO norms."""
    return legacy_profile(regime if regime == REGIME_JI else REGIME_DSGVO).norm(key)


def legacy_recommendation_text(recommendation: str, regime: str = REGIME_DSGVO) -> str:
    """Recommendation text of the regime (DSGVO for unknown regimes)."""
    return legacy_profile(regime).recommendation_texts[recommendation]


def legacy_risk_level(value: int) -> str:
    """``bewertung.risikostufe``."""
    if value <= 0:
        return "offen"
    if value <= 4:
        return "gering"
    if value <= 9:
        return "mittel"
    return "hoch"


@dataclass(frozen=True)
class LegacyAnswer:
    """Field-compatible with ``bewertung.Antwort``."""

    schluessel: str
    ja: Any
    begruendung: str = ""


@dataclass(frozen=True)
class LegacyScenario:
    """Field-compatible with ``bewertung.Szenario``."""

    dimension: str
    beschreibung: str
    schwere: int
    wahrscheinlichkeit: int
    massnahmen: tuple[str, ...] = ()
    netto_schwere: int | None = None
    netto_wahrscheinlichkeit: int | None = None

    @property
    def brutto(self) -> int:
        """Gross risk: severity × likelihood."""
        return self.schwere * self.wahrscheinlichkeit


@dataclass
class LegacyThreshold:
    """Field-compatible with ``bewertung.Schwellwertergebnis``."""

    ergebnis: str
    punkte: int
    regime: str = REGIME_DSGVO
    harte_ausloeser: list[str] = field(default_factory=list)
    punkt_kriterien: list[str] = field(default_factory=list)
    fria_erforderlich: bool = False
    begruendung: str = ""


def legacy_threshold(
    answers: Sequence[LegacyAnswer], regime: str = REGIME_DSGVO
) -> LegacyThreshold:
    """``bewertung.werte_schwellwert_aus`` including skipped unknown keys and truthiness."""
    questions = _questions()
    hard: list[str] = []
    points: list[str] = []
    fria = False
    for answer in answers:
        question = questions.get(answer.schluessel)
        if question is None or not answer.ja:
            continue
        if question.effect == EFFECT_HARD:
            hard.append(question.key)
        elif question.effect == EFFECT_POINT:
            points.append(question.key)
        elif question.effect == EFFECT_FRIA:
            fria = True
    score = len(points)
    threshold = legacy_profile(REGIME_DSGVO).points_threshold
    if hard:
        result = PFLICHT
        references = "; ".join(legacy_reference(s, regime) for s in hard)
        if regime == REGIME_JI:
            reasoning = (
                f"Die Datenschutz-Folgenabschätzung ist durchzuführen "
                f"({legacy_norm(regime, 'pflicht')}). Erfüllt ist: {references}. "
                "Der Dritte Teil des HDSIG kennt die Regelbeispiele des Art. 35 "
                "Abs. 3 DSGVO und die Liste nach Abs. 4 nicht; sie werden hier "
                "als strengerer Maßstab angewandt, weil die Abgrenzung beider "
                "Rechtsakte auf europäischer Ebene nicht geklärt ist."
            )
        elif len(hard) == 1:
            reasoning = (
                f"Die Datenschutz-Folgenabschätzung ist durchzuführen, weil "
                f"{len(hard)} Muss-Kriterium bejaht wurde: {references}."
            )
        else:
            reasoning = (
                f"Die Datenschutz-Folgenabschätzung ist durchzuführen, weil "
                f"{len(hard)} Muss-Kriterien bejaht wurden: {references}."
            )
    elif score >= threshold:
        result = PFLICHT
        reasoning = (
            f"Es sind {score} der neun Kriterien des Europäischen "
            f"Datenschutzausschusses erfüllt. Ab {threshold} Kriterien ist "
            "regelmäßig von einem voraussichtlich hohen Risiko auszugehen "
            "(WP 248 rev.01); die Folgenabschätzung ist durchzuführen."
        )
    else:
        result = KEINE_PFLICHT
        reasoning = (
            f"Kein Muss-Kriterium ist erfüllt und es sind {score} der neun "
            f"Kriterien des Europäischen Datenschutzausschusses bejaht, also "
            f"weniger als {threshold}. Eine Folgenabschätzung ist damit "
            "nicht erforderlich; das Ergebnis ist gleichwohl zu dokumentieren "
            f"({legacy_norm(regime, 'nachweis')})."
        )
    if fria:
        reasoning += (
            " Zusätzlich handelt es sich um ein Hochrisiko-KI-System; die "
            "Grundrechte-Folgenabschätzung nach Art. 27 der Verordnung (EU) "
            "2024/1689 ist zu erstellen und darf mit dieser Abschätzung "
            "verbunden werden (Art. 27 Abs. 4)."
        )
    return LegacyThreshold(
        ergebnis=result,
        regime=regime,
        punkte=score,
        harte_ausloeser=hard,
        punkt_kriterien=points,
        fria_erforderlich=fria,
        begruendung=reasoning,
    )


def _legacy_net(scenario: LegacyScenario) -> tuple[int, int, list[str]]:
    measures = _measures()
    reduce_l = 0
    reduce_s = 0
    titles: list[str] = []
    for key in scenario.massnahmen:
        measure = measures.get(key)
        if measure is None:
            continue
        titles.append(measure.title)
        reduce_l += measure.reduces_likelihood
        reduce_s += measure.reduces_severity
    severity = scenario.netto_schwere
    if severity is None:
        severity = max(1, scenario.schwere - min(2, reduce_s))
    likelihood = scenario.netto_wahrscheinlichkeit
    if likelihood is None:
        likelihood = max(1, scenario.wahrscheinlichkeit - min(2, reduce_l))
    return severity, likelihood, titles


def legacy_risk(scenarios: Sequence[LegacyScenario]) -> dict[str, Any]:
    """``asdict(bewertung.werte_risiko_aus(...))``."""
    rows: list[dict[str, Any]] = []
    gross_max = 0
    net_max = 0
    for scenario in scenarios:
        severity, likelihood, titles = _legacy_net(scenario)
        net = severity * likelihood
        gross_max = max(gross_max, scenario.brutto)
        net_max = max(net_max, net)
        rows.append(
            {
                "dimension": scenario.dimension,
                "beschreibung": scenario.beschreibung,
                "brutto_schwere": scenario.schwere,
                "brutto_wahrscheinlichkeit": scenario.wahrscheinlichkeit,
                "brutto": scenario.brutto,
                "brutto_stufe": legacy_risk_level(scenario.brutto),
                "massnahmen": list(scenario.massnahmen),
                "massnahmen_bezeichnungen": titles,
                "netto_schwere": severity,
                "netto_wahrscheinlichkeit": likelihood,
                "netto": net,
                "netto_stufe": legacy_risk_level(net),
            }
        )
    return {
        "brutto_hoechstwert": gross_max,
        "netto_hoechstwert": net_max,
        "stufe": legacy_risk_level(net_max),
        "szenarien": rows,
    }


def _criteria_json(keys: Sequence[str], regime: str) -> list[dict[str, str]]:
    questions = _questions()
    return [
        {"schluessel": s, "text": questions[s].text, "rechtsgrundlage": legacy_reference(s, regime)}
        for s in keys
    ]


def legacy_proposal(
    answers: Sequence[LegacyAnswer],
    scenarios: Sequence[LegacyScenario] | None = None,
    regime: str = REGIME_DSGVO,
) -> dict[str, Any]:
    """``vorschlag_als_json(erstelle_vorschlag(...))`` byte-for-byte as JSON value."""
    threshold = legacy_threshold(answers, regime)
    screening = {
        "ergebnis": threshold.ergebnis,
        "punkte": threshold.punkte,
        "harte_ausloeser": _criteria_json(threshold.harte_ausloeser, regime),
        "punkt_kriterien": _criteria_json(threshold.punkt_kriterien, regime),
        "fria_erforderlich": threshold.fria_erforderlich,
        "begruendung": threshold.begruendung,
    }

    def result(
        risk: dict[str, Any] | None, recommendation: str, text: str, reasoning: str
    ) -> dict[str, Any]:
        """Assemble the legacy proposal document."""
        return {
            "schwellwert": screening,
            "risiko": risk,
            "regime": regime,
            "empfehlung": recommendation,
            "empfehlung_text": text,
            "begruendung": reasoning,
        }

    if threshold.ergebnis == KEINE_PFLICHT:
        return result(
            None,
            RECOMMENDATION_SCREENING_ONLY,
            legacy_recommendation_text(RECOMMENDATION_SCREENING_ONLY, regime),
            threshold.begruendung,
        )
    risk = legacy_risk(list(scenarios or []))
    if not (scenarios or []):
        return result(
            risk,
            RECOMMENDATION_CONSULTATION,
            "Die Folgenabschätzung ist durchzuführen, es sind aber noch keine "
            "Risikoszenarien erfasst. Ohne Risikobetrachtung lässt sich das "
            f"verbleibende Risiko nicht beurteilen ({legacy_norm(regime, 'risiko')}).",
            threshold.begruendung,
        )
    if risk["netto_hoechstwert"] >= 10:
        recommendation = RECOMMENDATION_CONSULTATION
    elif risk["netto_hoechstwert"] >= 5:
        recommendation = RECOMMENDATION_RELEASE_WITH_CONDITIONS
    else:
        recommendation = RECOMMENDATION_RELEASE
    reasoning = (
        f"{threshold.begruendung} Das höchste Risiko vor Maßnahmen beträgt "
        f"{risk['brutto_hoechstwert']} von 16, nach den vorgesehenen Maßnahmen "
        f"{risk['netto_hoechstwert']} von 16 und ist damit als "
        f"{risk['stufe']} einzustufen."
    )
    return result(
        risk, recommendation, legacy_recommendation_text(recommendation, regime), reasoning
    )


def legacy_prefill(activity: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """``bewertung.vorbelegung_aus_taetigkeit`` (bool conversion, locale ``n`` format)."""
    threshold = legacy_profile(REGIME_DSGVO).large_scale_threshold
    special = bool(activity.get("besondere_kategorien"))
    criminal = bool(activity.get("daten_art10"))
    persons = activity.get("anzahl_betroffene")
    try:
        count = int(persons) if persons not in (None, "") else 0
    except (TypeError, ValueError):
        count = 0
    large = count >= threshold
    suggestions: dict[str, dict[str, Any]] = {}
    if special or criminal:
        source = "Artikel 9" if special else "Artikel 10"
        suggestions["edsa_04_sensible_daten"] = {
            "ja": True,
            "grund": f"Das Verarbeitungsverzeichnis weist Daten nach {source} DSGVO aus.",
        }
        if large:
            suggestions["art35_3_b"] = {
                "ja": True,
                "grund": (
                    f"Das Verzeichnis weist Daten nach {source} DSGVO und "
                    f"{count:n} betroffene Personen aus; das spricht für eine "
                    "umfangreiche Verarbeitung."
                ),
            }
    if large:
        suggestions["edsa_05_umfang"] = {
            "ja": True,
            "grund": (
                f"Das Verzeichnis nennt {count:n} betroffene Personen und liegt "
                f"damit über dem Anhaltswert von {threshold:n}."
            ),
        }
    if activity.get("drittlandtransfer"):
        suggestions["edsa_06_abgleich"] = {
            "ja": False,
            "grund": (
                "Das Verzeichnis weist eine Übermittlung in ein Drittland aus. Das "
                "ist für sich kein Kriterium der Liste, erhöht aber das Risiko und "
                "ist bei den Szenarien zu berücksichtigen (Kapitel V DSGVO)."
            ),
        }
    return suggestions


# ---------------------------------------------------------------------------
# Administration adapter (verwaltung.py, pure parts)
# ---------------------------------------------------------------------------


def legacy_answers_from_json(answers: Mapping[str, Any] | None) -> list[LegacyAnswer]:
    """``verwaltung._antworten_aus_json``: unknown keys dropped, ``bool()`` conversion."""
    questions = _questions()
    read: list[LegacyAnswer] = []
    for key, value in (answers or {}).items():
        if key not in questions:
            continue
        if isinstance(value, dict):
            read.append(
                LegacyAnswer(key, bool(value.get("ja")), str(value.get("begruendung") or ""))
            )
        else:
            read.append(LegacyAnswer(key, bool(value)))
    return read


def legacy_scenarios_from_json(scenarios: Sequence[Any] | None) -> list[LegacyScenario]:
    """``verwaltung._szenarien_aus_json``: gross values 1..4, residual values unchecked."""
    read: list[LegacyScenario] = []
    for entry in scenarios or []:
        if not isinstance(entry, dict):
            continue
        try:
            read.append(
                LegacyScenario(
                    dimension=str(entry.get("dimension") or ""),
                    beschreibung=str(entry.get("beschreibung") or ""),
                    schwere=int(entry.get("schwere") or 0),
                    wahrscheinlichkeit=int(entry.get("wahrscheinlichkeit") or 0),
                    massnahmen=tuple(entry.get("massnahmen") or ()),
                    netto_schwere=(
                        int(entry["netto_schwere"])
                        if entry.get("netto_schwere") not in (None, "")
                        else None
                    ),
                    netto_wahrscheinlichkeit=(
                        int(entry["netto_wahrscheinlichkeit"])
                        if entry.get("netto_wahrscheinlichkeit") not in (None, "")
                        else None
                    ),
                )
            )
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                "Ein Risikoszenario enthält unbrauchbare Werte; Schwere und "
                "Wahrscheinlichkeit müssen ganze Zahlen von 1 bis 4 sein."
            ) from exc
    for scenario in read:
        if not (1 <= scenario.schwere <= 4 and 1 <= scenario.wahrscheinlichkeit <= 4):
            raise ValidationError(
                "Schwere und Wahrscheinlichkeit sind auf einer Skala von 1 bis 4 einzustufen."
            )
    return read


def legacy_check_regime(value: str | None) -> str:
    """``verwaltung.pruefe_regime``."""
    chosen = (value or REGIME_DSGVO).strip()
    if chosen not in (REGIME_DSGVO, REGIME_JI):
        raise ValidationError(
            f"Unbekannter Rechtsrahmen. Zulässig sind {REGIME_DSGVO} und {REGIME_JI}."
        )
    return chosen


def legacy_preview(
    answers: Mapping[str, Any], scenarios: Sequence[Any], regime: str = REGIME_DSGVO
) -> dict[str, Any]:
    """``verwaltung.berechne_vorschlag``."""
    return legacy_proposal(
        legacy_answers_from_json(answers),
        legacy_scenarios_from_json(scenarios),
        legacy_check_regime(regime),
    )


def legacy_regime_suggestion(activity: Mapping[str, Any]) -> str:
    """``verwaltung.regime_vorschlag`` keyword heuristic (source-specific, not general)."""
    text = " ".join(
        str(activity.get(name) or "") for name in ("name", "zweck", "referat", "rechtsgrundlage")
    ).casefold()
    return REGIME_JI if any(word in text for word in REGIME_KEYWORDS) else REGIME_DSGVO


def legacy_compare_activity(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """``verwaltung.vergleiche_taetigkeit``; ``(old or "") != (new or "")`` semantics."""
    differences: list[dict[str, Any]] = []
    for name, title in legacy_profile(REGIME_DSGVO).significant_fields.items():
        old = before.get(name)
        new = after.get(name)
        if (old or "") != (new or ""):
            differences.append({"feld": name, "bezeichnung": title, "vorher": old, "nachher": new})
    return differences


# ---------------------------------------------------------------------------
# Register identifiers and prefill templates (mandant_dsgvo_service.py)
# ---------------------------------------------------------------------------


def legacy_activity_identifier(name: str, position: int) -> str:
    """``taetigkeit_kennung``: SHA-1 of the case-folded name, position for duplicates."""
    raw = (name or "").strip().casefold()
    identifier = "t-" + hashlib.sha1(raw.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]
    return identifier if position <= 1 else f"{identifier}-{position}"


def legacy_activities_with_identifiers(activities: Sequence[Any] | None) -> list[dict[str, Any]]:
    """``taetigkeiten_mit_kennung``; existing identifiers stay unchanged."""
    result: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for entry in activities or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("id"):
            result.append(entry)
            continue
        name = str(entry.get("name") or "")
        seen[name] = seen.get(name, 0) + 1
        result.append({**entry, "id": legacy_activity_identifier(name, seen[name])})
    return result


def legacy_fill_placeholders(value: Any, values: Mapping[str, str]) -> Any:
    """``fuelle_platzhalter``: ``{{mandant:feld}}`` recursively, empty fields marked."""
    if isinstance(value, dict):
        return {k: legacy_fill_placeholders(v, values) for k, v in value.items()}
    if isinstance(value, list):
        return [legacy_fill_placeholders(v, values) for v in value]
    if isinstance(value, str) and value.startswith("{{mandant:") and value.endswith("}}"):
        name = value[len("{{mandant:") : -2]
        replacement = values.get(name, "")
        if not replacement and name not in _PLACEHOLDER_EXEMPT:
            return PLACEHOLDER_EMPTY
        return replacement
    return value


def legacy_catalog_json() -> dict[str, Any]:
    """``katalog.katalog_als_json``."""
    dsgvo = legacy_profile(REGIME_DSGVO)
    blocks = []
    for block, title in dsgvo.blocks:
        blocks.append(
            {
                "block": block,
                "titel": title,
                "fragen": [
                    {
                        "schluessel": q.key,
                        "text": q.text,
                        "rechtsgrundlage": q.legal_basis,
                        "wirkung": q.effect,
                        "erlaeuterung": q.explanation,
                        "vorbelegung": q.prefill,
                    }
                    for q in dsgvo.questions
                    if q.block == block
                ],
            }
        )
    return {
        "bloecke": blocks,
        "regime": [
            {
                "schluessel": profile.regime,
                "titel": profile.regime_title,
                "erlaeuterung": profile.regime_explanation,
                "hinweis": profile.regime_notice,
                "normen": dict(profile.norms),
            }
            for profile in (dsgvo, legacy_profile(REGIME_JI))
        ],
        "schwelle_punkte": dsgvo.points_threshold,
        "dimensionen": dict(dsgvo.dimensions),
        "sdm_dimensionen": sorted(dsgvo.sdm_dimensions),
        "standpunkt_begruendungen": [dict(t) for t in dsgvo.data_subject_view_templates],
        "schwere": {str(k): v for k, v in dsgvo.severity_levels.items()},
        "wahrscheinlichkeit": {str(k): v for k, v in dsgvo.likelihood_levels.items()},
        "massnahmen": [
            {
                "schluessel": m.key,
                "bezeichnung": m.title,
                "rechtsgrundlage": m.legal_basis,
                "senkt_wahrscheinlichkeit": m.reduces_likelihood,
                "senkt_schwere": m.reduces_severity,
                "erlaeuterung": m.explanation,
            }
            for m in dsgvo.measures
        ],
    }


# ---------------------------------------------------------------------------
# Report (export.py, HTML)
# ---------------------------------------------------------------------------


def _date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    return "–"


def _row(label: str, value: str, style: str = "") -> str:
    return f"<tr><th{style}>{label}</th><td>{value}</td></tr>"


def _yes_no(value: Any) -> str:
    return "Ja" if value else "Nein"


def legacy_report_html(record: Mapping[str, Any], tenant_label: str = "") -> str:
    """``export.baue_bericht_html`` for a record shaped like ``verwaltung.als_json``
    plus ``taetigkeit_abbild``; datetimes as :class:`datetime`."""
    profile_dsgvo = legacy_profile(REGIME_DSGVO)
    status_text = profile_dsgvo.status_texts
    vote_text = profile_dsgvo.vote_texts
    proposal = record.get("vorschlag") or {}
    screening = proposal.get("schwellwert") or {}
    risk = proposal.get("risiko") or {}
    answers = record.get("antworten") or {}
    snapshot = record.get("taetigkeit_abbild") or {}
    regime = record.get("rechtsregime") or REGIME_DSGVO
    profile = legacy_profile(regime)

    def n(key: str) -> str:
        """Norm of the record's regime."""
        return legacy_norm(regime, key)

    def dimension_text(scenario: Mapping[str, Any]) -> str:
        """Dimension title; unknown keys stay readable."""
        key = scenario.get("dimension", "")
        return str(profile_dsgvo.dimensions.get(key, key))

    def origin(dimension: str) -> str:
        """Marker whether the dimension stems from the SDM."""
        if not dimension:
            return ""
        if dimension in profile_dsgvo.sdm_dimensions:
            return " <span class='klein'>(SDM)</span>"
        return " <span class='klein'>(Rechte und Freiheiten)</span>"

    parts: list[str] = [
        "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'>",
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
        "<h1>Datenschutz-Folgenabschätzung</h1>",
        f"<p class='klein'>{escape(n('dsfa'))} &middot; "
        f"{escape(profile.regime_title)}"
        f"{' &middot; ' + escape(tenant_label) if tenant_label else ''}</p>",
    ]
    status = record.get("status")
    parts += [
        "<h2>1. Gegenstand der Verarbeitung</h2>",
        "<table>",
        _row(
            "Verarbeitungstätigkeit",
            escape(str(record.get("taetigkeit_name"))),
            " style='width:32%'",
        ),
        _row("Zweck", escape(str(snapshot.get("zweck") or "–"))),
        _row("Rechtsgrundlage", escape(str(snapshot.get("ermaechtigungsgrundlage") or "–"))),
        _row(
            "Kategorien betroffener Personen",
            escape(str(snapshot.get("kategorien_betroffene") or "–")),
        ),
        _row("Kategorien der Daten", escape(str(snapshot.get("kategorien_daten") or "–"))),
        _row("Empfänger", escape(str(snapshot.get("kategorien_empfaenger") or "–"))),
        _row("Übermittlung in ein Drittland", _yes_no(snapshot.get("drittlandtransfer"))),
        _row(
            "Fassung",
            f"Nummer {record.get('version')}, Stand {status_text.get(str(status), status)};"
            f" beruht auf Fassung {record.get('vvt_version')} des Verzeichnisses von "
            "Verarbeitungstätigkeiten",
        ),
        "</table>",
        "<p class='klein'>Die Angaben stammen aus dem Verzeichnis von "
        f"Verarbeitungstätigkeiten nach {escape(n('verzeichnis'))} und sind mit dem "
        "Stand wiedergegeben, auf dem diese Abschätzung beruht.</p>",
    ]
    parts += ["<h2>2. Schwellwertanalyse</h2>"]
    if regime == REGIME_JI:
        parts.append(
            "<div class='hinweis'>Die Verarbeitung dient der Verhütung, "
            "Verfolgung oder Ahndung von Straftaten oder Ordnungswidrigkeiten. "
            "Nach § 40 Absatz 1 HDSIG gilt dafür der Dritte Teil des HDSIG; "
            "Rechtsgrundlage der Abschätzung ist § 62 HDSIG. "
            + escape(legacy_profile(REGIME_JI).regime_notice)
            + " Die Regelbeispiele des Artikels 35 Absatz 3 DSGVO, die Liste nach "
            "Absatz 4 und der Standpunkt der betroffenen Personen nach Absatz 9 "
            "werden deshalb weiter angewandt und mitzitiert.</div>"
        )
    for block, title in profile_dsgvo.blocks:
        questions = [q for q in profile_dsgvo.questions if q.block == block]
        if not questions:
            continue
        parts.append(f"<h3>{escape(title)}</h3>")
        parts.append(
            "<table><tr><th style='width:52%'>Frage</th><th style='width:8%'>Antwort</th>"
            "<th style='width:20%'>Fundstelle</th><th>Begründung</th></tr>"
        )
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
    parts += [
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
        f"<p class='klein'>{escape(n('notwendigkeit'))} verlangt die Bewertung "
        "der Notwendigkeit und Verhältnismäßigkeit der Verarbeitungsvorgänge in "
        f"Bezug auf den Zweck. Standpunkt der betroffenen Personen: "
        f"{escape(n('standpunkt'))}.</p>",
    ]
    parts.append("<h2>4. Risiken für die Rechte und Freiheiten und vorgesehene Maßnahmen</h2>")
    if not (risk and risk.get("szenarien")):
        parts.append(
            "<div class='hinweis'>Es ist noch kein Risikoszenario erfasst. Die "
            "Bewertung der Risiken und die vorgesehenen Abhilfemaßnahmen gehören "
            f"zum Mindestinhalt ({escape(n('risiko'))}, {escape(n('massnahmen'))}); "
            "ohne sie ist keine Freigabe möglich.</div>"
        )
    else:
        parts += [
            "<table><tr><th style='width:16%'>Schutzziel</th><th style='width:26%'>Szenario</th>"
            "<th>Vor Maßnahmen</th><th>Maßnahmen</th><th>Nach Maßnahmen</th></tr>",
        ]
        for scenario in risk["szenarien"]:
            measures = ", ".join(scenario.get("massnahmen_bezeichnungen") or []) or "–"
            parts.append(
                "<tr>"
                f"<td>{escape(dimension_text(scenario))}"
                f"{origin(scenario.get('dimension', ''))}</td>"
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
        parts.append("</table>")
        parts.append(
            "<p class='klein'>Bewertung auf einer Skala von 1 bis 4 je Schwere und "
            "Wahrscheinlichkeit; das Produkt ergibt einen Wert von 1 bis 16. "
            "Bis 4 gering, 5 bis 9 mittel, ab 10 hoch. Die mit „SDM“ "
            "gekennzeichneten Schutzziele sind die Gewährleistungsziele des "
            "Standard-Datenschutzmodells der Datenschutzkonferenz (V3.0); "
            "„Rechte und Freiheiten“ steht daneben und fasst die materiellen "
            "Grundrechtsfolgen nach Art. 35 Abs. 1 DSGVO zusammen.</p>"
            "<p class='klein'><b>Zur Minderung durch Maßnahmen.</b> Die im "
            f"Katalog nach {escape(n('sicherheit'))} hinterlegten Stufen sind "
            "eine <i>Obergrenze für den Systemvorschlag</i> und keine "
            "rechnerische Zusicherung: Sie treten nur ein, wenn die "
            "Fachabteilung keinen eigenen Restwert einträgt. Welche Wirkung "
            "eine Maßnahme im Einzelfall tatsächlich hat, beurteilt die "
            "Fachabteilung und begründet es; die Anwendung beurteilt auch "
            "nicht, ob eine Maßnahme umgesetzt ist.</p>"
        )
    vote = record.get("dsb_votum")
    parts += [
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
    parts += [
        f"<tr><th>Beteiligung der oder des Datenschutzbeauftragten</th><td>"
        f"{_date(record.get('dsb_beteiligt_am'))}, Votum: "
        f"{escape(vote_text.get(vote or '', 'noch offen'))}</td></tr>",
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
            f"{_date(record.get('leitung_vorgelegt_am'))}</td></tr>"
        )
    if vote == "abgelehnt":
        parts.append(
            "<tr><th>Hinweis</th><td class='klein'>Die Abschätzung ist trotz "
            "ablehnender Stellungnahme freigegeben worden. Die oder der "
            "Datenschutzbeauftragte berät und entscheidet nicht (Art. 38 Abs. 3 "
            "DSGVO); die Verantwortung für die Verarbeitung trägt der "
            "Verantwortliche (Art. 24 DSGVO).</td></tr>"
        )
    releaser = record.get("freigeber")
    parts += [
        _row(
            "Erstellt",
            f"{escape(str(record.get('ersteller')))} am {_date(record.get('erstellt_am'))}",
        ),
        "<tr><th>Freigegeben</th><td>"
        + (
            f"{escape(str(releaser))} am {_date(record.get('freigegeben_am'))}"
            if releaser
            else "noch nicht freigegeben"
        )
        + "</td></tr>",
        "</table>",
        "<p class='klein'>Die Beteiligung der oder des Datenschutzbeauftragten beruht "
        f"auf {escape(n('dsb'))}. Freigegeben wird durch eine zweite Person; "
        "freigegebene Fassungen sind unveränderlich. Die Abschätzung ist zu "
        f"überprüfen, wenn sich das Risiko ändert ({escape(n('ueberpruefung'))}).</p>",
        "</body></html>",
    ]
    return "".join(parts)
