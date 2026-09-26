"""Bewertung nach dem Training (Plan 2d): ein Befehl für Kandidat und Donut-CORD.

::

    python -m auditcore_invoicesynth.train.evaluate --dataset ds/ --run-dir runs/r1 \\
        --cord-model-dir base/donut-cord-v2 --out eval/r1.json

* Kandidat: neuester gültiger Checkpoint aus ``--run-dir`` (oder ``--model-dir``),
  Ausgabe über das Ziel-JSON ``auditcore_invoice_v1``.
* Vergleich: ``donut-base-finetuned-cord-v2`` (Prompt ``<s_cord-v2>``); dessen
  Felder werden abgebildet (``total.total_price`` → ``total``,
  ``sub_total.subtotal_price`` → ``net_amount``, ``sub_total.tax_price`` →
  Steuerzeile). Rechnungsnummer, Datum, IBAN und USt-IdNr. kennt CORD nicht.
* Testsätze: ``test_synthetic`` (T1) und ``test_layout_holdout`` (T2). Je Satz
  und Modell ``<out>.<modell>.<satz>.jsonl`` mit Vorhersagen, dazu der
  Gesamtbericht mit Kennzahlen und Abnahmeprüfung (E6).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path

from auditcore_invoicesynth.dataset import load_split, verify_dataset
from auditcore_invoicesynth.evaluation import check_acceptance, evaluate
from auditcore_invoicesynth.schema import TASK_TOKEN, from_sequence
from auditcore_invoicesynth.train.checkpoint import CheckpointManager
from auditcore_invoicesynth.train.torch_predict import Predictor, donut_predictor

CORD_PROMPT = "<s_cord-v2>"
DEFAULT_SPLITS = ("test_synthetic", "test_layout_holdout")


def latest_checkpoint(run_dir: Path) -> Path:
    """Neuester Checkpoint mit gültigen Prüfsummen (ohne Lauf-Abgleich, nur lesend)."""
    candidates = sorted(run_dir.glob("checkpoint-[0-9]*"), reverse=True)
    for path in candidates:
        if path.is_dir() and CheckpointManager.verify(path) is None:
            return path
    raise FileNotFoundError(f"Kein gültiger Checkpoint in {run_dir}")


def cord_to_invoice(parse: Mapping[str, object]) -> dict[str, object]:
    """CORD-Ausgabe auf die vergleichbaren Felder des Ziel-JSON abbilden."""
    result: dict[str, object] = {}
    total = parse.get("total")
    if isinstance(total, dict) and isinstance(total.get("total_price"), str):
        result["total"] = total["total_price"]
    sub_total = parse.get("sub_total")
    if isinstance(sub_total, dict):
        if isinstance(sub_total.get("subtotal_price"), str):
            result["net_amount"] = sub_total["subtotal_price"]
        if isinstance(sub_total.get("tax_price"), str):
            result["vat_lines"] = [{"amount": sub_total["tax_price"]}]
    return result


def parse_output(sequence: str, *, cord: bool) -> dict[str, object]:
    if not cord:
        return from_sequence(sequence)
    return cord_to_invoice(from_sequence(sequence.replace(CORD_PROMPT, "", 1)))


def run_split(
    dataset: Path,
    split: str,
    predictor: Predictor,
    *,
    cord: bool,
    out: Path,
    limit: int | None = None,
) -> dict[str, object]:
    """Vorhersagen schreiben und bewerten; Laufzeit je Seite (Median, 95-Perzentil)."""
    rows = load_split(dataset, split)[:limit]
    pairs = []
    seconds = []
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            started = time.monotonic()
            sequence = predictor(dataset / split / row["file_name"])
            seconds.append(time.monotonic() - started)
            parse = parse_output(sequence, cord=cord)
            pairs.append((row["gt_parse"], parse))
            record = {"file_name": row["file_name"], "parse": parse, "raw": sequence}
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    report = evaluate(pairs)
    acceptance = check_acceptance(report)
    timing = _quantiles(seconds)
    return {
        **report.to_dict(),
        "acceptance": {"passed": acceptance.passed, "failures": list(acceptance.failures)},
        "seconds_per_page": timing,
        "predictions": str(out),
        "summary": {
            "documents": report.documents,
            "document_rate": round(report.document_rate, 4),
            "accuracy": {k: round(v.accuracy, 4) for k, v in sorted(report.fields.items())},
            "acceptance": acceptance.passed,
            "seconds_per_page": timing,
        },
    }


def _quantiles(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"median": None, "p95": None}
    ordered = sorted(values)
    return {
        "median": round(ordered[len(ordered) // 2], 3),
        "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 3),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m auditcore_invoicesynth.train.evaluate")
    parser.add_argument("--dataset", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run-dir", help="neuester gültiger Checkpoint des Laufs")
    source.add_argument("--model-dir")
    parser.add_argument("--cord-model-dir", help="Vergleich Donut-CORD (optional)")
    parser.add_argument("--splits", nargs="+", default=list(DEFAULT_SPLITS))
    parser.add_argument("--limit", type=int, help="nur die ersten N Seiten je Satz")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--out", required=True, help="Bericht (JSON)")
    return parser


def main(
    argv: list[str] | None = None,
    make_predictor: Callable[..., Predictor] = donut_predictor,
) -> int:
    args = _parser().parse_args(argv)
    dataset = Path(args.dataset)
    verification = verify_dataset(dataset)
    if not verification.ok:
        sys.stderr.write("Fehler: Datensatz weicht vom Manifest ab\n")
        return 2
    model_dir = Path(args.model_dir) if args.model_dir else latest_checkpoint(Path(args.run_dir))
    candidates: list[tuple[str, Path, str, bool]] = [("kandidat", model_dir, TASK_TOKEN, False)]
    if args.cord_model_dir:
        candidates.append(("donut_cord", Path(args.cord_model_dir), CORD_PROMPT, True))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict[str, dict[str, object]]] = {}
    for name, directory, prompt, cord in candidates:
        predictor = make_predictor(
            directory, prompt=prompt, max_length=args.max_length, device=args.device
        )
        results[name] = {
            split: run_split(
                dataset,
                split,
                predictor,
                cord=cord,
                out=out.with_name(f"{out.stem}.{name}.{split}.jsonl"),
                limit=args.limit,
            )
            for split in _splits(args.splits)
        }
    report = {
        "dataset_hash": verification.dataset_hash,
        "model_dir": str(model_dir),
        "results": results,
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    summary = {
        f"{name}/{split}": result["summary"]
        for name, splits in results.items()
        for split, result in splits.items()
    }
    sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    return 0


def _splits(splits: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(splits))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
