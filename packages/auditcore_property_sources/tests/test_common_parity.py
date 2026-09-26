"""Parity old ↔ new: HTML detection and time-zone check from ``auditcore_common``."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from auditcore_common.html_text import has_html_marker

from auditcore_property_sources import zvg_lifecycle
from auditcore_property_sources.zvg_lifecycle import CaseState

HTML_BODIES = [
    "",
    "<html>",
    "<HTML lang=de>",
    "<!DOCTYPE html>",
    "<!doctype html><title>x</title>",
    "plain text",
    '{"json": true}',
    " " * 4090 + "<html>",  # marker crosses the 4096 window
    " " * 4091 + "<html>",
    " " * 4089 + "<!doctype",
    "İ" * 4095 + "<html>",  # lower() lengthens the text; the window is cut first
    "x" * 5000 + "<!DOCTYPE html>",
    "<htm",
]


# 0.1.2 adapters/_base.py :: _Portal._get_text and adapters/zvg.py (listing) – verbatim test
def legacy_is_html_window(body: str) -> bool:
    return not ("<html" not in body[:4096].lower() and "<!doctype" not in body[:4096].lower())


# 0.1.2 adapters/zvg.py (detail page) – verbatim test
def legacy_is_html_head(doc: str) -> bool:
    head = doc[:4096].lower()
    return not ("<html" not in head and "<!doctype" not in head)


# 0.1.2 zvg_lifecycle.py :: _aware (verbatim)
def legacy_aware(now: datetime) -> datetime:
    if now.tzinfo is None:
        raise ValueError("Zeitangaben müssen eine Zeitzone tragen.")
    return now


@pytest.mark.parametrize("body", HTML_BODIES, ids=range(len(HTML_BODIES)))
def test_html_marker_detection_is_unchanged(body: str) -> None:
    assert has_html_marker(body) == legacy_is_html_window(body) == legacy_is_html_head(body)


NAIVE = datetime(2026, 9, 26, 12, 0)
AWARE = [
    datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
    NAIVE.replace(tzinfo=timezone(timedelta(hours=2))),
]


@pytest.mark.parametrize("moment", AWARE)
def test_aware_moments_pass_unchanged(moment: datetime) -> None:
    assert zvg_lifecycle.mark_seen([], [], moment) == []
    assert legacy_aware(moment) is moment


def test_naive_moment_fails_with_the_same_message() -> None:
    with pytest.raises(ValueError) as old:
        legacy_aware(NAIVE)
    with pytest.raises(ValueError) as new:
        zvg_lifecycle.mark_seen([], [], NAIVE)
    with pytest.raises(ValueError) as state:
        CaseState("A 1/26", "erfasst", NAIVE)
    assert str(new.value) == str(state.value) == str(old.value)
