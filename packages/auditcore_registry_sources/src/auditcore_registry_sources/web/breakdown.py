"""Transparent score breakdown and comparison data of a hit.

The breakdown retraces how the library arrived at the score: comparison
forms from ``auditcore_entity_matching``, the base similarity, every
adjustment with its reason, clamping, and the score classes of the profile.
It is recomputed from the hit and the profile and cross-checked against the
library's score; if both differ, ``consistent`` is ``False`` and the
reviewer sees that the explanation is incomplete instead of a wrong one.
"""

from __future__ import annotations

from auditcore_entity_matching import Profile as NormalizationProfile
from auditcore_entity_matching import normalize

from ..bulk_screening import BulkHit, pep_score
from ..profiles import RegistryProfile
from ..screening import EntryLike, ScreeningHit, ScreeningSettings
from ._types import Breakdown, BreakdownStep, EntryView, ScoreClass

CLASS_LABELS = {
    "exact": "exakt",
    "high": "hoch",
    "medium": "mittel",
    "low": "niedrig",
    "fuzzy": "unscharf",
}
MAX_ALIASES = 50


def _field(entry: EntryLike, name: str) -> str:
    value = getattr(entry, name, "")
    return value if isinstance(value, str) else ""


def entry_view(entry: EntryLike) -> EntryView:
    """All list fields of an entry, as the list spells them."""
    return {
        "entry_id": entry.entry_id,
        "schema": entry.schema,
        "name": entry.name,
        "aliases": list(entry.aliases)[:MAX_ALIASES],
        "aliases_total": len(entry.aliases),
        "birth_date": entry.birth_date,
        "countries": entry.countries,
        "addresses": _field(entry, "addresses"),
        "identifiers": _field(entry, "identifiers"),
        "sanctions": _field(entry, "sanctions"),
        "program_ids": _field(entry, "program_ids"),
        "first_seen": _field(entry, "first_seen"),
        "last_seen": _field(entry, "last_seen"),
        "dataset": _field(entry, "dataset"),
    }


def _step(
    step: str,
    label: str,
    *,
    value: str | None = None,
    detail: str | None = None,
    points: float | None = None,
    kind: str | None = None,
) -> BreakdownStep:
    item: BreakdownStep = {"step": step, "label": label}
    if value is not None:
        item["value"] = value
    if detail is not None:
        item["detail"] = detail
    if points is not None:
        item["points"] = points
    if kind is not None:
        item["kind"] = kind
    return item


def _norm_ref(profile: NormalizationProfile) -> str:
    return f"{profile.id} {profile.version}"


def _classes(normalization: NormalizationProfile) -> list[ScoreClass]:
    rules = normalization.classification
    if rules is None:
        return []
    return [
        {"class": "exact", "label": CLASS_LABELS["exact"], "from": rules.exact_from},
        {"class": "high", "label": CLASS_LABELS["high"], "from": rules.high_from},
        {"class": "medium", "label": CLASS_LABELS["medium"], "from": rules.medium_from},
    ]


def sanctions_breakdown(
    hit: ScreeningHit, settings: ScreeningSettings, *, normalized_query: str, min_score: float
) -> Breakdown:
    """Steps from the name comparison to the adjusted score (scale 0–100)."""
    field_label = "Hauptname" if hit.matched_field == "name" else "Alias"
    steps = [
        _step(
            "normalization",
            "Vergleichsform der Eingabe",
            value=normalized_query,
            detail=f"Normalisierungsprofil {_norm_ref(settings.normalization)}",
        ),
        _step(
            "normalization",
            f"Vergleichsform der getroffenen Schreibweise ({field_label})",
            value=hit.matched_form,
            detail=hit.matched_name,
        ),
        _step(
            "base",
            "Namensähnlichkeit (Token-Set-Vergleich, beste Form über Name und Aliasse)",
            points=hit.raw_score,
        ),
    ]
    total = hit.raw_score
    for adjustment in hit.adjustments:
        total += adjustment.points
        steps.append(
            _step("adjustment", adjustment.reason, kind=adjustment.kind, points=adjustment.points)
        )
    low, high = settings.score_range
    clamped = max(low, min(high, total))
    if clamped != total:
        steps.append(
            _step(
                "clamp",
                f"Auf den Wertebereich {low:g}–{high:g} begrenzt",
                points=round(clamped - total, 1),
            )
        )
    steps.append(_step("result", "Ergebniswert", points=hit.score))
    return {
        "method": "rapidfuzz_token_set",
        "scale": {"min": low, "max": high},
        "steps": steps,
        "min_score": min_score,
        "classes": _classes(settings.normalization),
        "class": hit.confidence,
        "class_label": CLASS_LABELS.get(hit.confidence, hit.confidence),
        "consistent": round(clamped, 1) == hit.score,
    }


def _token_steps(
    query_form: str, form: str, profile: RegistryProfile, country: str | None, countries: str
) -> tuple[list[BreakdownStep], float]:
    query_tokens, tokens = set(query_form.split()), set(form.split())
    common = query_tokens & tokens
    if not common:
        return [_step("base", "Kein gemeinsamer Namensbestandteil", points=0.0)], 0.0
    q_cov, c_cov = len(common) / len(query_tokens), len(common) / len(tokens)
    token_f1 = 2 * (q_cov * c_cov) / (q_cov + c_cov)
    steps = [
        _step(
            "base",
            "Übereinstimmung der Namensbestandteile (Token-F1)",
            points=round(token_f1, 4),
            detail=(
                f"{len(common)} von {len(query_tokens)} Bestandteilen der Eingabe, "
                f"{len(common)} von {len(tokens)} des Eintrags"
            ),
        )
    ]
    total = token_f1
    if query_form in form or form in query_form:
        bonus = float(profile.setting("substring_bonus"))
        total += bonus
        steps.append(_step("adjustment", "Eine Vergleichsform enthält die andere", points=bonus))
    if country and countries and country.lower() in countries.lower():
        bonus = float(profile.setting("country_bonus"))
        total += bonus
        steps.append(_step("adjustment", "Land im Eintrag genannt", points=bonus))
    if total > 1.0:
        steps.append(_step("clamp", "Auf höchstens 1 begrenzt", points=round(1.0 - total, 4)))
    return steps, min(1.0, total)


def pep_breakdown(
    hit: BulkHit,
    profile: RegistryProfile,
    normalization: NormalizationProfile,
    *,
    query: str,
    country: str | None,
    min_score: float,
) -> Breakdown:
    """Steps of the token matching of the PEP variant (scale 0–1)."""
    query_form = normalize(query, normalization)
    form = normalize(hit.matched_name, normalization)
    steps = [
        _step(
            "normalization",
            "Vergleichsform der Eingabe",
            value=query_form,
            detail=f"Normalisierungsprofil {_norm_ref(normalization)}",
        ),
        _step(
            "normalization",
            "Vergleichsform der getroffenen Schreibweise"
            + (" (Alias)" if hit.via_alias else " (Hauptname)"),
            value=form,
            detail=hit.matched_name,
        ),
    ]
    if query_form and query_form == form:
        steps.append(_step("base", "Vergleichsformen identisch", points=1.0))
        total = 1.0
    else:
        token_steps, total = _token_steps(query_form, form, profile, country, hit.entry.countries)
        steps.extend(token_steps)
    digits = int(profile.setting("score_digits"))
    steps.append(_step("result", "Ergebniswert", points=hit.score))
    library = pep_score(
        query_form, form, profile, country=country, entry_countries=hit.entry.countries
    )
    exact_from = float(profile.setting("exact_from"))
    return {
        "method": "token_f1",
        "scale": {"min": 0.0, "max": 1.0},
        "steps": steps,
        "min_score": min_score,
        "classes": [{"class": "exact", "label": CLASS_LABELS["exact"], "from": exact_from}],
        "class": hit.method,
        "class_label": CLASS_LABELS.get(hit.method, hit.method),
        "consistent": round(total, digits) == hit.score == round(library, digits),
    }
