"""A shared OCR port limits all document jobs, including cancelled waiters."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from test_ocr_parallel import PAGES, Router

from auditcore_documents.pipeline import LimitedRouterOcr, OcrRouting, OcrStage, RouterResult


def test_shared_budget_limits_several_documents() -> None:
    async def run() -> None:
        router = Router()
        limited = LimitedRouterOcr(router, 2)
        stages = [
            OcrStage(routing=OcrRouting(max_concurrent_pages=4), timer=lambda: 0) for _ in range(3)
        ]
        results = await asyncio.gather(
            *(stage._router_pages(limited, Path("invoice.pdf"), PAGES, 0) for stage in stages)
        )
        assert results[0] == results[1] == results[2]
        assert router.peak == 2 and router.active == 0
        assert len(router.finished) == len(PAGES) * 3

    asyncio.run(run())


def test_cancelled_waiter_does_not_steal_a_slot() -> None:
    async def run() -> None:
        started, release = asyncio.Event(), asyncio.Event()
        calls = []

        async def router(data: bytes, **kwargs: str) -> tuple[RouterResult | None, str | None]:
            calls.append(data)
            started.set()
            await release.wait()
            return RouterResult(text=data.decode()), None

        limited = LimitedRouterOcr(router, 1)
        options = {"filename": "invoice.png", "model": "auto", "language": "auto"}
        first = asyncio.create_task(limited(b"first", **options))
        await asyncio.wait_for(started.wait(), 2)
        waiter = asyncio.create_task(limited(b"cancelled", **options))
        await asyncio.sleep(0)
        waiter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiter
        release.set()
        await first
        await asyncio.wait_for(limited(b"next", **options), 2)
        assert calls == [b"first", b"next"]

    asyncio.run(run())


def test_budget_rejects_other_event_loop() -> None:
    limited = LimitedRouterOcr(Router(), 1)
    options = {"filename": "invoice-1.png", "model": "auto", "language": "deu+eng"}
    asyncio.run(limited(b"1", **options))
    with pytest.raises(RuntimeError, match="Eventloop"):
        asyncio.run(limited(b"1", **options))


@pytest.mark.parametrize("limit", [True, 1.5, 0, -1])
def test_invalid_budget(limit: object) -> None:
    with pytest.raises((TypeError, ValueError), match="max_concurrent_requests"):
        LimitedRouterOcr(Router(), limit)
