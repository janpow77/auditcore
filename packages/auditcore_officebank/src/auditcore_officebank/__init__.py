"""auditcore_officebank – Office-, VBA- und VM-Prüfbank.

Fassung 0.1.0 ist das Gerüst (Etappe 0): Rechnerprofil und Projektdatei mit
Schemaversion, Ausgabe-Maskierung, Gast-Schnittstelle mit Fake und CLI-Rahmen.
Gates, VM-Steuerung, Office-Automation, Build, Abnahme und Lieferung folgen in
den Etappen 1–6 (``docs/projekt/20261005_Plan_auditcore_officebank_0.1.md``).
"""

from __future__ import annotations

from .config import (
    HOST_SCHEMA,
    PROJECT_SCHEMA,
    Endpoint,
    HostProfile,
    ProjectConfig,
    SecretRef,
    load_host_profile,
    load_project,
    parse_host_profile,
    parse_project,
)
from .errors import ConfigError, OfficebankError, StageNotImplemented
from .masking import mask_secrets
from .stages import STAGES, Stage, require, stage_of

__version__ = "0.1.0"

__all__ = [
    "HOST_SCHEMA",
    "PROJECT_SCHEMA",
    "STAGES",
    "ConfigError",
    "Endpoint",
    "HostProfile",
    "OfficebankError",
    "ProjectConfig",
    "SecretRef",
    "Stage",
    "StageNotImplemented",
    "__version__",
    "load_host_profile",
    "load_project",
    "mask_secrets",
    "parse_host_profile",
    "parse_project",
    "require",
    "stage_of",
]
