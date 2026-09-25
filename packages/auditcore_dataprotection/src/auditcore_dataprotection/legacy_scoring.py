"""Legacy-exact screening, risk, proposal and prefill of ``regulierung@a5d48ea``.

Reproduces ``backend/app/services/dsfa/bewertung.py`` including the behavior
this library corrects in its own contract: unknown questions are skipped,
truthy values count as "yes", empty surveys yield ``nur_schwellwert`` and
explicit residual values are not range-checked.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import cache
from typing import Any

from .rules import (
    EFFECT_FRIA,
    EFFECT_HARD,
    EFFECT_POINT,
    RECOMMENDATION_CONSULTATION,
    RECOMMENDATION_RELEASE,
    RECOMMENDATION_RELEASE_WITH_CONDITIONS,
    RECOMMENDATION_SCREENING_ONLY,
    Measure,
    Question,
    RuleProfile,
    load_profile,
)
from .screening import SCREENING_NOT_REQUIRED, SCREENING_REQUIRED

LEGACY_PROFILE_VERSION = "2026.09.1"
REGIME_DSGVO = "dsgvo"
REGIME_JI = "hdsig_ji"
#: Screening outcomes of the source; the same values as in :mod:`.screening`.
LEGACY_SCREENING_REQUIRED = SCREENING_REQUIRED
LEGACY_SCREENING_NOT_REQUIRED = SCREENING_NOT_REQUIRED

_FRIA_REASONING = (
    " Zusätzlich handelt es sich um ein Hochrisiko-KI-System; die "
    "Grundrechte-Folgenabschätzung nach Art. 27 der Verordnung (EU) "
    "2024/1689 ist zu erstellen und darf mit dieser Abschätzung "
    "verbunden werden (Art. 27 Abs. 4)."
)


@cache
def legacy_profile(regime: str) -> RuleProfile:
    """Packaged source profile; unknown regimes fall back to DSGVO like the source."""
    key = "regulierung.hdsig_ji" if regime == REGIME_JI else "regulierung.dsgvo"
    return load_profile(key, LEGACY_PROFILE_VERSION)


def _questions() -> dict[str, Question]:
    return {q.key: q for q in legacy_profile(REGIME_DSGVO).questions}


def _measures() -> dict[str, Measure]:
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
    """Field-compatible with ``bewertung.Antwort``; ``ja`` is evaluated by truthiness."""

    schluessel: str
    ja: object
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


def _legacy_hard_reasoning(hard: Sequence[str], regime: str) -> str:
    references = "; ".join(legacy_reference(s, regime) for s in hard)
    if regime == REGIME_JI:
        return (
            f"Die Datenschutz-Folgenabschätzung ist durchzuführen "
            f"({legacy_norm(regime, 'pflicht')}). Erfüllt ist: {references}. "
            "Der Dritte Teil des HDSIG kennt die Regelbeispiele des Art. 35 "
            "Abs. 3 DSGVO und die Liste nach Abs. 4 nicht; sie werden hier "
            "als strengerer Maßstab angewandt, weil die Abgrenzung beider "
            "Rechtsakte auf europäischer Ebene nicht geklärt ist."
        )
    if len(hard) == 1:
        return (
            f"Die Datenschutz-Folgenabschätzung ist durchzuführen, weil "
            f"{len(hard)} Muss-Kriterium bejaht wurde: {references}."
        )
    return (
        f"Die Datenschutz-Folgenabschätzung ist durchzuführen, weil "
        f"{len(hard)} Muss-Kriterien bejaht wurden: {references}."
    )


def _legacy_outcome(hard: Sequence[str], score: int, regime: str) -> tuple[str, str]:
    """Outcome and reasoning; without hard triggers only the point threshold decides."""
    threshold = legacy_profile(REGIME_DSGVO).points_threshold
    if hard:
        return LEGACY_SCREENING_REQUIRED, _legacy_hard_reasoning(hard, regime)
    if score >= threshold:
        return LEGACY_SCREENING_REQUIRED, (
            f"Es sind {score} der neun Kriterien des Europäischen "
            f"Datenschutzausschusses erfüllt. Ab {threshold} Kriterien ist "
            "regelmäßig von einem voraussichtlich hohen Risiko auszugehen "
            "(WP 248 rev.01); die Folgenabschätzung ist durchzuführen."
        )
    return LEGACY_SCREENING_NOT_REQUIRED, (
        f"Kein Muss-Kriterium ist erfüllt und es sind {score} der neun "
        f"Kriterien des Europäischen Datenschutzausschusses bejaht, also "
        f"weniger als {threshold}. Eine Folgenabschätzung ist damit "
        "nicht erforderlich; das Ergebnis ist gleichwohl zu dokumentieren "
        f"({legacy_norm(regime, 'nachweis')})."
    )


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
    result, reasoning = _legacy_outcome(hard, len(points), regime)
    if fria:
        reasoning += _FRIA_REASONING
    return LegacyThreshold(
        ergebnis=result,
        regime=regime,
        punkte=len(points),
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


def _legacy_scenario_row(scenario: LegacyScenario) -> dict[str, Any]:
    severity, likelihood, titles = _legacy_net(scenario)
    net = severity * likelihood
    return {
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


def legacy_risk(scenarios: Sequence[LegacyScenario]) -> dict[str, Any]:
    """``asdict(bewertung.werte_risiko_aus(...))``."""
    rows = [_legacy_scenario_row(scenario) for scenario in scenarios]
    gross_max = max([0, *(scenario.brutto for scenario in scenarios)])
    net_max = max([0, *(row["netto"] for row in rows)])
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


def _legacy_recommendation(net_maximum: int) -> str:
    if net_maximum >= 10:
        return RECOMMENDATION_CONSULTATION
    if net_maximum >= 5:
        return RECOMMENDATION_RELEASE_WITH_CONDITIONS
    return RECOMMENDATION_RELEASE


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

    if threshold.ergebnis == LEGACY_SCREENING_NOT_REQUIRED:
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
    recommendation = _legacy_recommendation(risk["netto_hoechstwert"])
    reasoning = (
        f"{threshold.begruendung} Das höchste Risiko vor Maßnahmen beträgt "
        f"{risk['brutto_hoechstwert']} von 16, nach den vorgesehenen Maßnahmen "
        f"{risk['netto_hoechstwert']} von 16 und ist damit als "
        f"{risk['stufe']} einzustufen."
    )
    return result(
        risk, recommendation, legacy_recommendation_text(recommendation, regime), reasoning
    )


def _legacy_count(persons: object) -> int:
    """``int(value)`` of the source; empty or unusable values count as 0."""
    try:
        return int(persons) if persons not in (None, "") else 0  # type: ignore[call-overload]
    except (TypeError, ValueError):
        return 0


def legacy_prefill(activity: Mapping[str, object]) -> dict[str, dict[str, Any]]:
    """``bewertung.vorbelegung_aus_taetigkeit`` (bool conversion, locale ``n`` format)."""
    threshold = legacy_profile(REGIME_DSGVO).large_scale_threshold
    special = bool(activity.get("besondere_kategorien"))
    criminal = bool(activity.get("daten_art10"))
    count = _legacy_count(activity.get("anzahl_betroffene"))
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
