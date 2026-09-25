"""Token verification as the applications perform it, applied to a fixed case set.

Where ``security.py`` has a decode helper it is called directly; otherwise the
decode expression of the consuming call site is reproduced verbatim (file and
line in the comment).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Decode = Callable[[str], Any]


def case_tokens(secret: str, wrong: str, now: int) -> dict[str, str]:
    import jwt  # PyJWT, only to build the inputs

    def sign(claims: dict[str, Any], key: str = secret, alg: str = "HS256") -> str:
        return jwt.encode(claims, key, algorithm=alg)

    valid = sign({"sub": "7", "iat": now, "exp": now + 3600})
    head, body, sig = valid.split(".")
    other = sign({"sub": "8", "iat": now, "exp": now + 3600}).split(".")[1]
    return {
        "valid": valid,
        "valid_without_iat": sign({"sub": "7", "exp": now + 3600}),
        "without_sub": sign({"iat": now, "exp": now + 3600}),
        "without_exp": sign({"sub": "7", "iat": now}),
        "expired": sign({"sub": "7", "iat": now - 7200, "exp": now - 3600}),
        "expired_30s": sign({"sub": "7", "iat": now - 600, "exp": now - 30}),
        "wrong_key": sign({"sub": "7", "iat": now, "exp": now + 3600}, key=wrong),
        "alg_none": jwt.encode({"sub": "7", "iat": now, "exp": now + 3600}, None, algorithm="none"),
        "alg_hs512": sign({"sub": "7", "iat": now, "exp": now + 3600}, alg="HS512"),
        "tampered_payload": f"{head}.{other}.{sig}",
        "tampered_signature": f"{head}.{body}.{sig[:-2]}{'AA' if sig[-2:] != 'AA' else 'BB'}",
        "garbage": "abc",
        "empty": "",
        "sub_int": sign({"sub": 7, "iat": now, "exp": now + 3600}),
        "iat_future": sign({"sub": "7", "iat": now + 600, "exp": now + 3600}),
        "nbf_future": sign({"sub": "7", "iat": now, "nbf": now + 600, "exp": now + 3600}),
        "refresh_type": sign({"sub": "7", "role": "lkb", "type": "refresh", "iat": now,
                              "exp": now + 3600}),
    }


def run(decode: Decode, tokens: dict[str, str]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for name, token in tokens.items():
        try:
            payload = decode(token)
        except Exception as error:  # noqa: BLE001 - the error class is the observation
            results[name] = {"token": token, "outcome": "reject", "error": type(error).__name__}
            continue
        accepted = payload is not None
        results[name] = {"token": token, "outcome": "accept" if accepted else "reject",
                         "claims": payload}
    return results


def _jose(secret: str) -> Decode:
    from jose import jwt

    return lambda token: jwt.decode(token, secret, algorithms=["HS256"])


def _require_sub(decode: Decode) -> Decode:
    def checked(token: str) -> Any:
        payload = decode(token)
        if payload.get("sub") is None:
            raise LookupError("sub")
        return payload

    return checked


def _flowsearch(secret: str) -> Decode:
    # backend/app/core/security.py:62-66 (get_current_user)
    def decode(token: str) -> Any:
        payload = _require_sub(_jose(secret))(token)
        int(payload["sub"])
        return payload

    return decode


def _regulierung(secret: str) -> Decode:
    # backend/app/core/auth/jwt_backend.py:25-55 (JwtAuthBackend.verify_token)
    import jwt

    def decode(token: str) -> Any:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        if payload.get("type") == "refresh":
            raise PermissionError("refresh")
        if not payload.get("sub"):
            raise LookupError("sub")
        return payload

    return decode


def _decoders() -> dict[str, Callable[[dict[str, Any], str], Decode]]:
    return {
        "audit_designer": lambda ns, key: ns["decode_token"],
        "flownavigator": lambda ns, key: ns["decode_access_token"],
        "flowsearch": lambda ns, key: _flowsearch(key),
        "qaaudit": lambda ns, key: ns["decode_access_token"],
        "versteigerung": lambda ns, key: ns["decode_token"],
        "regulierung": lambda ns, key: _regulierung(key),
        # backend/app/api/deps.py:103-110 (get_current_user)
        "flowinvoice": lambda ns, key: _require_sub(_jose(key)),
        # backend/app/api/deps.py:104-111 (get_current_user)
        "audit-portal": lambda ns, key: _require_sub(_jose(key)),
        "flowlib": lambda ns, key: lambda token: ns["decode_token"](token, key),
    }


def _bind(app: str) -> Callable[[dict[str, Any], str, str, int], dict[str, Any]]:
    def capture(ns: dict[str, Any], secret: str, wrong: str, now: int) -> dict[str, Any]:
        return run(_decoders()[app](ns, secret), case_tokens(secret, wrong, now))

    return capture


DECODERS = {app: _bind(app) for app in _decoders()}
