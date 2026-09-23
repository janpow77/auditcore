"""Einlesen, MIME-Prüfung, Größe, SHA-256 und Metadaten (aus ``stages/ingestion.py``).

Ports: ``fetch_url`` (HTTP(S)-Abruf, z. B. über ``auditcore_harvest``),
``mime_detector`` (Vorgabe: reine Signaturerkennung; ``libmagic_detector``
nutzt wie das Original python-magic), ``page_counter`` (Vorgabe pypdf wie im
Original, 0 bei jedem Fehler) und ``clock`` für den Speicherschlüssel.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from io import BytesIO
from pathlib import Path

from auditcore_documents.pipeline.context import PipelineContext
from auditcore_documents.pipeline.stages.base import PipelineStage, StageError

FetchUrl = Callable[[str], Awaitable[bytes]]
MimeDetector = Callable[[bytes], str]
PageCounter = Callable[[bytes], int]

ALLOWED_MIME_TYPES = frozenset(
    {"application/pdf", "image/png", "image/jpeg", "image/tiff", "image/webp"}
)
MAX_FILE_SIZE = 100 * 1024 * 1024


def sniff_mime(data: bytes) -> str:
    """Signaturerkennung ohne libmagic für die zulässigen Typen (PL-C04)."""
    head = data[:16]
    if head.startswith(b"%PDF"):
        return "application/pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith((b"II*\x00", b"MM\x00*")):
        return "image/tiff"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return "application/octet-stream"


def libmagic_detector(data: bytes) -> str:
    """Originalverhalten: ``magic.from_buffer``; bei Fehler %PDF-Rückfall (Extra ``mime``)."""
    try:
        import magic

        return str(magic.from_buffer(data, mime=True))
    except Exception:  # noqa: BLE001 - Originalvertrag
        return "application/pdf" if data[:4] == b"%PDF" else "application/octet-stream"


def pypdf_page_count(data: bytes) -> int:
    """Seitenzahl mit pypdf; jeder Fehler (auch fehlendes pypdf) ergibt 0."""
    try:
        import pypdf

        return len(pypdf.PdfReader(BytesIO(data)).pages)
    except Exception:  # noqa: BLE001 - Originalvertrag
        return 0


class IngestionStage(PipelineStage):
    name = "ingestion"
    description = "Document upload and initial hashing"
    ALLOWED_MIME_TYPES = ALLOWED_MIME_TYPES
    MAX_FILE_SIZE = MAX_FILE_SIZE

    def __init__(
        self,
        *args: object,
        fetch_url: FetchUrl | None = None,
        mime_detector: MimeDetector = sniff_mime,
        page_counter: PageCounter = pypdf_page_count,
        local_time: Callable[[], datetime] = datetime.now,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.fetch_url = fetch_url
        self.mime_detector = mime_detector
        self.page_counter = page_counter
        self.local_time = local_time

    async def execute(self, context: PipelineContext) -> PipelineContext:
        self.validate_context(context)
        input_path = context.input_uri
        if not input_path:
            raise StageError(
                stage=self.name,
                error_code="MISSING_INPUT",
                message="input_uri is required",
                recoverable=False,
            )
        document_bytes = await self._load_document(input_path)
        mime_type = self.mime_detector(document_bytes)
        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise StageError(
                stage=self.name,
                error_code="INVALID_MIME_TYPE",
                message=f"Unsupported file type: {mime_type}",
                recoverable=False,
                details={"mime_type": mime_type, "allowed": sorted(self.ALLOWED_MIME_TYPES)},
            )
        file_size = len(document_bytes)
        if file_size > self.MAX_FILE_SIZE:
            raise StageError(
                stage=self.name,
                error_code="FILE_TOO_LARGE",
                message=f"File size {file_size} exceeds maximum {self.MAX_FILE_SIZE}",
                recoverable=False,
                details={"file_size": file_size, "max_size": self.MAX_FILE_SIZE},
            )
        if self.hashing is not None:
            context.hash_original = self.hashing.hash_bytes(document_bytes)
        context.artifacts.file_size_bytes = file_size
        context.artifacts.mime_type = mime_type
        if mime_type == "application/pdf":
            context.artifacts.page_count = self.page_counter(document_bytes)
        if not context.storage_key:
            context.storage_key = self.storage_key(context)
        return context

    async def _load_document(self, input_path: str) -> bytes:
        if input_path.startswith("/") or input_path.startswith("file://"):
            raw_path = input_path.replace("file://", "")
            path = Path(raw_path)
            if not path.exists():
                raise StageError(
                    stage=self.name,
                    error_code="FILE_NOT_FOUND",
                    message=f"File not found: {raw_path}",
                    recoverable=False,
                )
            if path.stat().st_size > self.MAX_FILE_SIZE:
                # PL-C03: nicht erst vollständig einlesen, dann prüfen.
                raise StageError(
                    stage=self.name,
                    error_code="FILE_TOO_LARGE",
                    message=f"File size {path.stat().st_size} exceeds maximum {self.MAX_FILE_SIZE}",
                    recoverable=False,
                    details={"file_size": path.stat().st_size, "max_size": self.MAX_FILE_SIZE},
                )
            return path.read_bytes()
        if input_path.startswith("s3://"):
            raise StageError(
                stage=self.name,
                error_code="S3_NOT_IMPLEMENTED",
                message="S3 loading not yet implemented",
                recoverable=False,
            )
        if input_path.startswith(("http://", "https://")):
            if self.fetch_url is None:
                raise StageError(
                    stage=self.name,
                    error_code="HTTP_NOT_CONFIGURED",
                    message="No URL fetcher configured",
                    recoverable=False,
                )
            try:
                return await self.fetch_url(input_path)
            except Exception as exc:  # noqa: BLE001 - Port-Fehler → wiederholbar wie im Original
                raise StageError(
                    stage=self.name,
                    error_code="HTTP_DOWNLOAD_FAILED",
                    message=f"Failed to download from {input_path}: {exc}",
                    recoverable=True,
                    retry_after_sec=5,
                ) from exc
        raise StageError(
            stage=self.name,
            error_code="UNSUPPORTED_URI",
            message=f"Unsupported input URI scheme: {input_path}",
            recoverable=False,
        )

    def storage_key(self, context: PipelineContext) -> str:
        """``JJJJ/MM/TT/<document_id>/<run_id>`` in lokaler Zeit (wie im Original)."""
        return f"{self.local_time().strftime('%Y/%m/%d')}/{context.document_id}/{context.run_id}"
