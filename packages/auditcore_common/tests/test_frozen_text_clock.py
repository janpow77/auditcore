"""freeze/thaw, text, clock and ids against the package copies (differential)."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta, timezone

import legacy_reference as legacy
import pytest
from samples import SAMPLES, TEXTS, assert_same_outcome, random_json, random_value, rng

from auditcore_common.clock import require_aware, utc_now
from auditcore_common.frozen import freeze, thaw
from auditcore_common.ids import new_uuid
from auditcore_common.text import compact_upper, group_thousands_de


def test_freeze_and_thaw_match_documents() -> None:
    r = rng(21)
    for _ in range(SAMPLES):
        value = random_value(r) if r.random() < 0.5 else random_json(r)
        assert_same_outcome(lambda: legacy.documents_freeze(value), lambda: freeze(value))
        frozen = freeze(value)
        assert_same_outcome(lambda: legacy.documents_thaw(frozen), lambda: thaw(frozen))


def test_group_thousands_matches_dataprotection_and_registry() -> None:
    r = rng(22)
    values = [0, 1, -1, 999, 1000, -1000, 10**18, True] + [
        r.randint(-(10**15), 10**15) for _ in range(SAMPLES)
    ]
    for value in values:
        assert legacy.dataprotection_number(value) == group_thousands_de(value)
        assert legacy.registry_count(value) == group_thousands_de(value)


def test_compact_upper_matches_documents_and_invoicesynth() -> None:
    r = rng(23)
    for _ in range(SAMPLES):
        text = "".join(r.choice(TEXTS + (" ", "\t", " ", "de 12")) for _ in range(4))
        assert legacy.documents_compact(text) == compact_upper(text)
        assert legacy.invoicesynth_normalize_identifier(text) == compact_upper(text)


@pytest.mark.parametrize(
    "moment",
    [
        datetime(2026, 9, 25),
        datetime(2026, 9, 25, tzinfo=UTC),
        datetime(2026, 9, 25, tzinfo=timezone(timedelta(hours=-3))),
    ],
)
def test_require_aware_matches_harvest_and_property(moment: datetime) -> None:
    assert_same_outcome(lambda: legacy.property_aware(moment), lambda: require_aware(moment))
    assert_same_outcome(
        lambda: legacy.harvest_iso(moment), lambda: require_aware(moment).isoformat()
    )


def test_utc_now_and_new_uuid() -> None:
    before = datetime.now(UTC)
    now = utc_now()
    assert now.tzinfo is UTC and before <= now <= datetime.now(UTC)
    identifiers = {new_uuid() for _ in range(100)}
    assert len(identifiers) == 100
    pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
    assert all(re.fullmatch(pattern, i) for i in identifiers)
