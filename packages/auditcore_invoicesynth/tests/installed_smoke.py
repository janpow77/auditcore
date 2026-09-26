"""Run with python -I against an installed wheel or Debian package; no pytest needed."""

from datetime import date
from importlib.metadata import distribution
from importlib.util import find_spec
from random import Random

from auditcore_invoicegenerator import InvoiceScenario

from auditcore_invoicesynth import (
    SynthConfig,
    enrich,
    evaluate,
    fictional_bank_account,
    fictional_vat_id,
    from_sequence,
    iban_valid,
    plan_summary,
    to_sequence,
    vat_id_valid,
)
from auditcore_invoicesynth.plan import plan_dataset


def main() -> None:
    """Core contract of the installed package without the render extra."""
    package = distribution("auditcore_invoicesynth")
    assert package.version == "0.2.0"
    assert [r for r in package.requires or [] if "extra ==" not in r] == [
        "auditcore_common==0.2.0",
        "auditcore_invoicegenerator==0.2.3",
    ]
    assert find_spec("auditcore") is None
    rng = Random(3)
    for country in ("DE", "AT"):
        assert iban_valid(fictional_bank_account(rng, country).iban)
        assert vat_id_valid(fictional_vat_id(rng, country))
    record = InvoiceScenario(1, base_date=date(2026, 1, 15)).generate(1)
    invoice = enrich(record, rng=Random(1), vat_scheme="de_mixed")
    assert invoice.net_amount + invoice.vat_amount == invoice.total
    ground_truth = {"invoice_number": invoice.invoice_number, "total": f"{invoice.total}"}
    assert from_sequence(to_sequence(ground_truth)) == ground_truth
    families = ("DejaVu Sans", "DejaVu Serif")
    summary = plan_summary(SynthConfig(), families)
    assert summary["samples"] == 2000
    holdout = [s for s in plan_dataset(SynthConfig(), families) if s.split == "test_layout_holdout"]
    assert {s.layout for s in holdout} == {"holdout_kompakt", "holdout_briefkopf"}
    report = evaluate([(ground_truth, ground_truth)])
    assert report.fields["invoice_number"].accuracy == 1.0
    train_smoke()
    print("auditcore_invoicesynth installed smoke PASS", summary["plan_sha256"])


def train_smoke() -> None:
    """Trainingssteuerung ohne Torch: Rechenort offline, Wiederaufnahme mit Ersatzmodell."""
    import tempfile
    from dataclasses import replace
    from pathlib import Path

    from auditcore_invoicesynth.train import (
        PROFILES,
        MockBackend,
        choose_topology,
        flowagent_job,
        run_training,
    )

    config = PROFILES["donut_train_janpow_ai"]
    offline = choose_topology(config, [])
    assert offline.mode == "unavailable"
    job = flowagent_job(config, offline, dataset_hash="0" * 64, dataset_uri="-", run_id="r")
    assert job["status"] == "WAITING_FOR_COMPUTE" and job["fallback"] is None
    smoke = replace(PROFILES["cpu_smoke"], max_steps=8, checkpoint_every_steps=4)
    with tempfile.TemporaryDirectory() as tmp:
        run = Path(tmp)
        kwargs = {"samples": 5, "run_dir": run, "run_id": "r", "dataset_hash": "d"}
        run_training(MockBackend(), smoke, stop_after_step=6, **kwargs)  # type: ignore[arg-type]
        resumed = run_training(MockBackend(), smoke, **kwargs)  # type: ignore[arg-type]
        assert resumed.resumed_from == 4 and resumed.final_step == 8


if __name__ == "__main__":
    main()
