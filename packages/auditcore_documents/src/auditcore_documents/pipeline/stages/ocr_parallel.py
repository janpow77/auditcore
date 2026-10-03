"""Bounded gateway requests with ordered results and complete cancellation."""

from __future__ import annotations

import asyncio

from .ocr_results import OcrRouting, RouterOcr, RouterResult


async def recognize_pages(
    router: RouterOcr,
    pages: list[tuple[int, bytes]],
    stem: str,
    routing: OcrRouting,
) -> list[tuple[RouterResult | None, str | None]]:
    """Keep input order; at most ``max_concurrent_pages`` calls run per document.

    Only gateway calls overlap. Rasterization and local OCR remain sequential.
    A returned page error is data; a raised exception cancels all sibling calls.
    """
    results: list[tuple[RouterResult | None, str | None]] = [(None, None)] * len(pages)
    pending = iter(enumerate(pages))

    async def worker() -> None:
        for index, (page_no, png) in pending:
            results[index] = await router(
                png,
                filename=f"{stem or 'seite'}-{page_no}.png",
                model="auto",
                language=routing.languages,
            )

    tasks = [
        asyncio.create_task(worker()) for _ in range(min(routing.max_concurrent_pages, len(pages)))
    ]
    try:
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    return results
