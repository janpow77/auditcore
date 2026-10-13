"""Coherent synthetic test bundles for cohesion-policy audit work.

One seed and one base date give a reproducible bundle: operations, payment
claims, receipts, payment applications to the Commission and the accounts,
with amounts that add up to the cent. Template profiles project the bundle
into document layouts; a free table is built from a recipe of typed columns.
Every output carries the marker ``SYNTHETISCH``, the seed and the package
version. No database, no third-party dependency.
"""

from __future__ import annotations

from auditcore_dummybundle.amounts import allocate, quantize, share, split_random
from auditcore_dummybundle.anomalies import ANOMALIES, AnomalyKind, anomaly_codes, plant_anomalies
from auditcore_dummybundle.bundle import Bundle, build_bundle
from auditcore_dummybundle.checks import CheckOutcome, run_checks
from auditcore_dummybundle.config import (
    BundleConfig,
    BundleLimits,
    accounting_year,
    parse_config,
)
from auditcore_dummybundle.errors import BudgetExceededError, BundleError
from auditcore_dummybundle.export import document
from auditcore_dummybundle.generate import (
    VERSION,
    Options,
    generate_recipe,
    generate_templates,
)
from auditcore_dummybundle.identifiers import bic, iban, vat_id
from auditcore_dummybundle.model import (
    MARKING,
    Budget,
    Column,
    Result,
    SolutionEntry,
    Table,
)
from auditcore_dummybundle.recipe import Recipe, RecipeLimits, parse_recipe
from auditcore_dummybundle.seeds import derive_seed
from auditcore_dummybundle.table import generate_table, recipe_document
from auditcore_dummybundle.templates import Template, get_template, template_recipe, templates

__version__ = VERSION

__all__ = [
    "ANOMALIES",
    "MARKING",
    "AnomalyKind",
    "BudgetExceededError",
    "Budget",
    "Bundle",
    "BundleConfig",
    "BundleError",
    "BundleLimits",
    "CheckOutcome",
    "Column",
    "Options",
    "Recipe",
    "RecipeLimits",
    "Result",
    "SolutionEntry",
    "Table",
    "Template",
    "accounting_year",
    "allocate",
    "anomaly_codes",
    "bic",
    "build_bundle",
    "derive_seed",
    "document",
    "generate_recipe",
    "generate_table",
    "generate_templates",
    "get_template",
    "iban",
    "parse_config",
    "parse_recipe",
    "plant_anomalies",
    "quantize",
    "recipe_document",
    "run_checks",
    "share",
    "split_random",
    "template_recipe",
    "templates",
    "vat_id",
]
