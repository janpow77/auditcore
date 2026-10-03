"""Gateway concurrency preserves the established page and error contracts."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from auditcore_documents.pipeline.stages.base import StageError
from auditcore_documents.pipeline.stages.ocr import OcrRouting, OcrStage, RouterResult
from auditcore_documents.pipeline.stages.ocr_parallel import recognize_pages


class Router:
    def __init__(self, *, fail_all: bool = False) -> None:
        self.active = 0
        self.peak = 0
        self.finished: list[int] = []
        self.fail_all = fail_all

    async def __call__(
        self, data: bytes, *, filename: str, model: str, language: str
    ) -> tuple[RouterResult | None, str | None]:
        page = int(data)
        assert filename == f"invoice-{page}.png"
        assert model == "auto" and language == "deu+eng"
        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            for _ in range(6 if page == 1 else 1):
                await asyncio.sleep(0)
            self.finished.append(page)
            if page == 3 or self.fail_all:
                return None, "unavailable"
            return RouterResult(text=f"Seite {page}", confidence=page / 10, model="ocr"), None
        finally:
            self.active -= 1


PAGES = [(i, str(i).encode()) for i in range(1, 9)]


def result(router: Router, concurrency: int, *, outage_error: bool = False) -> dict:
    stage = OcrStage(
        routing=OcrRouting(max_concurrent_pages=concurrency),
        timer=lambda: 0,
        gateway_outage_is_error=outage_error,
    )
    return asyncio.run(stage._router_pages(router, Path("invoice.pdf"), PAGES, 0))


def test_parallel_pages_equal_sequential_including_partial_failure() -> None:
    sequential, parallel = Router(), Router()
    assert result(parallel, 2) == result(sequential, 1)
    assert parallel.peak == 2 and sequential.peak == 1
    assert parallel.active == 0 and parallel.finished[0] != 1


@pytest.mark.parametrize("concurrency", [1, 4])
def test_all_failed_pages_preserve_degraded_and_retry_contract(concurrency: int) -> None:
    output = result(Router(fail_all=True), concurrency)
    assert output["pages_failed"] == len(PAGES) and output["pages_processed"] == 0
    with pytest.raises(StageError) as caught:
        result(Router(fail_all=True), concurrency, outage_error=True)
    assert caught.value.error_code == "OCR_GATEWAY_UNAVAILABLE"
    assert caught.value.recoverable


@pytest.mark.parametrize("cancel", [False, True])
def test_exception_and_caller_cancellation_drain_sibling_requests(cancel: bool) -> None:
    async def run() -> None:
        started = asyncio.Event()
        stopped: list[int] = []

        async def router(data: bytes, **kwargs: str) -> tuple[RouterResult | None, str | None]:
            page = int(data)
            try:
                if page == 1:
                    await started.wait()
                    if not cancel:
                        raise RuntimeError("transport")
                else:
                    started.set()
                await asyncio.Event().wait()
                return None, None
            finally:
                stopped.append(page)

        task = asyncio.create_task(
            recognize_pages(router, PAGES, "invoice", OcrRouting(max_concurrent_pages=2))
        )
        await asyncio.wait_for(started.wait(), 2)
        if cancel:
            task.cancel()
        with pytest.raises(asyncio.CancelledError if cancel else RuntimeError):
            await asyncio.wait_for(task, 2)
        assert sorted(stopped) == [1, 2]

    asyncio.run(run())


@pytest.mark.parametrize("value", [0, -1, 51, True, 1.5])
def test_invalid_concurrency_is_rejected(value: object) -> None:
    with pytest.raises((TypeError, ValueError), match="max_concurrent_pages"):
        OcrRouting(max_concurrent_pages=value)
