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
from .model import AuthKind, HarvestRequest, RunStatus, SnapshotSemantics
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
        """Request for one contract run."""
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
        """Request for one contract run."""
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

    def to_dict(self) -> dict[str, Any]:
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


def check_adapter(
    factory: AdapterFactory,
    *,
    config: Mapping[str, Any],
    transport_factory: TransportFactory,
    credentials: Mapping[tuple[str, str], str] | None = None,
    request_filters: Mapping[str, Any] | None = None,
    min_records: int = 1,
) -> ContractReport:
    """Run the contract suite and return a report (never raises for adapter faults)."""
    adapter = factory()
    source = adapter.source
    report = ContractReport(source.source_id)
    secrets = StaticCredentials(dict(credentials or {}))

    def request(run: str) -> HarvestRequest:
        """Request for one contract run."""
        return HarvestRequest(source.source_id, run, filters=dict(request_filters or {}))

    def case(name: str, check: Callable[[], str | None]) -> None:
        """Run one case and record its outcome."""
        try:
            outcome = check()
        except AssertionError as exc:
            report.cases[name] = f"FAIL: {exc}"
        except Exception as exc:  # noqa: BLE001 - suite reports, never crashes
            report.cases[name] = f"FAIL: {type(exc).__name__}: {exc}"
        else:
            report.cases[name] = outcome or "PASS"

    def declaration() -> None:
        """Source declaration is complete."""
        assert source.source_id and "." in source.source_id, "source_id 'familie.quelle' erwartet"
        assert source.adapter_version and source.profile_version, "Versionen fehlen"
        assert source.family and source.data_format, "Familie/Datenformat fehlen"
        assert isinstance(source.snapshot_semantics, SnapshotSemantics)

    def configuration() -> None:
        """The given configuration is accepted."""
        adapter.validate_config(config)

    baseline = ListSink()
    first: dict[str, Any] = {}

    def full_replay() -> None:
        """A full replay completes and yields records with provenance."""
        result = _engine(transport_factory(), secrets).run(
            factory(), request("contract-1"), baseline, config=config
        )
        first["result"] = result
        assert result.status is RunStatus.COMPLETE, f"Status {result.status.value}: {result.errors}"
        assert result.source_exhausted, "Quelle nicht vollständig gelesen"
        assert result.records_delivered >= min_records, "zu wenige Datensätze"
        for record in baseline.records.values():
            assert record.record_id, "leere Quellen-ID"
            assert record.provenance.adapter_version == source.adapter_version
            assert record.provenance.profile_version == source.profile_version
            assert record.provenance.raw_sha256, "Provenienz ohne Rohwert-Hash"

    def determinism() -> None:
        """A second replay yields identical ids and hashes."""
        other = ListSink()
        _engine(transport_factory(), secrets).run(
            factory(), request("contract-2"), other, config=config
        )
        assert _content(other) == _content(baseline), "zweiter Lauf liefert andere IDs/Hashes"

    def idempotent_rerun() -> None:
        """Re-running with the same sink delivers nothing new."""
        state = MemoryStateStore()
        sink = ListSink()
        engine = _engine(transport_factory(), secrets, state)
        engine.run(factory(), request("contract-3a"), sink, config=config)
        engine.transport = transport_factory()
        again = engine.run(factory(), request("contract-3b"), sink, config=config)
        assert again.status in (RunStatus.COMPLETE, RunStatus.PARTIAL), again.errors
        assert again.records_delivered == 0, "unveränderte Datensätze erneut als neu übernommen"
        assert _content(sink) == _content(baseline)

    def resume_after_sink_failure() -> str | None:
        """A sink failure keeps the checkpoint; resume loses nothing."""
        pages = first["result"].pages if "result" in first else 1
        state = MemoryStateStore()
        sink = ListSink(fail_on_page=pages)
        engine = _engine(transport_factory(), secrets, state)
        broken = engine.run(factory(), request("contract-4a"), sink, config=config)
        assert broken.status in (RunStatus.PARTIAL, RunStatus.FAILED), "Senkenfehler nicht erkannt"
        assert broken.errors and broken.errors[0]["code"] == "sink_error"
        checkpoint = state.load(source.source_id)
        assert checkpoint is None or not checkpoint.finished, (
            "Checkpoint trotz Fehler abgeschlossen"
        )
        engine.transport = transport_factory()
        resumed = engine.run(factory(), request("contract-4b"), sink, config=config)
        assert resumed.status is RunStatus.COMPLETE, resumed.errors
        assert _content(sink) == _content(baseline), "Datenverlust nach Wiederanlauf"
        return None

    def resume_after_transport_failure() -> None:
        """Retries are bounded; resume after a network failure completes."""
        state = MemoryStateStore()
        sink = ListSink()
        engine = _engine(FlakyTransport(transport_factory(), frozenset({1, 2})), secrets, state)
        broken = engine.run(factory(), request("contract-5a"), sink, config=config)
        assert broken.status is RunStatus.FAILED, "dauerhafter Netzwerkfehler nicht erkannt"
        assert broken.errors[0]["code"] == "transport_error" and broken.errors[0]["retryable"]
        assert broken.attempts == 2, "Wiederholungen nicht begrenzt"
        engine.transport = transport_factory()
        resumed = engine.run(factory(), request("contract-5b"), sink, config=config)
        assert resumed.status is RunStatus.COMPLETE and _content(sink) == _content(baseline)

    def malformed_response() -> None:
        """An unparsable response is a parser error, not an empty result."""
        result = _engine(GarbageTransport(), secrets).run(
            factory(), request("contract-6"), ListSink(), config=config
        )
        assert result.status is RunStatus.FAILED, "unlesbare Antwort als Erfolg gewertet"
        assert result.errors[0]["code"] == "parser_error", result.errors

    def missing_credentials() -> str | None:
        """Missing credentials are an authentication error."""
        if source.auth in (AuthKind.NONE,):
            return "SKIPPED: Quelle ohne Zugangsdaten"
        result = _engine(transport_factory(), StaticCredentials()).run(
            factory(), request("contract-7"), ListSink(), config=config
        )
        assert result.status is RunStatus.FAILED
        assert result.errors[0]["code"] == "auth_error", result.errors
        return None

    def secret_free() -> None:
        """Results and events contain no credential values."""
        events = ListEvents()
        result = _engine(transport_factory(), secrets, events=events).run(
            factory(), request("contract-8"), ListSink(), config=config
        )
        text = repr(result.to_dict()) + repr(events.events)
        for value in (credentials or {}).values():
            assert value not in text, "Zugangsdaten in Ergebnis oder Ereignissen"

    for name, check in (
        ("declaration", declaration),
        ("configuration", configuration),
        ("full_replay", full_replay),
        ("determinism", determinism),
        ("idempotent_rerun", idempotent_rerun),
        ("resume_after_sink_failure", resume_after_sink_failure),
        ("resume_after_transport_failure", resume_after_transport_failure),
        ("malformed_response", malformed_response),
        ("missing_credentials", missing_credentials),
        ("secret_free", secret_free),
    ):
        case(name, check)
    return report


def assert_adapter(factory: AdapterFactory, **kwargs: Any) -> ContractReport:
    """Like :func:`check_adapter` but raises ``AssertionError`` listing failed cases."""
    report = check_adapter(factory, **kwargs)
    if not report.passed:
        failed = {k: v for k, v in report.cases.items() if v.startswith("FAIL")}
        raise AssertionError(f"Adaptervertrag verletzt für {report.source_id}: {failed}")
    return report
