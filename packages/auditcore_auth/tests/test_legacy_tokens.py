"""Tokens: byte-identical issuance and the same accept/reject decisions as the old code.

Deviations are listed explicitly (see docs/behavior-changes.md):
D1 tokens without ``exp`` are rejected; D2 tokens without ``iat`` are rejected
where the app always issued ``iat``; D3 tokens without ``sub`` are rejected
where every issuing call site set ``sub``.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from conftest import observed, observed_app

from auditcore_auth import APP_PROFILES, TokenIssuer, TokenVerifier, app_profile, fixed_clock
from auditcore_auth.clock import from_epoch

SECRET = str(observed()["secret"])
FROZEN = datetime.fromisoformat(str(observed()["frozen_instant"]))
M, H = timedelta(minutes=1), timedelta(hours=1)

# (app, label) -> (token kind, claims in call order, lifetime or None for the default)
ISSUE: dict[tuple[str, str], tuple[str, dict[str, Any], timedelta | None]] = {
    ("audit_designer", "login"): ("access", {"sub": "42", "mfa": True}, 720 * M),
    ("audit_designer", "default"): ("access", {"sub": "1"}, None),
    ("audit_designer", "kernel_capability"): ("access", {
        "token_type": "notebook_kernel", "page_id": "p-1", "user_id": 42,
        "scope": "notebook:kernel-api"}, 5 * M),
    ("audit_designer", "sse_ticket"): ("access", {
        "sub": "42", "scope": "vp-ai:progress-sse", "project_id": "pr-1"}, timedelta(seconds=60)),
    ("flownavigator", "login"): ("access", {"sub": "u-1", "tenant_id": "t-1", "role": "admin"},
                                 None),
    ("flownavigator", "vendor"): ("access", {"sub": "v-1", "type": "vendor",
                                             "role": "vendor_admin"}, None),
    ("flowsearch", "login"): ("access", {"sub": "7", "tenant_id": 3}, 30 * M),
    ("qaaudit", "login"): ("access", {"sub": "5", "role": "admin"}, None),
    ("qaaudit", "extra_claims"): ("access", {"sub": "5", "role": "pruefer", "scope": "x"}, 2 * H),
    ("versteigerung", "login"): ("access", {"sub": "9", "email": "a@b.de", "role": "bieter"},
                                 None),
    ("regulierung", "access_lkb"): ("access", {"sub": "sachbearbeiter", "role": "lkb"}, 8 * H),
    ("regulierung", "access_admin"): ("access", {"sub": "admin", "role": "admin"}, 24 * H),
    ("regulierung", "refresh"): ("refresh", {"sub": "sachbearbeiter", "role": "lkb"}, None),
    ("flowinvoice", "login"): ("access", {"sub": "pruefer", "role": "auditor"}, None),
    ("flowinvoice", "core_default"): ("access", {"sub": "pruefer"}, 8 * H),
    ("audit-portal", "login"): ("access", {"sub": "pruefer", "role": "auditor"}, None),
    # Legacy dropped the caller's "sub" from extra_claims silently; the library
    # refuses it (see test_audit_portal_rejects_sub_in_extra_claims).
    ("audit-portal", "sse_ticket"): ("ticket", {"scope": "flowstat:sse", "run_uuid": "r-1",
                                                "sub": "pruefer"}, timedelta(seconds=60)),
    ("audit-portal", "core_default"): ("ticket", {"sub": "pruefer"}, None),
    ("flowlib", "default"): ("access", {"sub": "1", "role": "x"}, None),
}

DEVIATIONS: dict[tuple[str, str], str] = {
    **{(app, "without_exp"): "D1" for app in APP_PROFILES},
    **{(app, "valid_without_iat"): "D2" for app in (
        "audit_designer", "qaaudit", "versteigerung", "regulierung", "flowinvoice",
        "audit-portal", "flowlib")},
    **{(app, "without_sub"): "D3" for app in ("flownavigator", "qaaudit", "versteigerung")},
}


def issued_cases() -> list[tuple[str, dict[str, Any]]]:
    return [(app, case) for app in sorted(APP_PROFILES)
            for case in observed_app(app)["issued"]]  # type: ignore[attr-defined]


def test_every_observed_issuance_is_reproduced() -> None:
    assert {(app, case["label"]) for app, case in issued_cases()} == set(ISSUE)


@pytest.mark.parametrize(("app", "case"), issued_cases(),
                         ids=[f"{a}-{c['label']}" for a, c in issued_cases()])
def test_issued_tokens_are_byte_identical(app: str, case: dict[str, Any]) -> None:
    kind, claims, lifetime = ISSUE[(app, case["label"])]
    profile = app_profile(app).token(kind)
    issuer = TokenIssuer(profile, SECRET, clock=fixed_clock(FROZEN))
    issued = issuer.issue(claims, lifetime=lifetime)
    assert issued.token == case["token"]
    verifier = TokenVerifier(profile, SECRET, clock=fixed_clock(FROZEN + timedelta(seconds=1)))
    assert verifier.verify(case["token"]).as_dict() == case["claims"]


def decode_cases() -> list[tuple[str, str, dict[str, Any]]]:
    return [(app, name, result) for app in sorted(APP_PROFILES)
            for name, result in observed_app(app)["decoded"].items()]  # type: ignore[attr-defined]


@pytest.mark.parametrize(("app", "name", "legacy"), decode_cases(),
                         ids=[f"{a}-{n}" for a, n, _ in decode_cases()])
def test_verification_matches_the_legacy_decision(app: str, name: str,
                                                  legacy: dict[str, Any]) -> None:
    now = from_epoch(int(observed_app(app)["decode_now"]))  # type: ignore[call-overload]
    verifier = TokenVerifier(app_profile(app).token("access"), SECRET, clock=fixed_clock(now))
    result = verifier.verify_or_none(legacy["token"])
    accepted = result is not None
    if (app, name) in DEVIATIONS:
        assert legacy["outcome"] == "accept" and not accepted, DEVIATIONS[(app, name)]
        return
    assert accepted is (legacy["outcome"] == "accept")
    if result is not None:
        assert result.as_dict() == legacy["claims"]


def test_regulierung_refresh_token_is_no_access_token() -> None:
    profile = app_profile("regulierung")
    refresh = TokenIssuer(profile.token("refresh"), SECRET, clock=fixed_clock(FROZEN)).issue(
        {"sub": "sachbearbeiter", "role": "lkb"})
    clock = fixed_clock(FROZEN + M)
    assert TokenVerifier(profile.token("access"), SECRET, clock=clock).verify_or_none(
        refresh.token) is None
    verified = TokenVerifier(profile.token("refresh"), SECRET, clock=clock).verify(
        refresh.token, expected_type="refresh")
    assert verified.subject == "sachbearbeiter"
    assert refresh.expires_in == 7 * 24 * 3600


def test_audit_portal_rejects_sub_in_extra_claims() -> None:
    issuer = TokenIssuer(app_profile("audit-portal").token("ticket"), SECRET)
    with pytest.raises(ValueError, match="doppelt"):
        issuer.issue({"scope": "flowstat:sse", "sub": "fremd"}, subject="pruefer")
