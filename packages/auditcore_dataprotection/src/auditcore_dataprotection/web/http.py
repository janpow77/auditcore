"""Starlette binding of the REST contract (extra ``web``).

``routes(api, identify)`` returns the endpoints for mounting into an existing
Starlette application, ``create_app`` a standalone application. The library
does not authenticate: ``identify`` maps a request to the tenant and person
(:class:`~.contract.Principal`) or returns ``None`` (answer 401). Write
requests must be ``application/json``, which keeps plain HTML forms of other
origins out; consumers with session cookies add their own CSRF check.
Starlette is imported lazily so that ``auditcore_dataprotection.web`` works
without the extra.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from ..errors import DataProtectionError
from .contract import ApiError, JsonObject, Principal, library_error
from .export import ExportFile
from .service import DataProtectionApi

if TYPE_CHECKING:
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Route

Identify = Callable[["Request"], "Principal | None | Awaitable[Principal | None]"]
Answer = JsonObject | ExportFile
Call = Callable[..., Answer]
Handler = Callable[["Request", Principal], Awaitable[Answer]]
Endpoint = Callable[["Request"], Awaitable["Response"]]

#: Upper bound of a request body in bytes (the register itself allows 5 MiB).
MAX_BODY_BYTES = 6 * 1024 * 1024


_UNRESERVED = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")


def _rfc5987(value: str) -> str:
    return "".join(chr(b) if b in _UNRESERVED else f"%{b:02X}" for b in value.encode("utf-8"))


def _attachment(filename: str) -> str:
    ascii_name = filename.encode("ascii", "replace").decode("ascii").replace("?", "_")
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{_rfc5987(filename)}"


def _respond(answer: Answer, status: int) -> Response:
    from starlette.responses import JSONResponse, Response

    if isinstance(answer, ExportFile):
        headers = {
            "Content-Disposition": _attachment(answer.filename),
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        }
        return Response(answer.content, media_type=answer.media_type, headers=headers)
    return JSONResponse(answer, status_code=status)


async def _principal(request: Request, identify: Identify) -> Principal:
    found = identify(request)
    principal = await found if inspect.isawaitable(found) else found
    if not isinstance(principal, Principal):
        raise ApiError(401, "unauthenticated", "Anmeldung erforderlich.")
    return principal


async def read_json(request: Request, max_bytes: int = MAX_BODY_BYTES) -> object:
    """JSON body with content type and size checks."""
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type != "application/json":
        raise ApiError(415, "unsupported_media_type", "Anfragen sind als JSON zu senden.")
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > max_bytes:
        raise ApiError(413, "body_too_large", "Die Anfrage ist zu groß.")
    raw = await request.body()
    if len(raw) > max_bytes:
        raise ApiError(413, "body_too_large", "Die Anfrage ist zu groß.")
    try:
        return json.loads(raw or b"null")
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ApiError(400, "invalid_json", "Die Anfrage ist kein gültiges JSON.") from None


def _endpoint(handler: Handler, identify: Identify, status: int = 200) -> Endpoint:
    from starlette.responses import JSONResponse

    async def endpoint(request: Request) -> Response:
        try:
            principal = await _principal(request, identify)
            return _respond(await handler(request, principal), status)
        except DataProtectionError as exc:
            error = library_error(exc)
            return JSONResponse(error.to_dict(), status_code=error.status)
        except ApiError as exc:
            return JSONResponse(exc.to_dict(), status_code=exc.status)

    endpoint.__name__ = handler.__name__
    endpoint.__doc__ = handler.__doc__
    return endpoint


class _Handlers:
    """Request → service call, run in the thread pool (repositories may block)."""

    def __init__(self, api: DataProtectionApi, max_body_bytes: int) -> None:
        self.api = api
        self.max_body_bytes = max_body_bytes

    async def _call(self, function: Call, *args: object) -> Answer:
        from starlette.concurrency import run_in_threadpool

        result: Answer = await run_in_threadpool(function, *args)
        return result

    async def _with_body(self, request: Request, function: Call, *args: object) -> Answer:
        body = await read_json(request, self.max_body_bytes)
        return await self._call(function, *args, body)

    async def profile(self, request: Request, who: Principal) -> Answer:
        """Rule profile of the forms."""
        return await self._call(self.api.profile_info)

    async def calculate(self, request: Request, who: Principal) -> Answer:
        """Proposal for unsaved answers and scenarios."""
        return await self._with_body(request, self.api.calculate)

    async def register(self, request: Request, who: Principal) -> Answer:
        """Draft, release and history of the register."""
        return await self._call(self.api.register, who)

    async def check(self, request: Request, who: Principal) -> Answer:
        """Content check of unsaved content."""
        return await self._with_body(request, self.api.check_register, who)

    async def draft(self, request: Request, who: Principal) -> Answer:
        """Save the draft."""
        return await self._with_body(request, self.api.save_draft, who)

    async def release_register(self, request: Request, who: Principal) -> Answer:
        """Release the draft (four eyes)."""
        return await self._with_body(request, self.api.release_register, who)

    async def export_register(self, request: Request, who: Principal) -> Answer:
        """Export the register."""
        return await self._with_body(request, self.api.export_register, who)

    async def overview(self, request: Request, who: Principal) -> Answer:
        """Activities with the state of their newest DPIA."""
        return await self._call(self.api.overview, who, request.query_params.get("department"))

    async def start(self, request: Request, who: Principal) -> Answer:
        """Start an assessment."""
        return await self._with_body(request, self.api.start, who)

    async def assessment(self, request: Request, who: Principal) -> Answer:
        """Read an assessment."""
        return await self._call(self.api.assessment, who, request.path_params["assessment_id"])

    async def _action(self, request: Request, who: Principal, function: Call) -> Answer:
        return await self._with_body(request, function, who, request.path_params["assessment_id"])

    async def update(self, request: Request, who: Principal) -> Answer:
        """Change the survey of an assessment."""
        return await self._action(request, who, self.api.update)

    async def decide(self, request: Request, who: Principal) -> Answer:
        """Decide on the proposal."""
        return await self._action(request, who, self.api.decide)

    async def dpo_request(self, request: Request, who: Principal) -> Answer:
        """Document the request for the DPO's advice."""
        return await self._action(request, who, self.api.dpo_request)

    async def release(self, request: Request, who: Principal) -> Answer:
        """Release an assessment (four eyes)."""
        return await self._action(request, who, self.api.release)

    async def reassess(self, request: Request, who: Principal) -> Answer:
        """New version from a released assessment."""
        return await self._call(self.api.reassess, who, request.path_params["assessment_id"])

    async def export_assessment(self, request: Request, who: Principal) -> Answer:
        """Export an assessment."""
        return await self._action(request, who, self.api.export_assessment)


def endpoints(
    api: DataProtectionApi, identify: Identify, max_body_bytes: int = MAX_BODY_BYTES
) -> list[tuple[str, str, Endpoint]]:
    """(path, method, endpoint) relative to the mount point."""
    h = _Handlers(api, max_body_bytes)
    one = "/assessments/{assessment_id}"
    table: list[tuple[str, str, Handler, int]] = [
        ("/profile", "GET", h.profile, 200),
        ("/calculate", "POST", h.calculate, 200),
        ("/register", "GET", h.register, 200),
        ("/register/check", "POST", h.check, 200),
        ("/register/draft", "POST", h.draft, 200),
        ("/register/release", "POST", h.release_register, 200),
        ("/register/export", "POST", h.export_register, 200),
        ("/assessments", "GET", h.overview, 200),
        ("/assessments", "POST", h.start, 201),
        (one, "GET", h.assessment, 200),
        (one, "POST", h.update, 200),
        (f"{one}/decide", "POST", h.decide, 200),
        (f"{one}/dpo-request", "POST", h.dpo_request, 200),
        (f"{one}/release", "POST", h.release, 200),
        (f"{one}/reassess", "POST", h.reassess, 201),
        (f"{one}/export", "POST", h.export_assessment, 200),
    ]
    return [(path, method, _endpoint(fn, identify, status)) for path, method, fn, status in table]


def routes(
    api: DataProtectionApi, identify: Identify, max_body_bytes: int = MAX_BODY_BYTES
) -> list[Route]:
    """Starlette routes for ``Mount("/api/dataprotection", routes=...)``."""
    from starlette.routing import Route

    return [
        Route(path, endpoint, methods=[method])
        for path, method, endpoint in endpoints(api, identify, max_body_bytes)
    ]


def create_app(
    api: DataProtectionApi,
    *,
    identify: Identify,
    prefix: str = "",
    max_body_bytes: int = MAX_BODY_BYTES,
) -> Starlette:
    """Standalone Starlette application with the API under ``prefix`` (``""`` = root)."""
    from starlette.applications import Starlette
    from starlette.routing import Mount

    inner = routes(api, identify, max_body_bytes)
    return Starlette(routes=[Mount(prefix, routes=inner)] if prefix else inner)
