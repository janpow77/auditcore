"""Run with python -I against an installed wheel or Debian package; no pytest needed.

The base installation has no runtime dependencies. Backends are optional
extras; without them the library must fail with a clear error, not at import.
"""

from datetime import UTC, datetime, timedelta
from importlib.metadata import distribution
from importlib.util import find_spec

from auditcore_auth import (
    APP_PROFILES,
    ARGON2ID,
    BCRYPT,
    DEFAULT_TOKEN_PROFILE,
    BackendUnavailableError,
    ConfigurationError,
    HashScheme,
    PasswordHasher,
    TokenIssuer,
    TokenProfile,
    TokenVerifier,
    app_profile,
    constant_time_equals,
    fixed_clock,
    identify_hash,
)

# audit_designer (passlib 1.7.4) hash of "geheim123", see tests/fixtures.
LEGACY_BCRYPT = "$2b$12$tykvNDpREeaFzESOYJImI.kzQ1zN4yEwmBO6UHdoYyoYK7TmEubSO"
KEY = "installed-smoke-secret-0123456789abcdef"


def expect_backend(call: object, module: str) -> None:
    if find_spec(module) is None:
        try:
            call()  # type: ignore[operator]
        except BackendUnavailableError as error:
            assert error.extra, error
        else:
            raise AssertionError(f"{module} missing but no BackendUnavailableError")
    else:
        call()  # type: ignore[operator]


def main() -> None:
    package = distribution("auditcore_auth")
    assert package.version == "0.1.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == []
    assert find_spec("auditcore") is None
    assert len(APP_PROFILES) == 9
    assert app_profile("regulierung").token("refresh").lifetime == timedelta(days=7)
    assert app_profile("versteigerung").password is ARGON2ID
    assert identify_hash(LEGACY_BCRYPT).scheme is HashScheme.BCRYPT  # type: ignore[union-attr]
    assert identify_hash("$2b$12$short") is None
    assert constant_time_equals("Prüfung", "Prüfung") and not constant_time_equals("a", "b")
    try:
        TokenProfile("bad", lifetime=timedelta(minutes=5), algorithm="none",
                     accepted_algorithms=("none",))
    except ConfigurationError:
        pass
    else:
        raise AssertionError("alg=none accepted")

    def legacy_login() -> None:
        assert PasswordHasher(BCRYPT).verify("geheim123", LEGACY_BCRYPT)
        assert not PasswordHasher(ARGON2ID).verify("falsch", LEGACY_BCRYPT)

    expect_backend(legacy_login, "bcrypt")
    now = datetime(2026, 9, 25, 12, tzinfo=UTC)

    def roundtrip() -> None:
        issued = TokenIssuer(DEFAULT_TOKEN_PROFILE, KEY, clock=fixed_clock(now)).issue(subject="7")
        verifier = TokenVerifier(DEFAULT_TOKEN_PROFILE, KEY, clock=fixed_clock(now))
        assert verifier.verify(issued.token).subject == "7"

    expect_backend(roundtrip, "jwt")


if __name__ == "__main__":
    main()
