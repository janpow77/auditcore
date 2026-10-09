"""Contract for multi-stage runs and crawls with a changing candidate list.

A crawl (for example: read an index page, then search sub-pages, then fetch
documents) still runs through the normal engine, one bounded step per page:

* :class:`CrawlTask` is one unit of work of a named stage (``"index"``,
  ``"subpage"``, ``"document"`` …) at a locator.
* A stage (:class:`Stage` or :class:`AsyncStage`) handles one task and
  returns records, issues and newly *discovered* tasks (:class:`StageResult`).
* :class:`Frontier` is the candidate list. It deduplicates by stage and
  locator, bounds depth and size (:class:`CrawlLimits`) and is stored as the
  cursor, so checkpoints, resume and retries work as for any paging source.
  Candidates dropped by a limit become visible ``RecordIssue`` entries.
* :class:`CrawlAdapter` and :class:`AsyncCrawlAdapter` turn seeds and stages
  into a regular (async) source adapter; the run is complete when the
  frontier is empty.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from .adapter import FetchContext
from .errors import ConfigError, ParserError
from .model import JSON, Cursor, HarvestRecord, PageResult, RecordIssue, Source, page_result

if TYPE_CHECKING:  # pragma: no cover - typing only; aio loads asyncio
    from .aio import AsyncFetchContext

CRAWL_CURSOR = "auditcore_harvest.crawl/1"
_TOO_DEEP = "Kandidat über der Höchsttiefe verworfen."
_TOO_MANY = "Kandidat über dem Aufgabenlimit verworfen."


@dataclass(frozen=True)
class CrawlTask:
    """One unit of work: a stage name, a locator and optional JSON data."""

    stage: str
    locator: str
    depth: int = 0
    data: Mapping[str, JSON] = field(default_factory=dict)

    @property
    def key(self) -> str:
        """Identity for deduplication (stage and locator)."""
        return f"{self.stage}\x1f{self.locator}"

    def to_dict(self) -> dict[str, JSON]:
        """JSON view (part of the cursor)."""
        return {
            "stage": self.stage,
            "locator": self.locator,
            "depth": self.depth,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, JSON]) -> CrawlTask:
        """Inverse of :meth:`to_dict`."""
        return cls(str(data["stage"]), str(data["locator"]), int(data["depth"]), dict(data["data"]))


@dataclass(frozen=True)
class StageResult:
    """What a stage produced for one task."""

    records: Sequence[HarvestRecord] = ()
    issues: Sequence[RecordIssue] = ()
    discovered: Sequence[CrawlTask] = ()


@dataclass(frozen=True)
class CrawlLimits:
    """Bounds of one crawl: depth of discovered tasks and total number of tasks."""

    max_depth: int = 3
    max_tasks: int = 1000


@dataclass(frozen=True)
class Frontier:
    """Pending tasks plus every task key ever accepted; serialised as cursor."""

    pending: tuple[CrawlTask, ...]
    seen: frozenset[str] = frozenset()
    done: int = 0

    @classmethod
    def start(cls, seeds: Sequence[CrawlTask], limits: CrawlLimits) -> Frontier:
        """Frontier of the seeds (deduplicated, bounded by ``max_tasks``)."""
        frontier, _ = cls(()).extend(seeds, limits)
        return frontier

    def extend(
        self, tasks: Sequence[CrawlTask], limits: CrawlLimits
    ) -> tuple[Frontier, tuple[RecordIssue, ...]]:
        """Append new tasks; known ones are skipped, those over a limit reported."""
        pending, seen = list(self.pending), set(self.seen)
        dropped: list[RecordIssue] = []
        for task in tasks:
            if task.key in seen:
                continue
            if task.depth > limits.max_depth:
                dropped.append(RecordIssue(task.locator, _TOO_DEEP))
            elif len(seen) >= limits.max_tasks:
                dropped.append(RecordIssue(task.locator, _TOO_MANY))
            else:
                seen.add(task.key)
                pending.append(task)
        return Frontier(tuple(pending), frozenset(seen), self.done), tuple(dropped)

    def to_cursor(self) -> dict[str, JSON]:
        """Cursor form stored in checkpoints."""
        return {
            "format": CRAWL_CURSOR,
            "pending": [task.to_dict() for task in self.pending],
            "seen": sorted(self.seen),
            "done": self.done,
        }

    @classmethod
    def from_cursor(cls, cursor: Cursor) -> Frontier:
        """Inverse of :meth:`to_cursor`; a foreign cursor is a ``ParserError``."""
        if cursor.get("format") != CRAWL_CURSOR:
            raise ParserError("Cursor gehört nicht zu einem Crawl-Ablauf.")
        try:
            pending = tuple(CrawlTask.from_dict(item) for item in cursor["pending"])
            return cls(pending, frozenset(str(k) for k in cursor["seen"]), int(cursor["done"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ParserError("Crawl-Cursor ist beschädigt.") from exc


class Stage(Protocol):
    """Handles one task of a stage synchronously."""

    def __call__(self, context: FetchContext, task: CrawlTask) -> StageResult:
        """Records, issues and discovered tasks of ``task``."""
        ...


class AsyncStage(Protocol):
    """Handles one task of a stage asynchronously."""

    async def __call__(self, context: AsyncFetchContext, task: CrawlTask) -> StageResult:
        """Records, issues and discovered tasks of ``task``."""
        ...


Seeds = Callable[[Mapping[str, JSON]], Sequence[CrawlTask]]
Validator = Callable[[Mapping[str, JSON]], None]


class _Crawl:
    """Seed and frontier handling shared by the sync and async crawl adapter."""

    def __init__(
        self,
        source: Source,
        seeds: Seeds,
        stage_names: frozenset[str],
        limits: CrawlLimits,
        validate: Validator | None,
    ) -> None:
        self._source = source
        self._seeds = seeds
        self._stage_names = stage_names
        self.limits = limits
        self._validate = validate

    @property
    def source(self) -> Source:
        """Declared source identity and capabilities."""
        return self._source

    def validate_config(self, config: Mapping[str, JSON]) -> None:
        """Adapter-specific check, then every seed must name a known stage."""
        if self._validate is not None:
            self._validate(config)
        self._known(self._seeds(config))

    def _known(self, tasks: Sequence[CrawlTask]) -> None:
        unknown = sorted({t.stage for t in tasks} - self._stage_names)
        if unknown:
            raise ConfigError(f"Unbekannte Crawl-Stufe(n): {', '.join(unknown)}.")

    def _frontier(self, context: FetchContext, cursor: Cursor | None) -> Frontier:
        if cursor is None:
            return Frontier.start(self._seeds(context.config), self.limits)
        return Frontier.from_cursor(cursor)

    def _page(self, frontier: Frontier, result: StageResult) -> PageResult:
        """Page for the first pending task; its discoveries extend the frontier."""
        self._known(result.discovered)
        rest = Frontier(frontier.pending[1:], frontier.seen, frontier.done + 1)
        rest, dropped = rest.extend(result.discovered, self.limits)
        issues = (*result.issues, *dropped)
        cursor = rest.to_cursor() if rest.pending else None
        return page_result(result.records, issues, cursor)


class CrawlAdapter(_Crawl):
    """Source adapter running ``stages`` over a frontier, one task per page."""

    def __init__(
        self,
        source: Source,
        seeds: Seeds,
        stages: Mapping[str, Stage],
        *,
        limits: CrawlLimits | None = None,
        validate: Validator | None = None,
    ) -> None:
        super().__init__(source, seeds, frozenset(stages), limits or CrawlLimits(), validate)
        self.stages = dict(stages)

    def fetch_page(self, context: FetchContext, cursor: Cursor | None) -> PageResult:
        """Handle the next task of the frontier."""
        frontier = self._frontier(context, cursor)
        if not frontier.pending:
            return page_result([])
        task = frontier.pending[0]
        return self._page(frontier, self.stages[task.stage](context, task))


class AsyncCrawlAdapter(_Crawl):
    """Asynchronous :class:`CrawlAdapter` for :class:`~auditcore_harvest.aio.AsyncHarvestEngine`."""

    def __init__(
        self,
        source: Source,
        seeds: Seeds,
        stages: Mapping[str, AsyncStage],
        *,
        limits: CrawlLimits | None = None,
        validate: Validator | None = None,
    ) -> None:
        super().__init__(source, seeds, frozenset(stages), limits or CrawlLimits(), validate)
        self.stages = dict(stages)

    async def fetch_page(self, context: AsyncFetchContext, cursor: Cursor | None) -> PageResult:
        """Handle the next task of the frontier."""
        frontier = self._frontier(context, cursor)
        if not frontier.pending:
            return page_result([])
        task = frontier.pending[0]
        return self._page(frontier, await self.stages[task.stage](context, task))
