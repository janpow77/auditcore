"""``ted_contractor``: statistics, red flags and legitimacy over one contractor's contracts.

The contracts are ``auditcore_procurement`` ``notice/1`` records;
:func:`select_contracts` reproduces the source's SQL selection.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .base import JsonObject, seq_sum
from .errors import ProfileError
from .fraud_profile import FraudProfile, require_parameters
from .templates import check_template
from .values import is_missing


def select_contracts(
    notices: Iterable[JsonObject], name: str, vat_id: str | None
) -> list[JsonObject]:
    """Contracts of one contractor like the source SQL (not executed against Postgres).

    ``LOWER(TRIM(contractor_name)) = lower(strip(name))`` or equal
    ``contractor_vat_id`` when ``vat_id`` is given; ordered by award date,
    newest first, missing dates last (stable for ties).
    """
    wanted = name.lower().strip()
    chosen = []
    for notice in notices:
        contractor = notice.get("contractor_name")
        by_name = isinstance(contractor, str) and contractor.strip(" ").lower() == wanted
        by_vat = vat_id is not None and notice.get("contractor_vat_id") == vat_id
        if by_name or by_vat:
            chosen.append(notice)
    dated = [n for n in chosen if not is_missing(n.get("contract_award_date"))]
    undated = [n for n in chosen if is_missing(n.get("contract_award_date"))]
    dated.sort(key=lambda n: str(n["contract_award_date"]), reverse=True)
    return dated + undated


@dataclass(frozen=True)
class TedAssessment:
    """Statistics, red flags and legitimacy of one contractor (legacy structure)."""

    total_contracts: int
    statistics: JsonObject
    red_flags: tuple[JsonObject, ...]
    legitimacy_score: JsonObject
    profile: Mapping[str, str]


def _authorities_and_values(
    contracts: Sequence[JsonObject],
) -> tuple[list[str], list[float | None]]:
    authorities: list[str] = []
    values: list[float | None] = []
    for notice in contracts:
        authority = notice.get("contracting_authority_name")
        authorities.append(authority if isinstance(authority, str) and authority else "")
        raw = notice.get("contract_value")
        values.append(float(raw) if not is_missing(raw) and raw else None)
    return authorities, values


def _statistics(contracts: Sequence[JsonObject], p: JsonObject) -> dict[str, Any]:
    """Legacy contract statistics (all periods count every given contract, as the source)."""
    authorities, values = _authorities_and_values(contracts)
    n = len(contracts)
    if not n:
        return dict(p["empty_statistics"])
    total_value = seq_sum(v or 0 for v in values)
    counts: dict[str, int] = {}
    for authority in authorities:
        counts[authority] = counts.get(authority, 0) + 1
    top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[: int(p["top_n"])]
    top1 = top[0][1] if top else 0
    return {
        "total_value_eur": total_value,
        "avg_value_eur": total_value / n,
        "contract_count_12m": n,
        "contract_count_24m": n,
        "contract_count_60m": n,
        "top_authorities": [{"name": a, "contract_count": c} for a, c in top],
        "authority_count": len(counts),
        "concentration_ratio": top1 / n,
    }


def _metrics(stats: JsonObject, p: JsonObject) -> dict[str, Any]:
    return {
        **stats,
        "contract_count": stats["contract_count_12m"],
        "concentration_percent": stats["concentration_ratio"] * 100,
        "top1_name": stats["top_authorities"][0]["name"]
        if stats["top_authorities"]
        else p["unknown_authority"],
        "authority_count": stats.get("authority_count", 0),
    }


def _red_flags(metrics: JsonObject, p: JsonObject) -> list[dict[str, Any]]:
    flags = []
    for rule in p["flags"]:
        if all(_holds(metrics[c["metric"]], c["op"], c["value"]) for c in rule["when"]):
            flags.append(
                {
                    "severity": rule["severity"],
                    "flag_type": rule["flag_type"],
                    "description": rule["description"].format(**metrics),
                    "evidence": {key: metrics[metric] for key, metric in rule["evidence"].items()},
                }
            )
    return flags


def _legitimacy(
    n: int, stats: JsonObject, flags: list[dict[str, Any]], legit: JsonObject
) -> dict[str, object]:
    """Legacy legitimacy score, clamped, rated and optionally as a fraction."""
    score: float = float(legit["start"])
    if n:
        count = min(stats["contract_count_60m"], legit["count_cap"])
        score += min(count / legit["count_divisor"], legit["count_max_points"])
        score += (
            legit["distribution_points"]
            - stats["concentration_ratio"] * legit["concentration_factor"]
        )
    for flag in flags:
        score -= legit["severity_penalties"].get(flag["severity"], 0)
    score = max(legit["clamp"][0], min(legit["clamp"][1], score))
    rating = next(
        (r["rating"] for r in legit["ratings"] if score >= r["min"]), legit["default_rating"]
    )
    if legit.get("unit") == "fraction":
        score = score / 100
    return {
        "score": round(score, int(legit["digits"])),
        "rating": rating,
        "factors": {
            "contract_count": n,
            "concentration": stats.get("concentration_ratio", 0),
            "red_flag_count": len(flags),
        },
    }


def assess_contractor(contracts: Sequence[JsonObject], profile: FraudProfile) -> TedAssessment:
    """Legacy TED statistics, red flags and legitimacy over ``notice/1`` records."""
    p = require_parameters(profile, "ted_contractor")
    n = len(contracts)
    stats = _statistics(contracts, p)
    flags = _red_flags(_metrics(stats, p), p)
    legitimacy = _legitimacy(n, stats, flags, p["legitimacy"])
    return TedAssessment(
        total_contracts=n,
        statistics=MappingProxyType(stats),
        red_flags=tuple(MappingProxyType(f) for f in flags),
        legitimacy_score=MappingProxyType(legitimacy),
        profile=MappingProxyType(profile.reference),
    )


def _holds(left: float, op: str, right: float) -> bool:
    outcome = {"gt": left > right, "ge": left >= right, "lt": left < right, "le": left <= right}
    return bool(outcome[op])


def validate_ted(p: JsonObject) -> None:
    """Parameter contract of a ``ted_contractor`` profile."""
    need = {"top_n", "empty_statistics", "unknown_authority", "flags", "legitimacy"}
    if p.get("legitimacy", {}).get("unit", "percent") not in ("percent", "fraction"):
        raise ProfileError("legitimacy.unit muss percent/fraction sein.")
    if set(p) != need:
        raise ProfileError(f"ted_contractor braucht {sorted(need)}.")
    metrics = {
        "contract_count",
        "concentration_ratio",
        "authority_count",
        "contract_count_12m",
        "concentration_percent",
    }
    for rule in p["flags"]:
        check_template(rule["description"], "ted_contractor")
        for cond in rule["when"]:
            if cond["metric"] not in metrics or cond["op"] not in ("gt", "ge", "lt", "le"):
                raise ProfileError(f"Unzulässige Bedingung {cond!r}.")
