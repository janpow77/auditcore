"""Execute the legacy auth helpers of the nine applications and record what they do.

Run in a separate environment with the *legacy* libraries the applications pin
(passlib 1.7.4, python-jose 3.3.0, bcrypt 4.2.1, PyJWT 2.10.1, argon2-cffi 23.1.0,
fastapi, sqlalchemy)::

    python tools/capture_legacy_auth.py --repos-root ~/Projekte \
        --output tests/fixtures/legacy_auth_observed.json

The source of every helper is read with ``git show <commit>:<path>`` from the
pinned commits in ``legacy_sources.py`` and executed unchanged; only the
application settings and the clock are replaced. The applications are read,
never modified.
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import subprocess
import sys
import time
import types
from collections.abc import Callable
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from legacy_decoders import DECODERS  # noqa: E402
from legacy_sources import REFERENCE_ONLY, SOURCES  # noqa: E402

SECRET = "characterization-secret-0123456789abcdef"
WRONG_SECRET = "another-secret-0123456789abcdef-xyz"
FROZEN = datetime(2026, 9, 25, 12, 0, 0, 654321, tzinfo=UTC)
PASSWORDS = ["geheim123", "Prüfung-ÄÖÜß", "", "x" * 80, "ä" * 40, "a\x00b"]
MALFORMED = ["", "garbage", "$2b$12$short", "$argon2id$v=19$m=65536,t=3,p=4$abc"]


class FrozenDatetime(datetime):
    """``datetime`` whose ``now``/``utcnow`` return the capture instant."""

    @classmethod
    def now(cls, tz: Any = None) -> datetime:  # type: ignore[override]
        return FROZEN if tz is None else FROZEN.astimezone(tz)

    @classmethod
    def utcnow(cls) -> datetime:  # type: ignore[override]
        return FROZEN.replace(tzinfo=None)


class Secret:
    def __init__(self, value: str) -> None:
        self._value = value

    def get_secret_value(self) -> str:
        return self._value


SETTINGS: dict[str, dict[str, Any]] = {
    "audit_designer": {"SECRET_KEY": SECRET, "ALGORITHM": "HS256",
                       "ACCESS_TOKEN_EXPIRE_MINUTES": 720},
    "flownavigator": {"secret_key": SECRET, "algorithm": "HS256",
                      "access_token_expire_minutes": 1440},
    "flowsearch": {"SECRET_KEY": SECRET, "ALGORITHM": "HS256", "ACCESS_TOKEN_EXPIRE_MINUTES": 30},
    "qaaudit": {"jwt_secret": SECRET, "jwt_algorithm": "HS256", "jwt_ttl_hours": 24},
    "versteigerung": {"jwt_secret": SECRET, "jwt_alg": "HS256", "access_ttl_min": 30},
    "regulierung": {"secret_key": Secret(SECRET), "jwt_algorithm": "HS256",
                    "jwt_expire_hours_lkb": 8, "jwt_expire_hours_admin": 24},
    "flowinvoice": {"secret_key": Secret(SECRET), "jwt_algorithm": "HS256",
                    "jwt_expire_hours": 24},
    "audit-portal": {"secret_key": Secret(SECRET), "jwt_algorithm": "HS256",
                     "jwt_expire_hours": 24},
    "flowlib": {},
}


def git_show(root: Path, app: str, path: str) -> str:
    source = SOURCES[app]
    checkout = root / str(source["checkout"])
    return subprocess.run(["git", "-C", str(checkout), "show", f"{source['commit']}:{path}"],
                          check=True, capture_output=True, text=True).stdout


def install_stubs(app: str) -> None:
    for name in [n for n in sys.modules if n == "app" or n.startswith("app.")]:
        del sys.modules[name]
    settings = types.SimpleNamespace(**SETTINGS[app])
    modules = {name: types.ModuleType(name) for name in (
        "app", "app.core", "app.core.config", "app.config", "app.core.database",
        "app.models", "app.models.user", "app.services", "app.services.betrieb")}
    for module in (modules["app.core.config"], modules["app.config"]):
        module.settings = settings  # type: ignore[attr-defined]
        module.get_settings = lambda: settings  # type: ignore[attr-defined]
    modules["app.core.database"].get_db = lambda: None  # type: ignore[attr-defined]
    modules["app.models.user"].User = type("User", (), {"id": 0})  # type: ignore[attr-defined]
    sys.modules.update(modules)


def freeze(namespace: dict[str, Any]) -> None:
    if namespace.get("datetime") is datetime:
        namespace["datetime"] = FrozenDatetime
    if isinstance(namespace.get("dt"), types.ModuleType):
        namespace["dt"] = types.SimpleNamespace(datetime=FrozenDatetime, UTC=UTC,
                                                timedelta=timedelta, timezone=timezone)


def load_security(root: Path, app: str) -> dict[str, Any]:
    install_stubs(app)
    namespace: dict[str, Any] = {"__name__": f"legacy_{app.replace('-', '_')}"}
    exec(compile(git_show(root, app, str(SOURCES[app]["security"])), app, "exec"), namespace)
    freeze(namespace)
    return namespace


def load_function(root: Path, app: str, path: str, name: str) -> Callable[..., Any]:
    """Execute one function definition of a module that is too heavy to import."""
    tree = ast.parse(git_show(root, app, path))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    from jose import jwt  # the call sites use python-jose

    namespace: dict[str, Any] = {"datetime": FrozenDatetime, "UTC": UTC, "timedelta": timedelta,
                                 "jwt": jwt, "get_settings": sys.modules["app.config"].get_settings}
    exec(compile(ast.Module(body=[node], type_ignores=[]), f"{app}:{path}", "exec"), namespace)
    return namespace[name]  # type: ignore[no-any-return]


def outcome(call: Callable[[], Any]) -> dict[str, Any]:
    try:
        return {"result": call()}
    except BaseException as error:  # noqa: BLE001 - bcrypt panics derive from BaseException
        return {"error": type(error).__name__}


def password_cases(hash_: Callable[[str], str], verify: Callable[[str, str], bool]
                   ) -> dict[str, Any]:
    cases = []
    for password in PASSWORDS:
        created = outcome(lambda p=password: hash_(p))
        case: dict[str, Any] = {"password": password, "hash": created}
        stored = created.get("result")
        if isinstance(stored, str):
            prefix = password.encode()[:72].decode(errors="ignore")
            case["verify_same"] = outcome(lambda p=password, h=stored: verify(p, h))
            case["verify_wrong"] = outcome(lambda h=stored: verify("falsch", h))
            case["verify_prefix72"] = outcome(lambda p=prefix, h=stored: verify(p, h))
        cases.append(case)
    malformed = [{"hash": bad, "verify": outcome(lambda b=bad: verify("geheim123", b))}
                 for bad in MALFORMED]
    return {"cases": cases, "malformed": malformed}


def issue_cases(root: Path, app: str, ns: dict[str, Any]) -> list[dict[str, Any]]:
    from issue_calls import ISSUE_CALLS  # noqa: PLC0415

    cases = []
    for label, call in ISSUE_CALLS[app](root, app, ns, load_function):
        token = call()
        token = token[0] if isinstance(token, tuple) else token
        cases.append({"label": label, "token": token, "claims": claims_of(token)})
    return cases


def claims_of(token: str) -> dict[str, Any]:
    payload = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))  # type: ignore[no-any-return]


def capture_app(root: Path, app: str) -> dict[str, Any]:
    ns = load_security(root, app)
    hash_name = "hash_password" if "hash_password" in ns else "get_password_hash"
    record: dict[str, Any] = {
        "passwords": password_cases(ns[hash_name], ns["verify_password"]),
        "issued": issue_cases(root, app, ns),
    }
    now = int(time.time())
    record["decode_now"] = now
    record["decoded"] = DECODERS[app](ns, SECRET, WRONG_SECRET, now)
    return record


def blob_sha(text: str) -> str:
    data = text.encode()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # noqa: S324 - git object id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repos-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from importlib.metadata import version

    observed: dict[str, Any] = {
        "schema_version": 1,
        "frozen_instant": FROZEN.isoformat(),
        "secret": SECRET,
        "wrong_secret": WRONG_SECRET,
        "libraries": {name: version(name) for name in (
            "passlib", "python-jose", "bcrypt", "PyJWT", "argon2-cffi")},
        "sources": {app: {**meta, "blobs": {path: blob_sha(git_show(args.repos_root, app, path))
                                            for path in meta["files"]}}  # type: ignore[attr-defined]
                    for app, meta in SOURCES.items()},
        "reference_only": REFERENCE_ONLY,
        "apps": {app: capture_app(args.repos_root, app) for app in SOURCES},
    }
    args.output.write_text(json.dumps(observed, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
