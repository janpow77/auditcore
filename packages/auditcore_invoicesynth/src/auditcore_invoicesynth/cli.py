"""Kommandozeile ``auditcore-invoicesynth``: fonts, plan, build, build-diagnostics, verify,
evaluate."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from auditcore_invoicesynth.dataset import (
    DatasetError,
    build_dataset,
    load_split,
    plan_summary,
    verify_dataset,
)
from auditcore_invoicesynth.diagnostics import (
    DIAGNOSTIC_SETS,
    DiagnosticConfig,
    build_diagnostics,
    resolve_sets,
)
from auditcore_invoicesynth.evaluation import check_acceptance, evaluate
from auditcore_invoicesynth.fonts import (
    DEFAULT_FONT_DIRS,
    FontError,
    FontSet,
    discover_fonts,
    font_report,
)
from auditcore_invoicesynth.plan import SPLITS, SynthConfig
from auditcore_invoicesynth.variety import VARIETIES


def _config(args: argparse.Namespace) -> SynthConfig:
    counts = dict(SynthConfig().counts)
    for split in SPLITS:
        value = getattr(args, split, None)
        if value is not None:
            counts[split] = value
    return SynthConfig(
        seed=args.seed,
        base_date=date.fromisoformat(args.base_date),
        counts=counts,
        dpi_choices=tuple(args.dpi),
        variety=args.variety,
    )


def _fonts(args: argparse.Namespace) -> FontSet:
    dirs = [Path(d) for d in args.font_dir] if args.font_dir else list(DEFAULT_FONT_DIRS)
    pins = json.loads(Path(args.font_pins).read_text()) if args.font_pins else None
    return discover_fonts(dirs, pins=pins)


def _print(data: object) -> None:
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def _common(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--seed", type=int, default=42)
    sub.add_argument("--base-date", default="2026-01-15")
    sub.add_argument("--dpi", type=int, action="append", default=None)
    sub.add_argument("--font-dir", action="append", default=[])
    sub.add_argument("--font-pins", help="JSON {Dateiname: SHA-256}")
    sub.add_argument(
        "--variety",
        choices=VARIETIES,
        default="v1",
        help="Generatorvariante; v1 = bisher (Hash stabil), v2 = Stufe 5, v3/v4 = Stufe 6/7",
    )
    for split in SPLITS:
        sub.add_argument(f"--{split.replace('_', '-')}", dest=split, type=int)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="auditcore-invoicesynth")
    commands = parser.add_subparsers(dest="command", required=True)
    fonts_cmd = commands.add_parser("fonts", help="freie Schriften suchen")
    fonts_cmd.add_argument("--font-dir", action="append", default=[])
    fonts_cmd.add_argument("--font-pins")
    _common(commands.add_parser("plan", help="Plan ohne Bilder"))
    build_cmd = commands.add_parser("build", help="Datensatz schreiben")
    _common(build_cmd)
    build_cmd.add_argument("--out", required=True)
    build_cmd.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Renderprozesse; 0 = automatisch (bis zu 16), 1 = sequenziell",
    )
    _diagnostics_parser(commands.add_parser("build-diagnostics", help="nur Diagnosesätze"))
    verify_cmd = commands.add_parser("verify", help="Datensatz gegen Manifest prüfen")
    verify_cmd.add_argument("dataset")
    eval_cmd = commands.add_parser("evaluate", help="Vorhersagen bewerten")
    eval_cmd.add_argument("dataset")
    eval_cmd.add_argument("--split", default="test_synthetic", choices=(*SPLITS, *DIAGNOSTIC_SETS))
    eval_cmd.add_argument("--predictions", required=True, help="JSONL {file_name, parse}")
    return parser


def _diagnostics_parser(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--out", required=True)
    sub.add_argument("--seed", type=int, default=42)
    sub.add_argument("--base-date", default="2026-01-15")
    sub.add_argument("--dpi", type=int, action="append", default=None)
    sub.add_argument("--font-dir", action="append", default=[])
    sub.add_argument("--font-pins", help="JSON {Dateiname: SHA-256}")
    sub.add_argument("--count", type=int, default=500, help="Belege je Diagnosesatz")
    sub.add_argument(
        "--sets",
        default="shuffled,holdout_b",
        help="Kommaliste: shuffled (T2-gemischt), holdout_b (T2b), holdout_c (T2c) oder Satznamen",
    )
    sub.add_argument("--workers", type=int, default=0, help="0 = automatisch (bis zu 16)")


def _build_diagnostics(args: argparse.Namespace) -> int:
    if args.workers < 0:
        raise ValueError("--workers muss 0 oder größer sein")
    config = DiagnosticConfig(
        seed=args.seed,
        base_date=date.fromisoformat(args.base_date),
        count=args.count,
        sets=resolve_sets(args.sets),
        dpi_choices=tuple(args.dpi or [150, 200, 300]),
    )
    workers = args.workers or min(16, max(1, (os.cpu_count() or 2) - 2))
    manifest = build_diagnostics(config, Path(args.out), _fonts(args), workers=workers)
    _print({"dataset_hash": manifest["dataset_hash"], "sets": manifest["sets"]})
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "fonts":
            _print(font_report(_fonts(args)))
            return 0
        if args.command in {"plan", "build"}:
            return _plan_or_build(args)
        if args.command == "build-diagnostics":
            return _build_diagnostics(args)
        if args.command == "verify":
            return _verify(args)
        return _evaluate(args)
    except (DatasetError, FontError, ValueError) as exc:
        sys.stderr.write(f"Fehler: {exc}\n")
        return 2


def _plan_or_build(args: argparse.Namespace) -> int:
    args.dpi = args.dpi or [150, 200, 300]
    config = _config(args)
    fonts = _fonts(args)
    if args.command == "plan":
        _print(plan_summary(config, fonts.families))
        return 0
    if args.workers < 0:
        raise ValueError("--workers muss 0 oder größer sein")
    manifest = build_dataset(
        config,
        Path(args.out),
        fonts,
        workers=None if args.workers == 0 else args.workers,
    )
    _print({"dataset_hash": manifest["dataset_hash"], "splits": manifest["splits"]})
    return 0


def _verify(args: argparse.Namespace) -> int:
    result = verify_dataset(Path(args.dataset))
    _print(
        {
            "ok": result.ok,
            "dataset_hash": result.dataset_hash,
            "expected_hash": result.expected_hash,
            "missing": list(result.missing),
            "unexpected": list(result.unexpected),
            "changed": list(result.changed),
        }
    )
    return 0 if result.ok else 1


def _evaluate(args: argparse.Namespace) -> int:
    rows = {row["file_name"]: row for row in load_split(Path(args.dataset), args.split)}
    predictions = {}
    for line in Path(args.predictions).read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            predictions[record["file_name"]] = record.get("parse", {})
    report = evaluate(
        (row["gt_parse"], predictions.get(name, {})) for name, row in sorted(rows.items())
    )
    acceptance = check_acceptance(report)
    _print(
        {
            **report.to_dict(),
            "acceptance": {"passed": acceptance.passed, "failures": list(acceptance.failures)},
        }
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
