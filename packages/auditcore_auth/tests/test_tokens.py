"""JWT security tests: alg=none, wrong key, expiry, tampering, allowlist, clock, types."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from conftest import FAST_TOKEN, KEY, NOW

from auditcore_auth import (
    DEFAULT_TOKEN_PROFILE,
    ConfigurationError,
    DisallowedAlgorithmError,
    ExpiredTokenError,
    ImmatureTokenError,
    InvalidClaimError,
    InvalidSignatureError,
    MalformedTokenError,
    MissingClaimError,
    TokenIssuer,
    TokenProfile,
    TokenTypeError,
    TokenVerifier,
    fixed_clock,
)
from auditcore_auth.clock import to_epoch


def issuer(profile: TokenProfile = FAST_TOKEN, at: datetime = NOW) -> TokenIssuer:
    return TokenIssuer(profile, KEY, clock=fixed_clock(at))


def verifier(profile: TokenProfile = FAST_TOKEN, at: datetime = NOW) -> TokenVerifier:
    return TokenVerifier(profile, KEY, clock=fixed_clock(at))


def forge(claims: dict[str, object], key: str = KEY, algorithm: str = "HS256") -> str:
    return jwt.encode(claims, key, algorithm=algorithm)


def hmac_token(claims: dict[str, object], secret: bytes) -> str:
    def part(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    signing_input = part(b'{"alg":"HS256","typ":"JWT"}') + "." + part(json.dumps(claims).encode())
    digest = hmac.new(secret, signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + part(digest)


def base_claims(offset: int = 600) -> dict[str, object]:
    return {"sub": "7", "iat": to_epoch(NOW), "exp": to_epoch(NOW) + offset}


def test_roundtrip_with_default_layout() -> None:
    issued = issuer().issue({"role": "pruefer"}, subject="7")
    verified = verifier().verify(issued.token)
    assert list(verified.claims) == ["sub", "role", "iat", "exp"]
    assert verified.subject == "7" and verified.algorithm == "HS256"
    assert verified.issued_at == NOW and verified.expires_at == NOW + timedelta(minutes=10)
    assert issued.expires_in == 600 and issued.expires_at == NOW + timedelta(minutes=10)


def test_alg_none_is_rejected() -> None:
    token = jwt.encode(base_claims(), None, algorithm="none")
    with pytest.raises(DisallowedAlgorithmError):
        verifier().verify(token)
    unsigned = token.rsplit(".", 1)[0] + "."
    with pytest.raises(DisallowedAlgorithmError):
        verifier().verify(unsigned)


def test_algorithm_outside_the_allowlist_is_rejected() -> None:
    with pytest.raises(DisallowedAlgorithmError):
        verifier().verify(forge(base_claims(), key=KEY * 2, algorithm="HS512"))


def test_wrong_key_is_rejected() -> None:
    with pytest.raises(InvalidSignatureError):
        verifier().verify(forge(base_claims(), key="another-secret-0123456789abcdefghij"))


def test_tampered_payload_and_signature_are_rejected() -> None:
    head, _body, signature = issuer().issue(subject="7").token.split(".")
    forged = base64.urlsafe_b64encode(json.dumps(base_claims(10**6)).encode()).rstrip(b"=")
    with pytest.raises(InvalidSignatureError):
        verifier().verify(f"{head}.{forged.decode()}.{signature}")
    flipped = signature[:-3] + ("AAA" if signature[-3:] != "AAA" else "BBB")
    with pytest.raises(InvalidSignatureError):
        verifier().verify(f"{head}.{_body}.{flipped}")


@pytest.mark.parametrize("token", ["", "abc", "a.b.c", "x" * 9000])
def test_malformed_tokens(token: str) -> None:
    with pytest.raises(MalformedTokenError):
        verifier().verify(token)
    assert verifier().verify_or_none(token) is None


def test_expiry_and_leeway() -> None:
    token = issuer().issue(subject="7").token
    assert verifier(at=NOW + timedelta(minutes=9, seconds=59)).verify(token)
    with pytest.raises(ExpiredTokenError):
        verifier(at=NOW + timedelta(minutes=10)).verify(token)
    tolerant = TokenProfile("tolerant", lifetime=timedelta(minutes=10),
                            leeway=timedelta(seconds=30))
    assert verifier(tolerant, at=NOW + timedelta(minutes=10, seconds=29)).verify(token)
    with pytest.raises(ExpiredTokenError):
        verifier(tolerant, at=NOW + timedelta(minutes=10, seconds=30)).verify(token)


def test_future_iat_and_nbf() -> None:
    later = forge({**base_claims(), "iat": to_epoch(NOW) + 60})
    with pytest.raises(ImmatureTokenError):
        verifier().verify(later)
    jose_like = TokenProfile("jose", lifetime=timedelta(minutes=10), reject_future_iat=False)
    assert verifier(jose_like).verify(later)
    with pytest.raises(ImmatureTokenError):
        verifier().verify(forge({**base_claims(), "nbf": to_epoch(NOW) + 60}))


@pytest.mark.parametrize("missing", ["exp", "iat", "sub"])
def test_required_claims(missing: str) -> None:
    claims = base_claims()
    del claims[missing]
    with pytest.raises(MissingClaimError) as caught:
        verifier().verify(forge(claims))
    assert caught.value.claim == missing


@pytest.mark.parametrize(("claim", "value"), [
    ("sub", 7), ("exp", "tomorrow"), ("iat", True), ("jti", 5),
])
def test_claim_types(claim: str, value: object) -> None:
    with pytest.raises(InvalidClaimError):
        verifier().verify(forge({**base_claims(), claim: value}))


def test_audience_in_token_without_configuration_is_rejected() -> None:
    assert verifier().verify_or_none(forge({**base_claims(), "aud": "fremd"})) is None


def test_token_types() -> None:
    profile = TokenProfile("typed", lifetime=timedelta(minutes=5), rejected_types=("refresh",))
    refresh = forge({**base_claims(), "type": "refresh"})
    with pytest.raises(TokenTypeError):
        verifier(profile).verify(refresh)
    access = forge({**base_claims(), "type": "access"})
    assert verifier(profile).verify(access, expected_type="access")
    with pytest.raises(TokenTypeError):
        verifier(profile).verify(access, expected_type="download")


def test_issuer_protects_reserved_and_fixed_claims() -> None:
    fixed = TokenProfile("fixed", lifetime=timedelta(minutes=5),
                         layout=("sub", "type", "*", "iat", "exp"), fixed_claims=(("type", "a"),))
    for claims in ({"exp": 1}, {"iat": 1}, {"nbf": 1}, {"type": "refresh"}):
        with pytest.raises(ValueError):
            issuer(fixed).issue(claims, subject="7")
    with pytest.raises(ValueError, match="String"):
        issuer().issue({"sub": 7})
    with pytest.raises(ValueError, match="verlangt"):
        issuer().issue({"role": "x"})
    with pytest.raises(ValueError, match="Laufzeit"):
        issuer().issue(subject="7", lifetime=timedelta(0))
    closed = TokenProfile("closed", lifetime=timedelta(minutes=5), layout=("sub", "iat", "exp"))
    with pytest.raises(ValueError, match="keine weiteren"):
        issuer(closed).issue({"role": "x"}, subject="7")
    assert list(verifier(fixed).verify(issuer(fixed).issue(subject="7").token).claims) == [
        "sub", "type", "iat", "exp"]


def test_naive_clock_is_refused() -> None:
    naive = TokenIssuer(FAST_TOKEN, KEY, clock=lambda: datetime(2026, 9, 25, 12))
    with pytest.raises(ConfigurationError):
        naive.issue(subject="7")
    with pytest.raises(ConfigurationError):
        fixed_clock(datetime(2026, 9, 25, 12))


def test_other_timezones_are_normalised() -> None:
    cest = NOW.astimezone(timezone(timedelta(hours=2)))
    assert issuer(at=cest).issue(subject="7").token == issuer().issue(subject="7").token


@pytest.mark.parametrize("kwargs", [
    {"algorithm": "none", "accepted_algorithms": ("none",)},
    {"algorithm": "HS256", "accepted_algorithms": ("HS256", "RS256")},
    {"algorithm": "HS256", "accepted_algorithms": ("HS512",)},
    {"algorithm": "XS1"},
    {"layout": ("sub", "iat")},
    {"required_claims": ("iat", "sub")},
    {"layout": ("sub", "exp"), "required_claims": ("exp", "iat")},
    {"layout": ("sub", "sub", "exp")},
    {"fixed_claims": (("exp", "1"),)},
    {"fixed_claims": (("type", "x"),)},
    {"leeway": timedelta(seconds=-1)},
    {"lifetime": timedelta(0)},
    {"min_key_bytes": -1},
])
def test_unsafe_profiles_are_refused(kwargs: dict[str, object]) -> None:
    arguments: dict[str, object] = {"lifetime": timedelta(minutes=5), **kwargs}
    with pytest.raises(ConfigurationError):
        TokenProfile("bad", **arguments)  # type: ignore[arg-type]


def test_key_requirements() -> None:
    with pytest.raises(ConfigurationError):
        TokenIssuer(DEFAULT_TOKEN_PROFILE, "short")
    with pytest.raises(ConfigurationError):
        TokenVerifier(DEFAULT_TOKEN_PROFILE, "")
    legacy = TokenProfile("legacy", lifetime=timedelta(minutes=5), min_key_bytes=0)
    with pytest.raises(ConfigurationError):
        TokenVerifier(legacy, "")
    assert TokenVerifier(legacy, b"0123456789abcdef")


def test_key_id_header() -> None:
    token = TokenIssuer(FAST_TOKEN, KEY, clock=fixed_clock(NOW), key_id="k1").issue(subject="7")
    assert jwt.get_unverified_header(token.token)["kid"] == "k1"


def test_asymmetric_profile_and_key_confusion() -> None:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    private = ec.generate_private_key(ec.SECP256R1())
    private_pem = private.private_bytes(serialization.Encoding.PEM,
                                        serialization.PrivateFormat.PKCS8,
                                        serialization.NoEncryption())
    public_pem = private.public_key().public_bytes(serialization.Encoding.PEM,
                                                   serialization.PublicFormat.SubjectPublicKeyInfo)
    profile = TokenProfile("es", lifetime=timedelta(minutes=5), algorithm="ES256")
    token = TokenIssuer(profile, private_pem, clock=fixed_clock(NOW)).issue(subject="7").token
    assert TokenVerifier(profile, public_pem, clock=fixed_clock(NOW)).verify(token).subject == "7"
    # HS256 token signed with the public key as HMAC secret must not pass
    # (built by hand: PyJWT itself refuses PEM keys as HMAC secrets).
    confused = hmac_token(base_claims(), public_pem)
    with pytest.raises(DisallowedAlgorithmError):
        TokenVerifier(profile, public_pem, clock=fixed_clock(NOW)).verify(confused)
