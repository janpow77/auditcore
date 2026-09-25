"""Result statuses and shared helpers of the procurement prechecks."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from .precheck_profile import PrecheckProfile, Tier

#: JSON row of one check (``check_id``, ``name_de``, ``status``, ``message``, extras, ``source``).
CheckResult = dict[str, Any]

PASS = "PASS"
WARNING = "WARNING"
FAIL = "FAIL"
NOT_APPLICABLE = "NOT_APPLICABLE"
NOT_CHECKED = "NOT_CHECKED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
MODES = ("legacy", "strict")


def category_of(profile: PrecheckProfile, service_type: str) -> str:
    return "construction" if profile.construction_marker in service_type else "supply_service"


def find_tier(profile: PrecheckProfile, category: str, name: str | None) -> Tier | None:
    for tier in profile.tiers.get(category, ()):
        if tier.name == name:
            return tier
    return None


def result(check_id: str, name: str, status: str, message: str, **extra: Any) -> CheckResult:
    return {
        "check_id": check_id,
        "name_de": name,
        "status": status,
        "message": message,
        **extra,
        "source": "RULE",
    }


def is_missing(value: Decimal | None, mode: str) -> bool:
    return value is None if mode == "strict" else not value
