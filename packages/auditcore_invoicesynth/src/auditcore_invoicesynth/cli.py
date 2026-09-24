"""Kommandozeile ``auditcore-invoicesynth``: fonts, plan, build, verify, evaluate."""

from __future__ import annotations

import argparse
import json
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
from auditcore_invoicesynth.evaluation import check_acceptance, evaluate
from auditcore_invoicesynth.fonts import DEFAULT_FONT_DIRS, FontError, discover_fonts, font_report
from auditcore_invoicesynth.plan import SPLITS, SynthConfig


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
    )


def _fonts(args: argparse.Namespace):  # type: ignore[no-untyped-def]
    dirs = [Path(d) for d in args.font_dir] if args.font_dir else list(DEFAULT_FONT_DIRS)
    pins = json.loads(Path(args.font_pins).read_text()) if args.font_pins else None
    return discover_fonts(dirs, pins=pins)


def _print(data: object) -> None:
    sys.stdout.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="auditcore-invoicesynth")
    commands = parser.add_subparsers(dest="command", required=True)

    def common(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--seed", type=int, default=42)
        sub.add_argument("--base-date", default="2026-01-15")
        sub.add_argument("--dpi", type=int, action="append", default=None)
        sub.add_argument("--font-dir", action="append", default=[])
        sub.add_argument("--font-pins", help="JSON {Dateiname: SHA-256}")
        for split in SPLITS:
            sub.add_argument(f"--{split.replace('_', '-')}", dest=split, type=int)

    fonts_cmd = commands.add_parser("fonts", help="freie Schriften suchen")
    fonts_cmd.add_argument("--font-dir", action="append", default=[])
    fonts_cmd.add_argument("--font-pins")
    common(commands.add_parser("plan", help="Plan ohne Bilder"))
    build_cmd = commands.add_parser("build", help="Datensatz schreiben")
    common(build_cmd)
    build_cmd.add_argument("--out", required=True)
    verify_cmd = commands.add_parser("verify", help="Datensatz gegen Manifest prüfen")
    verify_cmd.add_argument("dataset")
    eval_cmd = commands.add_parser("evaluate", help="Vorhersagen bewerten")
    eval_cmd.add_argument("dataset")
    eval_cmd.add_argument("--split", default="test_synthetic", choices=SPLITS)
    eval_cmd.add_argument("--predictions", required=True, help="JSONL {file_name, parse}")
    args = parser.parse_args(argv)
    try:
        if args.command == "fonts":
            _print(font_report(_fonts(args)))
            return 0
        if args.command in {"plan", "build"}:
            args.dpi = args.dpi or [150, 200, 300]
            config = _config(args)
            fonts = _fonts(args)
            if args.command == "plan":
                _print(plan_summary(config, fonts.families))
                return 0
            manifest = build_dataset(config, Path(args.out), fonts)
            _print({"dataset_hash": manifest["dataset_hash"], "splits": manifest["splits"]})
            return 0
        if args.command == "verify":
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
    except (DatasetError, FontError, ValueError) as exc:
        sys.stderr.write(f"Fehler: {exc}\n")
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
