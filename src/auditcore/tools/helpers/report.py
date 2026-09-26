"""Markdown rendering of the ``auditcore-helpers`` JSON report."""

from __future__ import annotations

from collections import Counter

from auditcore.tools.helpers.model import as_dict, as_int, as_list, as_str

MAX_ROWS = 40


def _cell(value: object) -> str:
    return as_str(value, str(value)).replace("|", "\\|").replace("\n", " ")


def _table(header: list[str], rows: list[list[object]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(_cell(item) for item in row) + " |" for row in rows[:MAX_ROWS]]
    if len(rows) > MAX_ROWS:
        lines.append(f"\n… {len(rows) - MAX_ROWS} weitere Zeilen im JSON-Bericht")
    return lines + [""]


def _scan(scan: dict[str, object]) -> list[str]:
    functions = as_dict(scan.get("functions"))
    matches = [as_dict(m) for m in as_list(scan.get("library_matches"))]
    available = [m for m in matches if m.get("status") == "vorhanden"]
    planned = Counter(as_str(m.get("topic")) for m in matches if m.get("status") != "vorhanden")
    lines = [
        "### Scan",
        "",
        f"{as_int(scan.get('files'))} Dateien, {as_int(functions.get('python'))} Python- und "
        f"{as_int(functions.get('ts'))} TS/JS/Vue-Funktionen, "
        f"{as_int(scan.get('duplicate_groups'))} Duplikatgruppen im Repository.",
        "",
        f"**Existiert schon in einer auditcore-Bibliothek: {len(available)}**",
        "",
    ]
    rows: list[list[object]] = [
        [
            f"{m.get('path')}:{m.get('line')}",
            m.get("name"),
            m.get("match"),
            f"{m.get('library')} {m.get('symbol')}",
        ]
        for m in available
    ]
    lines += _table(["Fundstelle", "Funktion", "Treffer", "Bibliothek"], rows) if rows else []
    if planned:
        summary = ", ".join(f"{topic} {count}" for topic, count in planned.most_common())
        lines += [
            f"Kandidaten für geplante Bibliotheksfunktionen (Hinweis, kein Ratchet): {summary}",
            "",
        ]
    return lines


def _lint(lint: dict[str, object]) -> list[str]:
    rules = [as_dict(r) for r in as_list(lint.get("rules"))]
    findings = [as_dict(f) for f in as_list(lint.get("findings"))]
    lines = ["### Lint", ""]
    lines += _table(
        ["Regel", "Titel", "Fundstellen"],
        [[r.get("id"), r.get("title"), r.get("findings")] for r in rules],
    )
    rows: list[list[object]] = [
        [f.get("rule"), f"{f.get('path')}:{f.get('line')}", f.get("message")] for f in findings
    ]
    lines += _table(["Regel", "Fundstelle", "Meldung"], rows) if rows else []
    probe = as_dict(lint.get("probe"))
    isolated, total = as_int(probe.get("isolated")), as_int(probe.get("candidates"))
    suppressed = len(as_list(lint.get("suppressed")))
    lines += [
        f"Ausgeführte Hilfsfunktionen (probe): {isolated} von {total} Kandidaten, übrige nicht "
        f"isoliert ausführbar. Per Kommentar unterdrückt: {suppressed}.",
        "",
    ]
    return lines


def _contracts(runs: list[object]) -> list[str]:
    lines = ["### Verträge", ""]
    if not runs:
        return lines + ["Keine Bindungen im Manifest `.auditcore/helpers.json`.", ""]
    rows: list[list[object]] = []
    details: list[str] = []
    for run in map(as_dict, runs):
        counts = as_dict(run.get("counts"))
        rows.append(
            [
                run.get("binding"),
                run.get("function"),
                counts.get("bestanden"),
                counts.get("verletzt"),
                counts.get("übersprungen"),
                run.get("load_error") or "",
            ]
        )
        details += [
            f"- `{run.get('binding')}` {as_dict(v).get('case')}: {as_dict(v).get('detail')}"
            for v in as_list(run.get("violations"))
        ]
    lines += _table(
        ["Bindung", "Funktion", "bestanden", "verletzt", "übersprungen", "Ladefehler"], rows
    )
    return lines + details[:MAX_ROWS] + [""]


def _ratchet(ratchet: dict[str, object]) -> list[str]:
    verdicts = [as_dict(v) for v in as_list(ratchet.get("verdicts"))]
    lines = [f"### Ratchet gegen `{ratchet.get('baseline')}`: {ratchet.get('status')}", ""]
    if not verdicts:
        return lines + ["Keine Abweichung von der Baseline.", ""]
    rows: list[list[object]] = [[v.get("status"), v.get("message")] for v in verdicts]
    return lines + _table(["Status", "Befund"], rows)


def render_markdown(report: dict[str, object]) -> str:
    """Render the report of any subcommand."""
    lines = [f"## Helfer-Verträge: {report.get('app')}", ""]
    status = as_dict(report.get("ratchet")).get("status")
    if status:
        lines += [f"**Gesamtstatus: {status}**", ""]
    if "scan" in report:
        lines += _scan(as_dict(report["scan"]))
    if "lint" in report:
        lines += _lint(as_dict(report["lint"]))
    if "contracts" in report:
        lines += _contracts(as_list(report["contracts"]))
    if "ratchet" in report:
        lines += _ratchet(as_dict(report["ratchet"]))
    errors = as_list(report.get("errors"))
    if errors:
        lines += ["### Hinweise", ""] + [f"- {_cell(e)}" for e in errors[:MAX_ROWS]] + [""]
    return "\n".join(lines)
