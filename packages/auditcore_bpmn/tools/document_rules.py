"""Erzeugt ``docs/rules.md`` aus dem Meldungskatalog und den Profilen.

python tools/document_rules.py docs/rules.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auditcore_bpmn.profiles import load_profile  # noqa: E402
from auditcore_bpmn.validation import MESSAGES  # noqa: E402
from auditcore_bpmn.validation.messages import SEVERITY_LABELS  # noqa: E402
from auditcore_bpmn.vocabulary import label  # noqa: E402

GROUPS = {
    "structure": "Struktur",
    "content": "Fachliche Angaben",
    "audit_authority": "Prüfbehörden-Funktionen",
    "segregation": "Funktionstrennung (Meldungsvorlagen)",
    "collection": "Diagrammsammlung",
}


def render() -> str:
    lines = [
        "# Prüfregeln von auditcore_bpmn",
        "",
        "Erzeugt mit `tools/document_rules.py`. Die IDs sind stabil. Platzhalter in",
        "geschweiften Klammern füllt die Prüfung. Schweregrade: Fehler, Warnung, Hinweis.",
        "",
    ]
    for group, title in GROUPS.items():
        lines += [f"## {title}", "", "| ID | Schwere | Meldung (de) | Message (en) |", "|---|---|---|---|"]
        for message in MESSAGES.values():
            if message.group == group:
                severity = label(SEVERITY_LABELS[message.severity])
                lines.append(f"| `{message.id}` | {severity} | {message.de} | {message.en} |")
        lines.append("")
    lines += [
        "## Funktionstrennung im Profil `foerderperiode-2021-2027`",
        "",
        "| ID | Art | Schwere | Regel |",
        "|---|---|---|---|",
    ]
    for rule in load_profile().segregation_rules:
        lines.append(f"| `BPMN-{rule.id}` | `{rule.kind}` | {rule.severity} | {label(rule.title)} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    main()
