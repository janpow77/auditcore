"""Optional FastAPI integration: a Bearer-token dependency (extra ``fastapi``).

FastAPI is imported only when :func:`bearer_dependency` is called. The module
deliberately has no ``from __future__ import annotations``: FastAPI reads the
parameter annotations of the returned dependency at runtime.
"""

from collections.abc import Awaitable, Callable

from .errors import BackendUnavailableError, TokenError
from .tokens import TokenVerifier, VerifiedToken

MISSING_DETAIL = "Anmeldung erforderlich"
INVALID_DETAIL = "Anmeldung ungültig oder abgelaufen"


def challenge(realm: str | None = None, error: str | None = None) -> str:
    """``WWW-Authenticate`` value per RFC 6750 section 3."""
    parameters = []
    if realm:
        parameters.append(f'realm="{realm}"')
    if error:
        parameters.append(f'error="{error}"')
    return "Bearer" + (" " + ", ".join(parameters) if parameters else "")


def bearer_dependency(
    verifier: TokenVerifier,
    *,
    expected_type: str | None = None,
    realm: str | None = None,
    scheme_name: str = "Bearer",
    missing_detail: str = MISSING_DETAIL,
    invalid_detail: str = INVALID_DETAIL,
) -> Callable[..., Awaitable[VerifiedToken]]:
    """Build a FastAPI dependency that returns the :class:`VerifiedToken`.

    Missing or non-Bearer credentials and every rejected token answer 401 with
    ``WWW-Authenticate``; the rejection reason is not disclosed to the client.
    """
    try:
        from fastapi import Depends, HTTPException, status
        from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    except ImportError:
        raise BackendUnavailableError("fastapi", "fastapi") from None

    scheme = HTTPBearer(auto_error=False, scheme_name=scheme_name)

    def unauthorized(detail: str, error: str | None) -> Exception:
        response: Exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": challenge(realm, error)},
        )
        return response

    async def dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(scheme),  # noqa: B008
    ) -> VerifiedToken:
        if credentials is None or not credentials.credentials:
            raise unauthorized(missing_detail, None)
        try:
            return verifier.verify(credentials.credentials, expected_type=expected_type)
        except TokenError:
            raise unauthorized(invalid_detail, "invalid_token") from None

    return dependency
