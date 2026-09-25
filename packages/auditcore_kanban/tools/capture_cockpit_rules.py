"""Characterize the cockpit board rules by executing the original functions with node.

    python -I tools/capture_cockpit_rules.py /path/to/cockpit \
        tests/fixtures/cockpit_rules_observed.json

``spalteVon`` (labels.ts) and ``darfVerschieben`` (KanbanView.vue) are cut from
the pinned commit (blob SHAs checked); only their TypeScript type annotations
are removed before node runs them. The backend rule (status change of a running
job -> 409) and the ordering gap (+10) are recorded as source lines.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

COMMIT = "df203d4c33e786eb8a8ad3fe53b3b7eb9241d406"
FILES = {
    "labels": ("frontend/src/components/kanban/labels.ts",
               "c98320f5940692d78d37f1041634c6ecb8e4f960"),
    "view": ("frontend/src/views/KanbanView.vue", "7e86a8d4b7f437dcdfb3bbf55335a5cd13b38df8"),
    "routes": ("src/cockpit/routes/auftraege.py", "666cb4f184d4259de7a2cd733b217766a3db8b5d"),
    "service": ("src/cockpit/services/auftraege.py", "14ad907a101413df73ea9bd06fcc7e301761cd7b"),
}
STATUSES = ["eingang", "geplant", "laeuft", "rueckfrage", "freigabe", "unterbrochen", "fertig",
            "fehler", "abgebrochen"]
COLUMNS = ["eingang", "geplant", "laeuft", "rueckfrage", "fertig"]


def show(repo: Path, key: str) -> str:
    path, blob = FILES[key]
    actual = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{COMMIT}:{path}"],
                            capture_output=True, text=True, check=True).stdout.strip()
    if actual != blob:
        raise SystemExit(f"blob mismatch {path}")
    return subprocess.run(["git", "-C", str(repo), "show", f"{COMMIT}:{path}"],
                          capture_output=True, text=True, check=True).stdout


def function(source: str, name: str) -> str:
    match = re.search(rf"(export )?function {name}\(.*?\n}}\n", source, re.S)
    if match is None:
        raise SystemExit(f"{name} not found")
    code = match.group(0).removeprefix("export ")
    return re.sub(r"\)\s*:\s*\w+\s*{", ") {", re.sub(r"(\w+)\s*:\s*\w+([,)])", r"\1\2", code))


def main() -> None:
    repo, output = Path(sys.argv[1]), Path(sys.argv[2])
    labels, view = show(repo, "labels"), show(repo, "view")
    script = "\n".join([
        function(labels, "spalteVon"), function(view, "darfVerschieben"),
        f"const S = {json.dumps(STATUSES)}, C = {json.dumps(COLUMNS)};",
        "const out = {spalteVon: {}, darfVerschieben: {}};",
        "for (const s of S) out.spalteVon[s] = spalteVon(s);",
        "for (const s of S) { out.darfVerschieben[s] = {};"
        " for (const c of C) out.darfVerschieben[s][c] = darfVerschieben({status: s}, c); }",
        "console.log(JSON.stringify(out));",
    ])
    observed = json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True,
                                         check=True).stdout)
    routes, service = show(repo, "routes"), show(repo, "service")
    observed["source_lines"] = {
        "running_status_change": next(line.strip() for line in routes.splitlines()
                                      if 'a.status == "laeuft"' in line),
        "running_status_change_error": next(line.strip() for line in routes.splitlines()
                                            if "Laufender Auftrag" in line),
        "order_gap": next(line.strip() for line in service.splitlines() if "+ 10" in line),
    }
    document = {
        "source": {"repository": "janpow77/cockpit", "commit": COMMIT,
                   "files": [{"path": p, "git_blob": b} for p, b in FILES.values()]},
        "tool": "tools/capture_cockpit_rules.py",
        "observed": observed,
    }
    output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("cockpit rules ->", output)


if __name__ == "__main__":
    main()
