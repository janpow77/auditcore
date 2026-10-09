"""Shared harvest core: contracts, engine, ports, transports and adapter contract tests.

Public API of contract version 1 (``CONTRACT_VERSION``). Source adapters live
in their family packages and depend on this core, not the other way round.
The asynchronous, abortable engine lives in :mod:`auditcore_harvest.aio`
(imported explicitly, because it loads :mod:`asyncio`).
"""

from .adapter import AdapterRegistry, FetchContext, SourceAdapter, require
from .content import BinaryContent
from .crawl import AsyncCrawlAdapter, CrawlAdapter, CrawlLimits, CrawlTask, StageResult
from .engine import CancelToken, HarvestEngine, RateLimit, RetryPolicy
from .errors import (
    AuthError,
    Cancelled,
    CheckpointConflict,
    ConfigError,
    ErrorKind,
    HarvestError,
    LimitReached,
    ParserError,
    RateLimitError,
    SinkError,
    TransportError,
)
from .model import (
    CONTRACT_VERSION,
    JSON,
    AuthKind,
    Capabilities,
    Checkpoint,
    Cursor,
    HarvestRecord,
    HarvestRequest,
    HarvestResult,
    PageResult,
    PageStatus,
    Provenance,
    RecordIssue,
    RunStatus,
    SinkReceipt,
    SnapshotSemantics,
    Source,
    canonical_hash,
    page_result,
)
from .ports import (
    Clock,
    CredentialProvider,
    EventSink,
    Response,
    Sink,
    Sleeper,
    StateStore,
    Transport,
)
from .session import CookieSession, SessionTransport
from .transport import (
    FileTransport,
    ReplayTransport,
    StatusPolicy,
    decode_json,
    raise_for_status,
)

__version__ = "0.2.0"

__all__ = [
    "CONTRACT_VERSION",
    "JSON",
    "AdapterRegistry",
    "AsyncCrawlAdapter",
    "AuthError",
    "AuthKind",
    "BinaryContent",
    "Cancelled",
    "CancelToken",
    "Capabilities",
    "Checkpoint",
    "CheckpointConflict",
    "Clock",
    "ConfigError",
    "CookieSession",
    "CrawlAdapter",
    "CrawlLimits",
    "CrawlTask",
    "CredentialProvider",
    "Cursor",
    "ErrorKind",
    "EventSink",
    "FetchContext",
    "FileTransport",
    "HarvestEngine",
    "HarvestError",
    "HarvestRecord",
    "HarvestRequest",
    "HarvestResult",
    "LimitReached",
    "PageResult",
    "PageStatus",
    "ParserError",
    "Provenance",
    "RateLimit",
    "RateLimitError",
    "RecordIssue",
    "ReplayTransport",
    "Response",
    "RetryPolicy",
    "RunStatus",
    "SessionTransport",
    "Sink",
    "SinkError",
    "SinkReceipt",
    "Sleeper",
    "SnapshotSemantics",
    "Source",
    "SourceAdapter",
    "StageResult",
    "StateStore",
    "StatusPolicy",
    "Transport",
    "TransportError",
    "__version__",
    "canonical_hash",
    "decode_json",
    "page_result",
    "raise_for_status",
    "require",
]
