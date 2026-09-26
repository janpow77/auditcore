"""Synthetische Trainings- und Testdaten für Donut-Belegerkennung (auditcore_invoice_v1).

Kern ohne Zusatzpakete: fiktive, prüfziffer-gültige Kennungen, Formate,
Anreicherung von ``auditcore_invoicegenerator``-Datensätzen, Variantenplan,
Ziel-JSON/Donut-Token, Manifest-Prüfung und Bewertung. Rendern und
Scanrauschen benötigen das Extra ``render`` (Pillow).
"""

from auditcore_invoicesynth.dataset import (
    DatasetError,
    build_dataset,
    dataset_hash,
    load_split,
    plan_summary,
    prepare_samples,
    verify_dataset,
)
from auditcore_invoicesynth.enrich import ALLOWED_VAT_RATES, SynthInvoice, enrich
from auditcore_invoicesynth.evaluation import (
    ACCEPTANCE_THRESHOLDS,
    EvaluationReport,
    check_acceptance,
    evaluate,
)
from auditcore_invoicesynth.fonts import (
    FONT_CATALOG,
    FontError,
    FontSet,
    discover_fonts,
    fetch_font,
)
from auditcore_invoicesynth.identifiers import (
    at_uid_check_digit,
    de_vat_check_digit,
    fictional_bank_account,
    fictional_vat_id,
    iban_valid,
    vat_id_valid,
)
from auditcore_invoicesynth.layouts import HOLDOUT_LAYOUTS, LAYOUTS, TRAINING_LAYOUTS
from auditcore_invoicesynth.plan import SPLITS, SampleSpec, SynthConfig, plan_dataset
from auditcore_invoicesynth.schema import (
    SCHEMA_VERSION,
    TASK_TOKEN,
    from_sequence,
    special_tokens,
    to_sequence,
)

__version__ = "0.2.0"

__all__ = [
    "ACCEPTANCE_THRESHOLDS",
    "ALLOWED_VAT_RATES",
    "FONT_CATALOG",
    "HOLDOUT_LAYOUTS",
    "LAYOUTS",
    "SCHEMA_VERSION",
    "SPLITS",
    "TASK_TOKEN",
    "TRAINING_LAYOUTS",
    "DatasetError",
    "EvaluationReport",
    "FontError",
    "FontSet",
    "SampleSpec",
    "SynthConfig",
    "SynthInvoice",
    "__version__",
    "at_uid_check_digit",
    "build_dataset",
    "check_acceptance",
    "dataset_hash",
    "de_vat_check_digit",
    "discover_fonts",
    "enrich",
    "evaluate",
    "fetch_font",
    "fictional_bank_account",
    "fictional_vat_id",
    "from_sequence",
    "iban_valid",
    "load_split",
    "plan_dataset",
    "plan_summary",
    "prepare_samples",
    "special_tokens",
    "to_sequence",
    "vat_id_valid",
    "verify_dataset",
]
