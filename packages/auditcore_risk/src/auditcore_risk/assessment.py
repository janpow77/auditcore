"""Profile-local legacy aggregation of one record: message texts, points and weights.

Each function reproduces the aggregation of exactly one profile; nothing here
combines profiles into a common score.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .base import JsonObject, seq_sum
from .errors import ProfileError
from .profiles import RiskProfile, Rule
from .results import FlagHit


def render_messages(
    rule: Rule, variant: str | None, values: Mapping[str, object]
) -> dict[str, str] | None:
    """Message parts of ``variant`` (``default`` if none) filled with ``values``."""
    if rule.messages is None:
        return None
    templates = rule.messages.get(variant or "default")
    if templates is None:
        raise ProfileError(f"Regel {rule.code}: keine Texte für Variante {variant!r}.")
    try:
        return {part: str(template).format(**values) for part, template in templates.items()}
    except (KeyError, ValueError, TypeError) as exc:
        raise ProfileError(f"Regel {rule.code}: Textvorlage passt nicht ({exc!r}).") from exc


def _spec(profile: RiskProfile) -> JsonObject:
    spec = profile.assessment
    if spec is None:
        raise ProfileError(f"Profil {profile.id} enthält keine Bewertung.")
    return spec


def points_assessment(
    profile: RiskProfile, flags: Mapping[str, bool | None], points: Mapping[str, float]
) -> dict[str, object]:
    """Legacy point score of *this* profile: sum of the points of true criteria."""
    spec = _spec(profile)
    score: float = 0
    detail = []
    for rule in profile.rules:
        if flags.get(rule.code):
            score = score + points[rule.code]
            if spec["detail_template"] is not None and points[rule.code] > 0:
                detail.append(
                    str(spec["detail_template"]).format(
                        label=rule.label, points=points[rule.code], code=rule.code
                    )
                )
    if spec["cap"] is not None:
        score = min(score, spec["cap"])
    stage = next((s["stage"] for s in spec["stages"] if score >= s["min"]), spec["default_stage"])
    return {
        "score": score,
        "stage": stage,
        "criteria": {code: bool(value) for code, value in flags.items()},
        "detail": detail,
        "points": dict(points),
        "source_version": spec["source_version"],
        "kind": spec["kind"],
    }


def _highest_severity(spec: JsonObject, hits: Sequence[FlagHit]) -> str | None:
    return next(
        (level for level in spec["severity_order"] if any(h.severity == level for h in hits)),
        None,
    )


def _summary_text(spec: JsonObject, hits: Sequence[FlagHit], highest: str | None) -> str:
    text = spec["summary"]
    if not hits:
        return str(text["none"])
    word = (
        text["level_words"].get(highest, text["unknown_level"])
        if highest
        else text["unknown_level"]
    )
    key = "one" if len(hits) == 1 else "many"
    return str(text[key]).format(count=len(hits), level=word)


def weighted_assessment(profile: RiskProfile, hits: Sequence[FlagHit]) -> dict[str, object]:
    """Legacy score of *this* profile: sum of severity weights in rule order."""
    spec = _spec(profile)
    weights = spec["weights"]
    total = seq_sum(float(weights.get(h.severity, spec["fallback_weight"])) for h in hits)
    score = min(total / float(spec["divisor"]), float(spec["cap"])) if hits else 0.0
    highest = _highest_severity(spec, hits)
    return {
        "score": score,
        "highest_severity": highest,
        "summary": _summary_text(spec, hits, highest),
        "findings": [
            {"code": h.code, "severity": h.severity, **(dict(h.messages) if h.messages else {})}
            for h in hits
        ],
        "source_version": spec["source_version"],
        "kind": spec["kind"],
    }


def record_assessment(
    profile: RiskProfile,
    flags: Mapping[str, bool | None],
    hits: Sequence[FlagHit],
    points: Mapping[str, float],
) -> dict[str, object] | None:
    """The profile's own assessment of one record (``None`` if it defines none)."""
    if profile.assessment is None:
        return None
    if profile.assessment["kind"] == "points_stages":
        return points_assessment(profile, flags, points)
    return weighted_assessment(profile, hits)


def points_for(profile: RiskProfile, override: Mapping[str, float] | None) -> dict[str, float]:
    """Criterion points: the profile's own or, where the profile allows it, the consumer's."""
    spec = profile.assessment
    if spec is None or spec["kind"] != "points_stages":
        if override is not None:
            raise ProfileError(f"Profil {profile.id} vergibt keine Punkte.")
        return {}
    if override is None:
        return {r.code: r.points if r.points is not None else 0 for r in profile.rules}
    if spec["points_override"] != "allowed":
        raise ProfileError(f"Profil {profile.id} erlaubt keine übergebenen Punkte.")
    codes = {r.code for r in profile.rules}
    if set(override) != codes:
        raise ProfileError(f"Punkte für genau {sorted(codes)} sind anzugeben.")
    for value in override.values():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ProfileError("Punkte müssen Zahlen sein.")
    return dict(override)
