"""``auditcore-harvest``: validate the source catalogue and replay adapters on fixtures.

Commands::

    auditcore-harvest catalog [--file FILE]          validate and summarise
    auditcore-harvest replay MODULE:FACTORY --fixture F.json --config C.json
                             [--output records.jsonl]

``replay`` never touches the network: requests are answered from the fixture
only. Live runs with a real transport are a consumer integration concern.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path

from .adapter import SourceAdapter
from .catalog import load_catalog, summary, validate_catalog
from .engine import HarvestEngine
from .errors import ConfigError
from .memory import ClockSleeper, FixedClock, ListSink, MemoryStateStore, StaticCredentials
from .model import HarvestRequest
from .transport import ReplayTransport


def _factory(spec: str) -> Callable[[], SourceAdapter]:
    module_name, _, attribute = spec.partition(":")
    if not module_name or not attribute:
        raise ConfigError("Adapter als 'modul:fabrik' angeben.")
    factory: Callable[[], SourceAdapter] = getattr(importlib.import_module(module_name), attribute)
    return factory


def main(argv: list[str] | None = None) -> int:
    """Entry point; returns the process exit code."""
    parser = argparse.ArgumentParser(
        prog="auditcore-harvest",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    catalog = commands.add_parser("catalog", help="Quellenkatalog prüfen und zusammenfassen")
    catalog.add_argument("--file", type=Path)
    replay = commands.add_parser("replay", help="Adapter gegen aufgezeichnete Fixtures ausführen")
    replay.add_argument("adapter")
    replay.add_argument("--fixture", type=Path, required=True)
    replay.add_argument("--config", type=Path, required=True)
    replay.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "catalog":
            entries = (
                validate_catalog(json.loads(args.file.read_text(encoding="utf-8")))
                if args.file
                else load_catalog()
            )
            print(
                json.dumps(
                    {"sources": len(entries), **summary(entries)},
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        adapter = _factory(args.adapter)()
        config = json.loads(args.config.read_text(encoding="utf-8"))
        clock = FixedClock()
        engine = HarvestEngine(
            ReplayTransport.from_file(args.fixture),
            StaticCredentials({(adapter.source.source_id, "api_key"): "replay"}),
            MemoryStateStore(),
            clock,
            ClockSleeper(clock),
        )
        sink = ListSink()
        result = engine.run(
            adapter, HarvestRequest(adapter.source.source_id, "replay"), sink, config=config
        )
        if args.output:
            args.output.write_text(
                "".join(
                    json.dumps(r.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
                    for r in sink.records.values()
                ),
                encoding="utf-8",
            )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result.status.value == "complete" else 1
    except (ConfigError, OSError, ValueError) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
