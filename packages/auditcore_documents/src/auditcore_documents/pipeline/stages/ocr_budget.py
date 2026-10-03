"""Shared gateway admission for several documents in one event loop."""

from __future__ import annotations

import asyncio

from .ocr_results import RouterOcr, RouterResult


class LimitedRouterOcr:
    """Share one instance across document jobs to limit total in-flight requests.

    This is a budget for one event loop, not a distributed semaphore. The
    application must divide gateway capacity between its worker processes
    or enforce the overall limit at the gateway. No extra HTTP client is
    created; the wrapped port retains its connection pool and retry policy.
    """

    def __init__(self, router: RouterOcr, max_concurrent_requests: int) -> None:
        if isinstance(max_concurrent_requests, bool) or not isinstance(
            max_concurrent_requests, int
        ):
            raise TypeError("max_concurrent_requests muss eine ganze Zahl sein.")
        if max_concurrent_requests < 1:
            raise ValueError("max_concurrent_requests muss positiv sein.")
        self._router = router
        self._semaphore = asyncio.BoundedSemaphore(max_concurrent_requests)
        self._loop: asyncio.AbstractEventLoop | None = None

    async def __call__(
        self, data: bytes, *, filename: str, model: str, language: str
    ) -> tuple[RouterResult | None, str | None]:
        loop = asyncio.get_running_loop()
        if self._loop is not None and self._loop is not loop:
            raise RuntimeError("LimitedRouterOcr muss je Eventloop angelegt werden.")
        self._loop = loop
        async with self._semaphore:
            return await self._router(data, filename=filename, model=model, language=language)
