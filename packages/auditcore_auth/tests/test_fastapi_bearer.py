"""FastAPI extra: Bearer dependency, 401 with WWW-Authenticate, no reason disclosure."""

from __future__ import annotations

from datetime import timedelta

import pytest
from conftest import FAST_TOKEN, KEY, NOW

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from auditcore_auth import TokenIssuer, TokenVerifier, VerifiedToken, fixed_clock  # noqa: E402
from auditcore_auth.fastapi_bearer import bearer_dependency, challenge  # noqa: E402


def client(expected_type: str | None = None) -> TestClient:
    verifier = TokenVerifier(FAST_TOKEN, KEY, clock=fixed_clock(NOW))
    current = bearer_dependency(verifier, expected_type=expected_type, realm="auditcore")
    app = fastapi.FastAPI()

    @app.get("/me")
    async def me(token: VerifiedToken = fastapi.Depends(current)) -> dict[str, object]:  # noqa: B008
        return {"sub": token.subject}

    return TestClient(app)


def token(**claims: object) -> str:
    return TokenIssuer(FAST_TOKEN, KEY, clock=fixed_clock(NOW)).issue(claims, subject="7").token


def test_valid_bearer_token() -> None:
    response = client().get("/me", headers={"Authorization": f"Bearer {token()}"})
    assert response.status_code == 200 and response.json() == {"sub": "7"}


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Basic dXNlcjpwdw=="},
                                     {"Authorization": "Bearer"}])
def test_missing_credentials(headers: dict[str, str]) -> None:
    response = client().get("/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Bearer realm="auditcore"'
    assert response.json() == {"detail": "Anmeldung erforderlich"}


def test_invalid_token_does_not_disclose_the_reason() -> None:
    expired = TokenIssuer(FAST_TOKEN, KEY, clock=fixed_clock(NOW - timedelta(hours=1))).issue(
        subject="7").token
    for value in (expired, "abc", token() + "x"):
        response = client().get("/me", headers={"Authorization": f"Bearer {value}"})
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == (
            'Bearer realm="auditcore", error="invalid_token"')
        assert response.json() == {"detail": "Anmeldung ungültig oder abgelaufen"}


def test_expected_type() -> None:
    wrong = client(expected_type="access").get(
        "/me", headers={"Authorization": f"Bearer {token(type='refresh')}"})
    assert wrong.status_code == 401
    right = client(expected_type="access").get(
        "/me", headers={"Authorization": f"Bearer {token(type='access')}"})
    assert right.status_code == 200


def test_openapi_declares_the_bearer_scheme() -> None:
    schema = client().get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["Bearer"]["scheme"] == "bearer"


def test_challenge_without_parameters() -> None:
    assert challenge() == "Bearer"
