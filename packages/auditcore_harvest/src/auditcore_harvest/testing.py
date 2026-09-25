"""Reusable adapter contract suite (contract version 1).

Adapter packages call :func:`check_adapter` (or :func:`assert_adapter` in
pytest) with a factory, a valid configuration and a factory for a
:class:`~auditcore_harvest.transport.ReplayTransport` built from recorded
fixtures. Every case runs through the real :class:`HarvestEngine`.

Cases: declaration, configuration, full replay, determinism, idempotent
re-run, resume after sink failure, resume after transport failure, malformed
response, missing credentials, secret-free events/results.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from .adapter import SourceAdapter
from .engine import HarvestEngine, RetryPolicy
from .errors import TransportError
from .memory import (
    ClockSleeper,
    FixedClock,
    ListEvents,
    ListSink,
    MemoryStateStore,
    StaticCredentials,
)
from .model import JSON, AuthKind, HarvestRequest, HarvestResult, RunStatus, SnapshotSemantics
from .ports import Response, Transport

AdapterFactory = Callable[[], SourceAdapter]
TransportFactory = Callable[[], Transport]


@dataclass
class FlakyTransport:
    """Fails the given call numbers with a retryable ``TransportError``."""

    inner: Transport
    fail_calls: frozenset[int]
    calls: int = 0

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        """Delegate or fail."""
        self.calls += 1
        if self.calls in self.fail_calls:
            raise TransportError("simulierter Netzwerkfehler")
        return self.inner.request(method, url, **kwargs)


@dataclass
class GarbageTransport:
    """Answers every request with a 200 response the adapter cannot parse."""

    body: bytes = b"\x00<<kein gueltiges Format>>"

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        """Garbage response."""
        return Response(200, self.body, {"content-type": "text/plain"}, url)


@dataclass
class ContractReport:
    """Outcome per case: ``PASS``, ``FAIL: reason`` or ``SKIPPED: reason``."""

    source_id: str
    cases: dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """True if no case failed."""
        return not any(v.startswith("FAIL") for v in self.cases.values())

    def to_dict(self) -> dict[str, JSON]:
        """JSON view."""
        return {"source_id": self.source_id, "passed": self.passed, "cases": dict(self.cases)}


def _engine(
    transport: Transport,
    credentials: StaticCredentials,
    state: MemoryStateStore | None = None,
    events: ListEvents | None = None,
) -> HarvestEngine:
    clock = FixedClock()
    return HarvestEngine(
        transport=transport,
        credentials=credentials,
        state=state or MemoryStateStore(),
        clock=clock,
        sleeper=ClockSleeper(clock),
        retry=RetryPolicy(max_attempts=2, base_delay=0.01),
        events=events or ListEvents(),
    )


def _content(sink: ListSink) -> set[tuple[tuple[str, str], str]]:
    return {(key, record.content_hash) for key, record in sink.records.items()}


class _ContractSuite:
    """The contract cases of one adapter; each case raises ``AssertionError`` on failure."""

    def __init__(
        self,
        factory: AdapterFactory,
        config: Mapping[str, JSON],
        transport_factory: TransportFactory,
        credentials: Mapping[tuple[str, str], str],
        request_filters: Mapping[str, JSON],
        min_records: int,
    ) -> None:
        self.factory = factory
        self.config = config
        self.transport_factory = transport_factory
        self.credentials = credentials
        self.request_filters = request_filters
        self.min_records = min_records
        self.adapter = factory()
        self.source = self.adapter.source
        self.secrets = StaticCredentials(dict(credentials))
        self.baseline = ListSink()
        self.first: HarvestResult | None = None

    def cases(self) -> tuple[tuple[str, Callable[[], str | None]], ...]:
        """All cases in execution order (later cases compare against ``full_replay``)."""
        return (
            ("declaration", self.declaration),
            ("configuration", self.configuration),
            ("full_replay", self.full_replay),
            ("determinism", self.determinism),
            ("idempotent_rerun", self.idempotent_rerun),
            ("resume_after_sink_failure", self.resume_after_sink_failure),
            ("resume_after_transport_failure", self.resume_after_transport_failure),
            ("malformed_response", self.malformed_response),
            ("missing_credentials", self.missing_credentials),
            ("secret_free", self.secret_free),
        )

    def request(self, run: str) -> HarvestRequest:
        """Request for one contract run."""
        return HarvestRequest(self.source.source_id, run, filters=dict(self.request_filters))

    def _run(self, engine: HarvestEngine, run: str, sink: ListSink) -> HarvestResult:
        return engine.run(self.factory(), self.request(run), sink, config=self.config)

    def declaration(self) -> None:
        """Source declaration is complete."""
        source = self.source
        assert source.source_id and "." in source.source_id, "source_id 'familie.quelle' erwartet"
        assert source.adapter_version and source.profile_version, "Versionen fehlen"
        assert source.family and source.data_format, "Familie/Datenformat fehlen"
        assert isinstance(source.snapshot_semantics, SnapshotSemantics)

    def configuration(self) -> None:
        """The given configuration is accepted."""
        self.adapter.validate_config(self.config)

    def full_replay(self) -> None:
        """A full replay completes and yields records with provenance."""
        engine = _engine(self.transport_factory(), self.secrets)
        result = self._run(engine, "contract-1", self.baseline)
        self.first = result
        assert result.status is RunStatus.COMPLETE, f"Status {result.status.value}: {result.errors}"
        assert result.source_exhausted, "Quelle nicht vollständig gelesen"
        assert result.records_delivered >= self.min_records, "zu wenige Datensätze"
        for record in self.baseline.records.values():
            assert record.record_id, "leere Quellen-ID"
            assert record.provenance.adapter_version == self.source.adapter_version
            assert record.provenance.profile_version == self.source.profile_version
            assert record.provenance.raw_sha256, "Provenienz ohne Rohwert-Hash"

    def determinism(self) -> None:
        """A second replay yields identical ids and hashes."""
        other = ListSink()
        self._run(_engine(self.transport_factory(), self.secrets), "contract-2", other)
        assert _content(other) == _content(self.baseline), "zweiter Lauf liefert andere IDs/Hashes"

    def idempotent_rerun(self) -> None:
        """Re-running with the same sink delivers nothing new."""
        sink = ListSink()
        engine = _engine(self.transport_factory(), self.secrets, MemoryStateStore())
        self._run(engine, "contract-3a", sink)
        engine.transport = self.transport_factory()
        again = self._run(engine, "contract-3b", sink)
        assert again.status in (RunStatus.COMPLETE, RunStatus.PARTIAL), again.errors
        assert again.records_delivered == 0, "unveränderte Datensätze erneut als neu übernommen"
        assert _content(sink) == _content(self.baseline)

    def resume_after_sink_failure(self) -> None:
        """A sink failure keeps the checkpoint; resume loses nothing."""
        pages = self.first.pages if self.first is not None else 1
        state = MemoryStateStore()
        sink = ListSink(fail_on_page=pages)
        engine = _engine(self.transport_factory(), self.secrets, state)
        broken = self._run(engine, "contract-4a", sink)
        assert broken.status in (RunStatus.PARTIAL, RunStatus.FAILED), "Senkenfehler nicht erkannt"
        assert broken.errors and broken.errors[0]["code"] == "sink_error"
        checkpoint = state.load(self.source.source_id)
        assert checkpoint is None or not checkpoint.finished, (
            "Checkpoint trotz Fehler abgeschlossen"
        )
        engine.transport = self.transport_factory()
        resumed = self._run(engine, "contract-4b", sink)
        assert resumed.status is RunStatus.COMPLETE, resumed.errors
        assert _content(sink) == _content(self.baseline), "Datenverlust nach Wiederanlauf"

    def resume_after_transport_failure(self) -> None:
        """Retries are bounded; resume after a network failure completes."""
        sink = ListSink()
        flaky = FlakyTransport(self.transport_factory(), frozenset({1, 2}))
        engine = _engine(flaky, self.secrets, MemoryStateStore())
        broken = self._run(engine, "contract-5a", sink)
        assert broken.status is RunStatus.FAILED, "dauerhafter Netzwerkfehler nicht erkannt"
        assert broken.errors[0]["code"] == "transport_error" and broken.errors[0]["retryable"]
        assert broken.attempts == 2, "Wiederholungen nicht begrenzt"
        engine.transport = self.transport_factory()
        resumed = self._run(engine, "contract-5b", sink)
        assert resumed.status is RunStatus.COMPLETE and _content(sink) == _content(self.baseline)

    def malformed_response(self) -> None:
        """An unparsable response is a parser error, not an empty result."""
        result = self._run(_engine(GarbageTransport(), self.secrets), "contract-6", ListSink())
        assert result.status is RunStatus.FAILED, "unlesbare Antwort als Erfolg gewertet"
        assert result.errors[0]["code"] == "parser_error", result.errors

    def missing_credentials(self) -> str | None:
        """Missing credentials are an authentication error."""
        if self.source.auth in (AuthKind.NONE,):
            return "SKIPPED: Quelle ohne Zugangsdaten"
        engine = _engine(self.transport_factory(), StaticCredentials())
        result = self._run(engine, "contract-7", ListSink())
        assert result.status is RunStatus.FAILED
        assert result.errors[0]["code"] == "auth_error", result.errors
        return None

    def secret_free(self) -> None:
        """Results and events contain no credential values."""
        events = ListEvents()
        engine = _engine(self.transport_factory(), self.secrets, events=events)
        result = self._run(engine, "contract-8", ListSink())
        text = repr(result.to_dict()) + repr(events.events)
        for value in self.credentials.values():
            assert value not in text, "Zugangsdaten in Ergebnis oder Ereignissen"


def _outcome(check: Callable[[], str | None]) -> str:
    """``PASS``, the case's own verdict, or ``FAIL: reason``; the suite never crashes."""
    try:
        outcome = check()
    except AssertionError as exc:
        return f"FAIL: {exc}"
    except Exception as exc:  # noqa: BLE001 - suite reports, never crashes
        return f"FAIL: {type(exc).__name__}: {exc}"
    return outcome or "PASS"


def check_adapter(
    factory: AdapterFactory,
    *,
    config: Mapping[str, JSON],
    transport_factory: TransportFactory,
    credentials: Mapping[tuple[str, str], str] | None = None,
    request_filters: Mapping[str, JSON] | None = None,
    min_records: int = 1,
) -> ContractReport:
    """Run the contract suite and return a report (never raises for adapter faults)."""
    suite = _ContractSuite(
        factory,
        config,
        transport_factory,
        credentials or {},
        request_filters or {},
        min_records,
    )
    report = ContractReport(suite.source.source_id)
    for name, check in suite.cases():
        report.cases[name] = _outcome(check)
    return report


def assert_adapter(
    factory: AdapterFactory,
    *,
    config: Mapping[str, JSON],
    transport_factory: TransportFactory,
    credentials: Mapping[tuple[str, str], str] | None = None,
    request_filters: Mapping[str, JSON] | None = None,
    min_records: int = 1,
) -> ContractReport:
    """Like :func:`check_adapter` but raises ``AssertionError`` listing failed cases."""
    report = check_adapter(
        factory,
        config=config,
        transport_factory=transport_factory,
        credentials=credentials,
        request_filters=request_filters,
        min_records=min_records,
    )
    if not report.passed:
        failed = {k: v for k, v in report.cases.items() if v.startswith("FAIL")}
        raise AssertionError(f"Adaptervertrag verletzt für {report.source_id}: {failed}")
    return report
