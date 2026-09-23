"""Fraud-check mechanics of flowinvoice ``fraud_detection`` as profile-driven functions.

Three separate, versioned legacy profiles (schema ``auditcore_risk.fraud-profile/1``):

* ``signal_score`` — blockers, warnings, score and level from the results of the
  sub-checks (duplicates, sanctions, PEP, company, TED). Sanctions, PEP and
  company results are *consumed* as plain mappings (port contract); the
  screening itself belongs to the registry/screening libraries.
* ``ted_contractor`` — statistics, red flags and legitimacy score over the
  public contracts of one contractor, given as ``auditcore_procurement``
  ``notice/1`` records; :func:`select_contracts` reproduces the SQL selection.
* ``duplicates`` — exact and fuzzy invoice duplicates among candidate documents
  the application has already pre-selected (its SQL window/limit stay there).

Every weight, threshold, text and format comes from the profile; the results
are this profile's legacy values only, never a combined score across profiles.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from importlib import resources
from types import MappingProxyType
from typing import Any

from .base import seq_sum
from .errors import InputError, ProfileError
from .profiles import check_template, fingerprint
from .values import is_missing

SCHEMA = "auditcore_risk.fraud-profile/1"
FRAUD_KINDS = ("signal_score", "ted_contractor", "duplicates")
_TOP = frozenset(
    {
        "schema",
        "id",
        "version",
        "kind",
        "status",
        "legal_status",
        "source",
        "open_decisions",
        "parameters",
    }
)


@dataclass(frozen=True)
class FraudProfile:
    """Immutable fraud-check profile (one mechanic, one source variant)."""

    id: str
    version: str
    kind: str
    status: str
    legal_status: str
    source: Mapping[str, Any]
    parameters: Mapping[str, Any]
    open_decisions: tuple[str, ...]
    fingerprint: str

    @property
    def reference(self) -> dict[str, str]:
        """Identity recorded with every result."""
        return {
            "id": self.id,
            "version": self.version,
            "fingerprint": self.fingerprint,
            "status": self.status,
        }


def fraud_profile_from_dict(data: Mapping[str, Any]) -> FraudProfile:
    """Validate a fraud-check profile document."""
    if not isinstance(data, Mapping) or data.get("schema") != SCHEMA:
        raise ProfileError("Unbekanntes Schema für Betrugsprüfprofile.")
    unknown = set(data) - _TOP
    if unknown:
        raise ProfileError(f"Profil: unbekannte Felder {sorted(unknown)}.")
    if data.get("kind") not in FRAUD_KINDS:
        raise ProfileError(f"Unbekannte Profilart {data.get('kind')!r}.")
    for key in ("id", "version", "status", "legal_status"):
        if not isinstance(data.get(key), str) or not data[key]:
            raise ProfileError(f"Profil: {key!r} fehlt.")
    if not isinstance(data.get("source"), dict) or not isinstance(data.get("parameters"), dict):
        raise ProfileError("Profil: 'source' und 'parameters' sind Pflicht.")
    _VALIDATORS[data["kind"]](data["parameters"])
    return FraudProfile(
        id=data["id"],
        version=data["version"],
        kind=data["kind"],
        status=data["status"],
        legal_status=data["legal_status"],
        source=MappingProxyType(dict(data["source"])),
        parameters=MappingProxyType(json.loads(json.dumps(data["parameters"]))),
        open_decisions=tuple(data.get("open_decisions", [])),
        fingerprint=fingerprint(data),
    )


def _packaged() -> dict[tuple[str, str], Any]:
    found = {}
    for entry in resources.files("auditcore_risk.fraud_profiles").iterdir():
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            found[(str(data["id"]), str(data["version"]))] = entry
    return found


def available_fraud_profiles() -> tuple[tuple[str, str], ...]:
    """Packaged ``(id, version)`` pairs of fraud-check profiles."""
    return tuple(sorted(_packaged()))


def load_fraud_profile(profile_id: str, version: str, kind: str | None = None) -> FraudProfile:
    """Load an explicitly named packaged fraud-check profile (optionally of one kind)."""
    entry = _packaged().get((profile_id, version))
    if entry is None:
        raise ProfileError(f"Profil {profile_id} in Version {version} ist nicht vorhanden.")
    profile = fraud_profile_from_dict(json.loads(entry.read_text(encoding="utf-8")))
    if kind is not None and profile.kind != kind:
        raise ProfileError(f"Profil {profile_id} ist kein {kind}-Profil.")
    return profile


def _require(profile: FraudProfile, kind: str) -> Mapping[str, Any]:
    if not isinstance(profile, FraudProfile) or profile.kind != kind:
        raise ProfileError(f"Ein ausdrücklich geladenes {kind}-Profil ist erforderlich.")
    return profile.parameters


def _number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float | Decimal):
        raise InputError(f"{where}: Zahl erwartet, erhalten {type(value).__name__}.")
    return float(value)


# --------------------------------------------------------------------------- signals


@dataclass(frozen=True)
class SignalAssessment:
    """Blockers, warnings, score components, score and level of one invoice."""

    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    checks_performed: tuple[str, ...]
    components: tuple[Mapping[str, Any], ...]
    raw_score: float
    score: float
    level: str
    profile: Mapping[str, str]


def score_signals(signals: Mapping[str, Any], profile: FraudProfile) -> SignalAssessment:
    """Legacy blocker/warning derivation and score of the fraud-check manager.

    ``signals`` maps each check name to ``None`` (check switched off),
    ``{"failed": True}`` (check raised) or its result mapping, for example
    ``{"is_sanctioned": True, "error_message": None, "matches": [{"match_score": 0.9}]}``.
    Warnings keep their derivation order and are de-duplicated deterministically.
    """
    p = _require(profile, "signal_score")
    derive = p["derivation"]
    blockers: list[str] = []
    warnings: list[str] = []
    performed: list[str] = []
    results: dict[str, Mapping[str, Any]] = {}
    for check in p["order"]:
        value = signals.get(check)
        if value is None:
            continue
        rules = derive[check]
        if not isinstance(value, Mapping):
            raise InputError(f"Signal {check!r} muss eine Zuordnung oder None sein.")
        if value.get("failed"):
            warnings.append(rules["failed_warning"])
            continue
        performed.append(rules["performed"])
        results[check] = value
        if check == "duplicate":
            if value["is_duplicate"]:
                if any(m["match_type"] == "exact" for m in value["matches"]):
                    blockers.append(rules["exact_blocker"])
                else:
                    warnings.append(rules["fuzzy_warning"])
        elif check == "sanctions":
            if value["is_sanctioned"]:
                blockers.append(rules["hit_blocker"])
            elif value.get("error_message"):
                warnings.append(rules["error_warning"])
        elif check == "pep":
            if not value["is_clean"]:
                warnings.append(rules["hit_warning"])
            elif value.get("error_message"):
                warnings.append(rules["error_warning"])
        elif check == "company":
            for indicator in value["risk_indicators"]:
                if indicator in rules["blocker_indicators"]:
                    blockers.append(indicator)
                elif indicator not in rules["ignored_indicators"]:
                    warnings.append(indicator)
        elif check == "ted":
            for flag in value.get("red_flags", []):
                if flag.get("severity", rules["default_severity"]) in rules["warning_severities"]:
                    warnings.append(
                        rules["warning_prefix"] + str(flag.get("flag_type", rules["unknown_type"]))
                    )
    w = p["score"]
    components: list[dict[str, Any]] = []
    score = 0.0

    def add(name: str, value: float, detail: Mapping[str, Any]) -> None:
        """Add one score component in the source's order and record it."""
        nonlocal score
        score += value
        components.append({"component": name, "contribution": value, **detail})

    add("blockers", len(blockers) * w["per_blocker"], {"count": len(blockers)})
    add("warnings", len(warnings) * w["per_warning"], {"count": len(warnings)})
    if "company" in results:
        verification = _number(results["company"]["verification_score"], "company")
        add(
            "company",
            (1.0 - verification) * w["company_weight"],
            {"verification_score": verification},
        )
    dup = results.get("duplicate")
    if dup and dup["is_duplicate"]:
        top = max((_number(m["confidence"], "duplicate") for m in dup["matches"]), default=0)
        add("duplicate", top * w["duplicate_weight"], {"max_confidence": top})
    sanctions = results.get("sanctions")
    if sanctions and sanctions["is_sanctioned"]:
        top = max((_number(m["match_score"], "sanctions") for m in sanctions["matches"]), default=0)
        add("sanctions", top * w["sanctions_weight"], {"max_match_score": top})
    pep = results.get("pep")
    if pep and not pep["is_clean"]:
        top = max((_number(m["match_score"], "pep") for m in pep["matches"]), default=0)
        add("pep", top * w["pep_weight"], {"max_match_score": top})
    ted = results.get("ted")
    if ted and len(ted.get("red_flags", [])) > 0:
        legitimacy = ted.get("legitimacy_score", 1.0)
        if not isinstance(legitimacy, int | float) or isinstance(legitimacy, bool):
            raise InputError(
                "TED-Legitimität muss eine Zahl zwischen 0 und 1 sein; die Quelle liefert ein "
                "Wörterbuch (0–100) und bricht an dieser Stelle ab (siehe RK-C09)."
            )
        add("ted", (1.0 - legitimacy) * w["ted_weight"], {"legitimacy_score": legitimacy})
    raw = min(float(w["cap"]), score)
    levels = p["levels"]
    if blockers:
        level = levels["blocker_level"]
    else:
        level = next(
            (t["level"] for t in levels["thresholds"] if raw >= t["min"]), levels["default"]
        )
    return SignalAssessment(
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
        checks_performed=tuple(performed),
        components=tuple(MappingProxyType(c) for c in components),
        raw_score=raw,
        score=round(raw, int(w["output_digits"])),
        level=level,
        profile=MappingProxyType(profile.reference),
    )


def _validate_signal(p: Mapping[str, Any]) -> None:
    need = {"order", "derivation", "score", "levels"}
    if set(p) != need:
        raise ProfileError(f"signal_score braucht {sorted(need)}.")
    if sorted(p["order"]) != sorted(p["derivation"]) or len(set(p["order"])) != len(p["order"]):
        raise ProfileError("Reihenfolge und Ableitungsregeln müssen übereinstimmen.")
    known = {"duplicate", "sanctions", "pep", "company", "ted"}
    if not set(p["order"]) <= known:
        raise ProfileError(f"Unbekannte Teilprüfung in {p['order']}.")
    for key, value in p["score"].items():
        if key != "output_digits" and not isinstance(value, int | float):
            raise ProfileError(f"Gewicht {key} muss eine Zahl sein.")
    thresholds = [t["min"] for t in p["levels"]["thresholds"]]
    if thresholds != sorted(thresholds, reverse=True):
        raise ProfileError("Stufen müssen absteigend geordnet sein.")


# --------------------------------------------------------------------------- TED


def select_contracts(
    notices: Iterable[Mapping[str, Any]], name: str, vat_id: str | None
) -> list[Mapping[str, Any]]:
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
    statistics: Mapping[str, Any]
    red_flags: tuple[Mapping[str, Any], ...]
    legitimacy_score: Mapping[str, Any]
    profile: Mapping[str, str]


def assess_contractor(
    contracts: Sequence[Mapping[str, Any]], profile: FraudProfile
) -> TedAssessment:
    """Legacy TED statistics, red flags and legitimacy over ``notice/1`` records."""
    p = _require(profile, "ted_contractor")
    authorities: list[str] = []
    values: list[float | None] = []
    for notice in contracts:
        authority = notice.get("contracting_authority_name")
        authorities.append(authority if isinstance(authority, str) and authority else "")
        raw = notice.get("contract_value")
        values.append(float(raw) if not is_missing(raw) and raw else None)
    n = len(contracts)
    stats: dict[str, Any]
    if not n:
        stats = dict(p["empty_statistics"])
    else:
        total_value: Any = seq_sum(v or 0 for v in values)
        counts: dict[str, int] = {}
        for authority in authorities:
            counts[authority] = counts.get(authority, 0) + 1
        top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[: int(p["top_n"])]
        top1 = top[0][1] if top else 0
        stats = {
            "total_value_eur": total_value,
            "avg_value_eur": total_value / n,
            "contract_count_12m": n,
            "contract_count_24m": n,
            "contract_count_60m": n,
            "top_authorities": [{"name": a, "contract_count": c} for a, c in top],
            "authority_count": len(counts),
            "concentration_ratio": top1 / n,
        }
    metrics = {
        **stats,
        "contract_count": stats["contract_count_12m"],
        "concentration_percent": stats["concentration_ratio"] * 100,
        "top1_name": stats["top_authorities"][0]["name"]
        if stats["top_authorities"]
        else p["unknown_authority"],
        "authority_count": stats.get("authority_count", 0),
    }
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
    legit = p["legitimacy"]
    score: Any = float(legit["start"])
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
    legitimacy = {
        "score": round(score, int(legit["digits"])),
        "rating": rating,
        "factors": {
            "contract_count": n,
            "concentration": stats.get("concentration_ratio", 0),
            "red_flag_count": len(flags),
        },
    }
    return TedAssessment(
        total_contracts=n,
        statistics=MappingProxyType(stats),
        red_flags=tuple(MappingProxyType(f) for f in flags),
        legitimacy_score=MappingProxyType(legitimacy),
        profile=MappingProxyType(profile.reference),
    )


def _holds(left: Any, op: str, right: float) -> bool:
    outcome = {"gt": left > right, "ge": left >= right, "lt": left < right, "le": left <= right}
    return bool(outcome[op])


def _validate_ted(p: Mapping[str, Any]) -> None:
    need = {"top_n", "empty_statistics", "unknown_authority", "flags", "legitimacy"}
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


# --------------------------------------------------------------------------- duplicates


@dataclass(frozen=True)
class DuplicateMatch:
    """One candidate document considered a duplicate."""

    candidate_id: Any
    match_type: str
    confidence: float
    details: Mapping[str, Any]


def _decimal(value: Any, where: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, int | float | str | Decimal):
        raise InputError(f"{where}: Betrag als Zahl oder Text erwartet.")
    try:
        return Decimal(str(value))
    except InvalidOperation as exc:
        raise InputError(f"{where}: kein Betrag {value!r}.") from exc


def exact_duplicates(
    invoice: Mapping[str, Any], candidates: Iterable[Mapping[str, Any]], profile: FraudProfile
) -> list[DuplicateMatch]:
    """Same invoice number (candidate side not trimmed) and amount difference below the limit."""
    p = _require(profile, "duplicates")["exact"]
    number = str(invoice["invoice_number"])
    wanted = number.strip().upper()
    total = _decimal(invoice["total_amount"], "total_amount")
    out = []
    for cand in candidates:
        cand_number = cand.get("invoice_number")
        if is_missing(cand_number) or str(cand_number).upper() != wanted:
            continue
        raw = cand.get("gross_amount")
        raw = p["missing_amount"] if raw is None else raw
        cleaned = str(raw)
        for old, new in p["amount_replacements"]:
            cleaned = cleaned.replace(old, new)
        try:
            amount = Decimal(cleaned)
        except InvalidOperation:
            amount = Decimal(p["invalid_amount"])
        if abs(amount - total) < Decimal(p["tolerance"]):
            out.append(
                DuplicateMatch(
                    cand.get("id"),
                    "exact",
                    float(p["confidence"]),
                    {
                        "invoice_number": number,
                        "amount": str(total),
                        "original_filename": cand.get("original_filename"),
                        "original_project_id": cand.get("project_id"),
                    },
                )
            )
    return out


def names_similar(first: str, second: str, min_containment: int, leading_words: int) -> bool:
    """Legacy name heuristic: equal, containment (≥ ``min_containment``) or a shared word
    among the first ``leading_words`` words (very permissive; see RK-L)."""
    if first == second:
        return True
    if len(first) >= min_containment and first in second:
        return True
    if len(second) >= min_containment and second in first:
        return True
    a, b = first.split()[:leading_words], second.split()[:leading_words]
    return bool(a and b and set(a) & set(b))


def parse_date(value: str, formats: Sequence[str]) -> date | None:
    """First matching format wins (European before US for ambiguous dates)."""
    if not value:
        return None
    text = value.strip()
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def fuzzy_duplicates(
    invoice: Mapping[str, Any], candidates: Iterable[Mapping[str, Any]], profile: FraudProfile
) -> list[DuplicateMatch]:
    """Amount within ±tolerance, date within ±days and similar supplier name."""
    p = _require(profile, "duplicates")["fuzzy"]
    amount = float(_decimal(invoice["total_amount"], "total_amount"))
    if amount == 0:
        raise InputError("Fuzzy-Abgleich mit Betrag 0 ist nicht definiert (Quelle: Division).")
    tolerance = float(p["amount_tolerance"])
    days = int(p["date_range_days"])
    low, high = amount * (1 - tolerance), amount * (1 + tolerance)
    day = invoice["invoice_date"]
    if isinstance(day, str):
        day = date.fromisoformat(day)
    if not isinstance(day, date):
        raise InputError("invoice_date muss ein Datum sein.")
    min_date, max_date = day - timedelta(days=days), day + timedelta(days=days)
    supplier = str(invoice["supplier_name"]).lower().strip()
    out = []
    for cand in candidates:
        raw = cand.get("gross_amount")
        cleaned = str(p["missing_amount"] if raw is None else raw)
        for old, new in p["amount_replacements"]:
            cleaned = cleaned.replace(old, new)
        try:
            cand_amount = float(cleaned)
        except ValueError:
            continue
        if not (low <= cand_amount <= high):
            continue
        cand_date_raw = cand.get("invoice_date")
        cand_date = parse_date(
            "" if cand_date_raw is None else str(cand_date_raw), p["date_formats"]
        )
        if cand_date is None or not (min_date <= cand_date <= max_date):
            continue
        cand_supplier = cand.get("supplier_name")
        cand_supplier = "" if cand_supplier is None else str(cand_supplier)
        if not names_similar(
            supplier, cand_supplier.lower(), int(p["min_containment"]), int(p["leading_words"])
        ):
            continue
        amount_diff = abs(cand_amount - amount) / amount
        date_diff = abs((cand_date - day).days) / days
        confidence = 1.0 - (amount_diff * p["amount_weight"] + date_diff * p["date_weight"])
        out.append(
            DuplicateMatch(
                cand.get("id"),
                "fuzzy",
                round(max(0.0, min(1.0, confidence)), int(p["digits"])),
                {
                    "supplier_name": cand_supplier[: int(p["name_chars"])],
                    "amount": f"{cand_amount:.2f}",
                    "date": str(cand_date),
                    "amount_diff_percent": f"{amount_diff * 100:.1f}%",
                    "original_filename": cand.get("original_filename"),
                    "original_project_id": cand.get("project_id"),
                },
            )
        )
    return out


def find_duplicates(
    invoice: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]], profile: FraudProfile
) -> list[DuplicateMatch]:
    """Exact matches first; fuzzy matches only if there is no exact match (as the source)."""
    exact = exact_duplicates(invoice, candidates, profile)
    return exact if exact else fuzzy_duplicates(invoice, candidates, profile)


def _validate_duplicates(p: Mapping[str, Any]) -> None:
    if set(p) != {"exact", "fuzzy"}:
        raise ProfileError("duplicates braucht 'exact' und 'fuzzy'.")
    fuzzy = p["fuzzy"]
    if not 0 <= float(fuzzy["amount_tolerance"]) < 1 or int(fuzzy["date_range_days"]) <= 0:
        raise ProfileError("Toleranz oder Zeitfenster ungültig.")
    if not math.isclose(float(fuzzy["amount_weight"]) + float(fuzzy["date_weight"]), 1.0):
        raise ProfileError("Gewichte der Konfidenz müssen 1 ergeben.")


_VALIDATORS = {
    "signal_score": _validate_signal,
    "ted_contractor": _validate_ted,
    "duplicates": _validate_duplicates,
}
