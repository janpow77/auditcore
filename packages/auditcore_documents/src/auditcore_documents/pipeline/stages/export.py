"""Export zu nachgelagerten Systemen (aus ``stages/export.py``).

Ziele sind austauschbar. ``WebhookExport`` benutzt einen injizierten
``post``-Port (HTTP-Fehler als ``WebhookError``); ``FileExport`` schreibt
JSON/CSV wie das Original, jedoch ausdrücklich in UTF-8 (PL-C07).
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Protocol

from auditcore_documents.pipeline.context import PipelineContext
from auditcore_documents.pipeline.stages.base import PipelineStage, StageError


class WebhookError(Exception):
    """HTTP-Fehler des Webhook-Ports (im Original ``httpx.HTTPError``)."""


Poster = Callable[[str, dict[str, Any], dict[str, str], float], Awaitable[tuple[int, str]]]


class ExportTarget(Protocol):
    name: str
    enabled: bool

    async def export(self, context: PipelineContext) -> dict[str, Any]: ...


def webhook_payload(context: PipelineContext) -> dict[str, Any]:
    return {
        "event": "pipeline_completed",
        "run_id": context.run_id,
        "document_id": context.document_id,
        "status": context.status.value,
        "hash_original": context.hash_original,
        "extracted_fields": context.artifacts.extracted_fields,
        "validation_flags": context.validation_flags,
        "completed_at": context.completed_at.isoformat() if context.completed_at else None,
    }


class WebhookExport:
    name = "webhook"
    enabled = True

    def __init__(
        self, url: str, post: Poster, headers: dict[str, str] | None = None, timeout: int = 30
    ) -> None:
        self.url = url
        self.post = post
        self.headers = headers or {}
        self.timeout = timeout

    async def export(self, context: PipelineContext) -> dict[str, Any]:
        try:
            status_code, text = await self.post(
                self.url,
                webhook_payload(context),
                {"Content-Type": "application/json", **self.headers},
                float(self.timeout),
            )
        except WebhookError as exc:
            return {"success": False, "error": str(exc), "url": self.url}
        return {"success": True, "status_code": status_code, "response": text[:500]}


def file_export_content(context: PipelineContext, fmt: str) -> str | None:
    if fmt == "json":
        return json.dumps(
            {
                "run_id": context.run_id,
                "document_id": context.document_id,
                "status": context.status.value,
                "extracted_fields": context.artifacts.extracted_fields,
                "validation_results": [r.to_dict() for r in context.validation_results],
            },
            indent=2,
            default=str,
        )
    if fmt == "csv":
        fields = context.artifacts.extracted_fields or {}
        return ",".join(fields.keys()) + "\n" + ",".join(str(v) for v in fields.values())
    return None


class FileExport:
    name = "file"
    enabled = True

    def __init__(self, output_dir: str | Path, format: str = "json") -> None:  # noqa: A002
        self.output_dir = str(output_dir)
        self.format = format

    async def export(self, context: PipelineContext) -> dict[str, Any]:
        output_path = Path(self.output_dir) / f"{context.run_id}.{self.format}"
        try:
            content = file_export_content(context, self.format)
            if content is None:
                return {"success": False, "error": f"Unknown format: {self.format}"}
            output_path.write_text(content, encoding="utf-8")
            return {
                "success": True,
                "path": str(output_path),
                "format": self.format,
                "size_bytes": len(content),
            }
        except Exception as exc:  # noqa: BLE001 - Originalvertrag
            return {"success": False, "error": str(exc), "path": str(output_path)}


class ExportStage(PipelineStage):
    name = "export"
    description = "Export to downstream systems"

    def __init__(
        self,
        *args: object,
        targets: list[ExportTarget] | None = None,
        fail_on_error: bool = False,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.targets = targets or []
        self.fail_on_error = fail_on_error

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        if not self.targets:
            return context
        results: list[dict[str, Any]] = []
        for target in self.targets:
            if not target.enabled:
                continue
            try:
                result = await target.export(context)
                result["target"] = target.name
                results.append(result)
                if not result.get("success") and self.fail_on_error:
                    raise StageError(
                        stage=self.name,
                        error_code="EXPORT_FAILED",
                        message=f"Export to {target.name} failed: {result.get('error')}",
                        recoverable=True,
                        details=result,
                    )
            except StageError:
                raise
            except Exception as exc:  # noqa: BLE001 - Originalvertrag
                results.append({"target": target.name, "success": False, "error": str(exc)})
                if self.fail_on_error:
                    raise StageError(
                        stage=self.name,
                        error_code="EXPORT_ERROR",
                        message=f"Export to {target.name} raised exception: {exc}",
                        recoverable=True,
                    ) from exc
        if self.audit is not None:
            await self.audit.log_event(
                event_type="EXPORTED",
                document_id=context.document_id,
                run_id=context.run_id,
                hash_original=context.hash_original,
                details={
                    "targets": [t.name for t in self.targets if t.enabled],
                    "results": results,
                    "success_count": sum(1 for r in results if r.get("success")),
                    "failure_count": sum(1 for r in results if not r.get("success")),
                },
            )
        return context
