"""Ziel-JSON ``auditcore_invoice_v1`` (nur Kopf-/Summenfelder, Entscheidung E8).

Die Werte sind das **Gedruckte** (Zeichenkette wie auf dem Beleg); Normalisierung
geschieht erst in der Bewertung. Die Donut-Tokenfolge ist eine eigene
Umsetzung der Donut-Konvention ``<s_feld>wert</s_feld>``, Listen mit
``<sep/>``; der Task-Token trägt die Schemaversion.
"""

from __future__ import annotations

import re
from typing import Any

SCHEMA_VERSION = "auditcore_invoice_v1"
TASK_TOKEN = f"<s_{SCHEMA_VERSION}>"
SEPARATOR = "<sep/>"

#: Feldreihenfolge im Ziel-JSON; verschachtelte Felder als Liste der Unterschlüssel.
FIELD_ORDER: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("document_type", ()),
    ("invoice_number", ()),
    ("invoice_date", ()),
    ("supply_date", ()),
    ("due_date", ()),
    ("supplier", ("name", "vat_id")),
    ("currency", ()),
    ("net_amount", ()),
    ("vat_lines", ("rate", "base", "amount")),
    ("total", ()),
    ("iban", ()),
    ("bic", ()),
)
LIST_FIELDS = frozenset({"vat_lines"})
REQUIRED_FIELDS = ("total", "invoice_date", "invoice_number", "supplier.vat_id", "iban")


def nest_fields(flat: dict[str, str]) -> dict[str, Any]:
    """``{"supplier.name": …, "vat_lines.0.rate": …}`` → verschachteltes Ziel-JSON."""
    result: dict[str, Any] = {}
    lines: dict[int, dict[str, str]] = {}
    for key, value in flat.items():
        parts = key.split(".")
        if parts[0] == "vat_lines":
            lines.setdefault(int(parts[1]), {})[parts[2]] = value
        elif len(parts) == 2:
            result.setdefault(parts[0], {})[parts[1]] = value
        else:
            result[key] = value
    if lines:
        result["vat_lines"] = [lines[index] for index in sorted(lines)]
    return result


def special_tokens() -> list[str]:
    """Alle Zusatz-Token für den Tokenizer (Task, Feld-Tags, Trenner)."""
    tokens = [TASK_TOKEN, SEPARATOR]
    for key, children in FIELD_ORDER:
        tokens += [f"<s_{key}>", f"</s_{key}>"]
        for child in children:
            for token in (f"<s_{child}>", f"</s_{child}>"):
                if token not in tokens:
                    tokens.append(token)
    return tokens


def ordered(ground_truth: dict[str, Any]) -> dict[str, Any]:
    """Schlüssel in Schemaordnung; unbekannte Schlüssel sind ein Fehler."""
    known = {key for key, _ in FIELD_ORDER}
    unknown = set(ground_truth) - known
    if unknown:
        raise ValueError(f"Unbekannte Felder im Ziel-JSON: {sorted(unknown)}")
    result: dict[str, Any] = {}
    for key, children in FIELD_ORDER:
        if key not in ground_truth:
            continue
        value = ground_truth[key]
        if key in LIST_FIELDS:
            result[key] = [{c: item[c] for c in children if c in item} for item in value]
        elif children:
            result[key] = {c: value[c] for c in children if c in value}
        else:
            result[key] = value
    return result


def _encode(value: Any) -> str:
    if isinstance(value, dict):
        return "".join(f"<s_{k}>{_encode(v)}</s_{k}>" for k, v in value.items())
    if isinstance(value, list):
        return SEPARATOR.join(_encode(item) for item in value)
    if not isinstance(value, str):
        raise ValueError("Ziel-JSON enthält nur Zeichenketten, Objekte und Listen")
    if "<s_" in value or "</s_" in value or SEPARATOR in value:
        raise ValueError("Feldwert enthält reservierte Token")
    return value


def to_sequence(ground_truth: dict[str, Any]) -> str:
    """Ziel-JSON → Donut-Zielsequenz (ohne EOS; das setzt der Tokenizer)."""
    return TASK_TOKEN + _encode(ordered(ground_truth))


_OPEN = re.compile(r"<s_([a-z_0-9]+)>")


def _decode(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    position = 0
    while True:
        match = _OPEN.search(text, position)
        if match is None:
            break
        key = match[1]
        close = f"</s_{key}>"
        end = text.find(close, match.end())
        if end == -1:
            position = match.end()
            continue
        content = text[match.end() : end]
        position = end + len(close)
        if key in LIST_FIELDS:
            parts = content.split(SEPARATOR)
            result[key] = [_decode(part) for part in parts if _OPEN.search(part)]
        elif _OPEN.search(content):
            result[key] = _decode(content)
        else:
            result[key] = content.strip()
    return result


def from_sequence(sequence: str) -> dict[str, Any]:
    """Donut-Ausgabe → Ziel-JSON; unvollständige Tags werden übergangen."""
    text = sequence.replace("</s>", "").replace("<s>", "").replace("<pad>", "")
    text = text.replace(TASK_TOKEN, "", 1)
    return _decode(text)
