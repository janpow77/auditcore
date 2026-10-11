"""Export profiles and the public-export guard (catalogue 10.3, T-22).

Nothing is published automatically. A public pattern keeps only the abstract
structure; any other content for the public needs an explicit approval and a
scan without findings (e-mail addresses, URLs, IP addresses, secrets). The
scan is a safety net, not proof that a document is free of personal data.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from enum import StrEnum

from .errors import ConflictError

PLACEHOLDER = "‹auszufüllen›"


class ExportProfile(StrEnum):
    """Export profiles with their own audience."""

    INTERNAL = "internes_vvt"
    REVIEW_PACKAGE = "pruefpaket"
    EXCHANGE = "austausch"
    PUBLIC_PATTERN = "oeffentliches_muster"


_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("E-Mail-Adresse", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("URL", re.compile(r"\b(?:https?|ftp|file|smb)://\S+", re.IGNORECASE)),
    ("IP-Adresse", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("privater Schlüssel", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "Zugangsdaten",
        re.compile(r"(?i)\b(?:passwor[dt]|kennwort|secret|token|api[_-]?key)\s*[:=]\s*\S+"),
    ),
    ("Zugangstoken", re.compile(r"\b(?:ghp|gho|github_pat|xox[bpa]|AKIA)[A-Za-z0-9_-]{8,}")),
    ("Telefonnummer", re.compile(r"(?<!\d)(?:\+49|0)\d[\d /-]{6,}\d")),
)


def _strings(value: object, path: str) -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, Mapping):
        return [p for k, v in value.items() for p in _strings(v, f"{path}.{k}")]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [p for i, v in enumerate(value) for p in _strings(v, f"{path}[{i}]")]
    return []


def public_findings(document: object) -> tuple[str, ...]:
    """Places that must not appear in a public document."""
    findings: list[str] = []
    for path, text in _strings(document, "dokument"):
        for label, pattern in _PATTERNS:
            if pattern.search(text):
                findings.append(f"{path}: {label}")
    return tuple(findings)


def public_pattern(content: Mapping[str, object]) -> dict[str, object]:
    """Abstract structure of a register: keys only, every value a placeholder."""

    def blank(value: object) -> object:
        if isinstance(value, Mapping):
            return {str(k): blank(v) for k, v in value.items()}
        if isinstance(value, list):
            return [blank(value[0])] if value else []
        return PLACEHOLDER

    return {"art": ExportProfile.PUBLIC_PATTERN.value, "struktur": blank(content)}


def release_for_public(
    document: Mapping[str, object], *, approved_by: str, approval: str
) -> dict[str, object]:
    """Deliberate, approved publication of a document without scan findings."""
    if not approved_by.strip() or not approval.strip():
        raise ConflictError(
            "Eine Veröffentlichung braucht eine ausdrückliche, dokumentierte Freigabe."
        )
    findings = public_findings(document)
    if findings:
        raise ConflictError("Nicht veröffentlichungsfähig: " + "; ".join(findings[:10]))
    return {**document, "veroeffentlichung": {"freigegeben_von": approved_by, "freigabe": approval}}
