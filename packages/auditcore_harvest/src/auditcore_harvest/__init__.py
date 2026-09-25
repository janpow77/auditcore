"""Shared harvest core: contracts, engine, ports, transports and adapter contract tests.

Public API of contract version 1 (``CONTRACT_VERSION``). Source adapters live
in their family packages and depend on this core, not the other way round.
"""

from .adapter import AdapterRegistry, FetchContext, SourceAdapter, require
from .engine import CancelToken, HarvestEngine, RateLimit, RetryPolicy
from .errors import (
    AuthError,
    Cancelled,
    CheckpointConflict,
    ConfigError,
    HarvestError,
    LimitReached,
    ParserError,
    RateLimitError,
    SinkError,
    TransportError,
)
from .model import (
    CONTRACT_VERSION,
    AuthKind,
    Capabilities,
    Checkpoint,
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
from .transport import FileTransport, ReplayTransport, decode_json, raise_for_status

__version__ = "0.1.1"

__all__ = [
    "CONTRACT_VERSION",
    "AdapterRegistry",
    "AuthError",
    "AuthKind",
    "Cancelled",
    "CancelToken",
    "Capabilities",
    "Checkpoint",
    "CheckpointConflict",
    "Clock",
    "ConfigError",
    "CredentialProvider",
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
    "Sink",
    "SinkError",
    "SinkReceipt",
    "Sleeper",
    "SnapshotSemantics",
    "Source",
    "SourceAdapter",
    "StateStore",
    "Transport",
    "TransportError",
    "__version__",
    "canonical_hash",
    "decode_json",
    "page_result",
    "raise_for_status",
    "require",
]
