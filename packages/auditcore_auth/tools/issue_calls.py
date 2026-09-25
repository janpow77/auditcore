"""Representative token issuance calls, taken from the real call sites of each app.

Every entry calls the *legacy* function (executed from the pinned source) with
arguments shaped like the call site named in the comment.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from pathlib import Path
from typing import Any

Calls = list[tuple[str, Callable[[], Any]]]
Loader = Callable[[Path, str, str, str], Callable[..., Any]]


def audit_designer(root: Path, app: str, ns: dict[str, Any], load: Loader) -> Calls:
    create = ns["create_access_token"]
    return [
        # backend/app/api/auth.py:374 (login)
        ("login", lambda: create(data={"sub": "42", "mfa": True},
                                 expires_delta=timedelta(minutes=720))),
        # scripts: create_access_token({"sub": "1"}) → Standardlaufzeit
        ("default", lambda: create({"sub": "1"})),
        # backend/app/api/vpai_notebook/jupyter.py:286 (Capability ohne sub)
        ("kernel_capability", lambda: create(
            {"token_type": "notebook_kernel", "page_id": "p-1", "user_id": 42,
             "scope": "notebook:kernel-api"}, expires_delta=timedelta(minutes=5))),
        # backend/app/modules/vp_ai/api/progress.py:37 (SSE-Ticket)
        ("sse_ticket", lambda: create({"sub": "42", "scope": "vp-ai:progress-sse",
                                       "project_id": "pr-1"}, expires_delta=timedelta(seconds=60))),
    ]


def flownavigator(root: Path, app: str, ns: dict[str, Any], load: Loader) -> Calls:
    create = ns["create_access_token"]
    return [
        # apps/backend/app/services/auth_service.py:70
        ("login", lambda: create(data={"sub": "u-1", "tenant_id": "t-1", "role": "admin"})),
        # apps/backend/app/api/vendor.py:140
        ("vendor", lambda: create(data={"sub": "v-1", "type": "vendor", "role": "vendor_admin"})),
    ]


def flowsearch(root: Path, app: str, ns: dict[str, Any], load: Loader) -> Calls:
    create = ns["create_access_token"]
    # backend/app/api/auth.py:76
    return [("login", lambda: create(data={"sub": "7", "tenant_id": 3},
                                     expires_delta=timedelta(minutes=30)))]


def qaaudit(root: Path, app: str, ns: dict[str, Any], load: Loader) -> Calls:
    create = ns["create_access_token"]
    return [
        # backend/app/api/v1/auth.py:48
        ("login", lambda: create(5, role="admin")),
        ("extra_claims", lambda: create("5", role="pruefer", extra_claims={"scope": "x"},
                                        ttl_hours=2)),
    ]


def versteigerung(root: Path, app: str, ns: dict[str, Any], load: Loader) -> Calls:
    create = ns["create_access_token"]
    # backend/app/api/routers/auth.py:42
    return [("login", lambda: create(subject="9",
                                     extra_claims={"email": "a@b.de", "role": "bieter"}))]


def regulierung(root: Path, app: str, ns: dict[str, Any], load: Loader) -> Calls:
    access, refresh = ns["create_access_token"], ns["create_refresh_token"]
    # backend/app/api/auth_routes.py:305/308 (Laufzeit aus der Administration)
    return [
        ("access_lkb", lambda: access("sachbearbeiter", "lkb", expires_hours=8)),
        ("access_admin", lambda: access("admin", role="admin", expires_hours=24)),
        ("refresh", lambda: refresh("sachbearbeiter", "lkb")),
    ]


def _user_auth(root: Path, app: str, load: Loader) -> Callable[..., Any]:
    return load(root, app, "backend/app/api/user_auth.py", "_create_access_token")


def flowinvoice(root: Path, app: str, ns: dict[str, Any], load: Loader) -> Calls:
    create_user_token = _user_auth(root, app, load)
    return [
        # backend/app/api/user_auth.py:239 (einziger Ausstellungsweg)
        ("login", lambda: create_user_token("pruefer", "auditor")),
        # backend/app/core/security.py:24 (exportiert, im Backend ungenutzt)
        ("core_default", lambda: ns["create_access_token"]("pruefer")),
    ]


def audit_portal(root: Path, app: str, ns: dict[str, Any], load: Loader) -> Calls:
    create_user_token = _user_auth(root, app, load)
    create = ns["create_access_token"]
    return [
        # backend/app/api/user_auth.py:187
        ("login", lambda: create_user_token("pruefer", "auditor")),
        # backend/app/modules/flowstat/api/pipelines.py:736 (SSE-Ticket)
        ("sse_ticket", lambda: create("pruefer", expires_delta=timedelta(seconds=60),
                                      extra_claims={"scope": "flowstat:sse", "run_uuid": "r-1",
                                                    "sub": "ignoriert"})),
        ("core_default", lambda: create("pruefer")),
    ]


def flowlib(root: Path, app: str, ns: dict[str, Any], load: Loader) -> Calls:
    from capture_legacy_auth import SECRET  # noqa: PLC0415

    create = ns["create_access_token"]
    return [("default", lambda: create({"sub": "1", "role": "x"}, SECRET))]


ISSUE_CALLS: dict[str, Callable[[Path, str, dict[str, Any], Loader], Calls]] = {
    "audit_designer": audit_designer,
    "flownavigator": flownavigator,
    "flowsearch": flowsearch,
    "qaaudit": qaaudit,
    "versteigerung": versteigerung,
    "regulierung": regulierung,
    "flowinvoice": flowinvoice,
    "audit-portal": audit_portal,
    "flowlib": flowlib,
}
