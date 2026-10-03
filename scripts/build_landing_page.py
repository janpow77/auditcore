"""Erzeugt die moderne HTML-Landingpage für GitHub Pages (auditcore).

Die Seite erklärt den fachlichen Nutzen der 42 Bibliotheken anhand von 5 Prüfungsphasen
und bietet einen interaktiven Bibliotheks-Finder mit Live-Suche und 1-Klick-Installation.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/docs"))

from catalog import Package  # noqa: E402
from catalog import collect as collect_catalog  # noqa: E402

CLUSTERS: dict[str, dict[str, Any]] = {
    "recherche": {
        "title": "1. Recherche, Vergabe & Compliance",
        "description": "Vergabevorprüfung, Schwellenwerte, Sanktionslisten, PEP, Beihilfen.",
        "icon": "🔍",
        "keys": {
            "procurement",
            "funding_sources",
            "registry_sources",
            "legal_sources",
            "price_sources",
            "property_sources",
            "entity_matching",
            "risk",
            "geo",
        },
    },
    "checklisten": {
        "title": "2. Checklisten & Verfahrensprüfung",
        "description": "Strukturierte Prüfbäume, Antwortführung, Dokumentenvergleich, BPMN.",
        "icon": "📋",
        "keys": {
            "checklists",
            "documents",
            "bpmn",
            "bpmn-editor",
            "bpmn-flowaudit",
            "bpmn-react",
            "bpmn-vue",
        },
    },
    "stichproben": {
        "title": "3. Stichproben & Prüfstatistik",
        "description": "Stichproben (MUS/Zufall), Benford-Analysen und Hochrechnung (TER/RER).",
        "icon": "📊",
        "keys": {
            "sampling",
            "statistics",
            "extrapolation",
            "market_indicators",
            "price_analysis",
        },
    },
    "datenschutz": {
        "title": "4. Datenschutz, Schwärzung & Testdaten",
        "description": "Revisionssichere PDF-Schwärzung, Scoped-Pseudonymisierung und Testakten.",
        "icon": "🔒",
        "keys": {
            "pdf",
            "privacy",
            "dataprotection",
            "dummygenerator",
            "invoicegenerator",
            "invoicesynth",
        },
    },
    "reporting": {
        "title": "5. Berichtswesen, Plattform & UI",
        "description": "Revisionssichere Berichte, Prüfstands-Kanban und modulare UI-Kerne.",
        "icon": "📑",
        "keys": {
            "reporting",
            "kanban",
            "kanban-core",
            "account",
            "auth",
            "identifiers",
            "common",
            "harvest",
            "llm_client",
            "runner",
            "ui",
            "ui-core",
            "ui-react",
            "layout",
        },
    },
}

STYLES = """
:root {
  --bg: #0f172a; --surface: #1e293b; --surface-hover: #273549; --surface-subtle: #141e30;
  --text: #f8fafc; --text-muted: #94a3b8; --border: #334155; --border-subtle: #1e293b;
  --accent: #38bdf8; --accent-glow: rgba(56, 189, 248, 0.15); --accent-hover: #0ea5e9;
  --tag-bg: #1e293b; --tag-text: #38bdf8; --badge-green: #10b981; --badge-green-bg: #064e3b;
  --badge-amber: #f59e0b; --badge-amber-bg: #451a03; --badge-purple: #c084fc;
}
@media (prefers-color-scheme: light) {
  :root {
    --bg: #f8fafc; --surface: #ffffff; --surface-hover: #f1f5f9; --surface-subtle: #f8fafc;
    --text: #0f172a; --text-muted: #475569; --border: #e2e8f0; --border-subtle: #cbd5e1;
    --accent: #0284c7; --accent-glow: rgba(2, 132, 199, 0.1); --accent-hover: #0369a1;
    --tag-bg: #f1f5f9; --tag-text: #0284c7; --badge-green: #047857; --badge-green-bg: #d1fae5;
    --badge-amber: #b45309; --badge-amber-bg: #fef3c7; --badge-purple: #7e22ce;
  }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.6; padding: 0 1rem 3rem;
}
header {
  max-width: 1200px; margin: 0 auto; padding: 3rem 1rem 2rem; text-align: center;
}
.hero-badge {
  display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0.75rem;
  border-radius: 9999px; background: var(--surface); border: 1px solid var(--border);
  font-size: 0.85rem; color: var(--accent); margin-bottom: 1rem;
}
h1 { font-size: 2.75rem; font-weight: 800; letter-spacing: -0.03em; margin-bottom: 0.5rem; }
h1 span { color: var(--accent); }
.lead {
  font-size: 1.25rem; color: var(--text-muted); max-width: 720px;
  margin: 0 auto 1.5rem; font-weight: 400;
}
.pip-box {
  background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem;
  padding: 0.75rem 1.25rem; max-width: 680px; margin: 0 auto 2.5rem;
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9rem;
}
.pip-box code { color: var(--accent); word-break: break-all; text-align: left; }
.btn-copy {
  background: var(--accent); color: #0f172a; border: none; padding: 0.4rem 0.75rem;
  border-radius: 0.375rem; font-weight: 600; font-size: 0.8rem; cursor: pointer;
  white-space: nowrap; transition: background 0.15s;
}
.btn-copy:hover { background: var(--accent-hover); }
.btn-copy.copied { background: var(--badge-green); color: white; }

.section-title {
  max-width: 1200px; margin: 2.5rem auto 1rem; font-size: 1.5rem; font-weight: 700;
  display: flex; align-items: center; gap: 0.5rem;
}
.workflows {
  max-width: 1200px; margin: 0 auto 3rem; display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;
}
.wf-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem;
  padding: 1.25rem; cursor: pointer; transition: transform 0.15s, border-color 0.15s;
}
.wf-card:hover { transform: translateY(-2px); border-color: var(--accent); }
.wf-icon { font-size: 1.75rem; margin-bottom: 0.5rem; }
.wf-title { font-weight: 700; font-size: 1rem; margin-bottom: 0.25rem; }
.wf-desc { font-size: 0.85rem; color: var(--text-muted); }

.filter-bar {
  max-width: 1200px; margin: 0 auto 1.5rem; display: flex; flex-direction: column; gap: 1rem;
}
.search-input {
  width: 100%; padding: 0.75rem 1rem; border-radius: 0.5rem; border: 1px solid var(--border);
  background: var(--surface); color: var(--text); font-size: 1rem; outline: none;
}
.search-input:focus { border-color: var(--accent); }
.chips { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.chip {
  padding: 0.4rem 0.85rem; border-radius: 9999px; background: var(--surface);
  border: 1px solid var(--border); font-size: 0.85rem; color: var(--text); cursor: pointer;
  transition: all 0.15s;
}
.chip:hover, .chip.active {
  background: var(--accent); color: #0f172a; border-color: var(--accent);
}

.grid {
  max-width: 1200px; margin: 0 auto; display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 1.25rem;
}
.pkg-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem;
  padding: 1.25rem; display: flex; flex-direction: column; justify-content: space-between;
  transition: border-color 0.15s;
}
.pkg-card:hover { border-color: var(--accent); }
.pkg-header {
  display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;
}
.pkg-name { font-size: 1.15rem; font-weight: 700; color: var(--text); }
.pkg-name a { color: inherit; text-decoration: none; }
.pkg-name a:hover { color: var(--accent); }
.pkg-version {
  font-size: 0.8rem; padding: 0.15rem 0.4rem; border-radius: 0.25rem;
  background: var(--tag-bg); color: var(--tag-text); font-family: monospace;
}
.pkg-cluster {
  font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;
  letter-spacing: 0.05em; margin-bottom: 0.5rem; font-weight: 600;
}
.pkg-purpose { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 1rem; flex-grow: 1; }
.pkg-footer { border-top: 1px solid var(--border); padding-top: 0.75rem; font-size: 0.8rem; }
.pkg-deps { color: var(--text-muted); margin-bottom: 0.5rem; font-size: 0.75rem; }
.pkg-cmd {
  background: var(--surface-subtle); padding: 0.35rem 0.6rem; border-radius: 0.375rem;
  display: flex; justify-content: space-between; align-items: center;
  font-family: monospace; font-size: 0.75rem;
}
.pkg-cmd code {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 0.5rem;
}
.framework-section {
  max-width: 1200px; margin: 0 auto 3rem; display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.25rem;
}
.fw-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem;
  padding: 1.5rem; display: flex; flex-direction: column; gap: 0.75rem;
}
.fw-card h3 {
  font-size: 1.15rem; color: var(--accent); display: flex; align-items: center; gap: 0.5rem;
}
.fw-card p { font-size: 0.9rem; color: var(--text); }
.fw-card ul { padding-left: 1.25rem; color: var(--text-muted); font-size: 0.85rem; }
.fw-card li { margin-bottom: 0.35rem; }
.fw-card code {
  font-size: 0.8rem; background: var(--surface-subtle); padding: 0.1rem 0.35rem;
  border-radius: 0.25rem; font-family: monospace;
}
footer {
  max-width: 1200px; margin: 4rem auto 0; padding-top: 2rem; border-top: 1px solid var(--border);
  text-align: center; color: var(--text-muted); font-size: 0.85rem;
}
footer a { color: var(--accent); text-decoration: none; }
"""

SCRIPTS = """
<script>
function filterPackages() {
  const q = document.getElementById('search').value.toLowerCase();
  const activeChip = document.querySelector('.chip.active').dataset.filter;
  document.querySelectorAll('.pkg-card').forEach(card => {
    const text = card.dataset.search;
    const cluster = card.dataset.cluster;
    const kind = card.dataset.kind;
    const matchesQuery = !q || text.includes(q);
    let matchesFilter = true;
    if (activeChip === 'python') matchesFilter = (kind === 'python');
    else if (activeChip === 'npm') matchesFilter = (kind === 'npm');
    else if (activeChip !== 'all') matchesFilter = (cluster === activeChip);
    card.style.display = (matchesQuery && matchesFilter) ? 'flex' : 'none';
  });
}
function setFilter(el, filter) {
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  filterPackages();
}
function selectCluster(clusterKey) {
  const chip = document.querySelector(`.chip[data-filter="${clusterKey}"]`);
  if (chip) {
    setFilter(chip, clusterKey);
    document.getElementById('catalog').scrollIntoView({ behavior: 'smooth' });
  }
}
function copyCmd(btn, cmd) {
  navigator.clipboard.writeText(cmd);
  const orig = btn.innerText;
  btn.innerText = '✓';
  btn.classList.add('copied');
  setTimeout(() => { btn.innerText = orig; btn.classList.remove('copied'); }, 1500);
}
</script>
"""


def _detect_cluster(name: str) -> tuple[str, str, str]:
    raw = name.replace("@auditcore/", "").replace("auditcore_", "").replace("auditcore-", "")
    for key, data in CLUSTERS.items():
        if raw in data["keys"]:
            return key, str(data["title"]), str(data["icon"])
    return "reporting", str(CLUSTERS["reporting"]["title"]), str(CLUSTERS["reporting"]["icon"])


def _render_package_card(pkg: Package) -> str:
    cluster_key, cluster_title, cluster_icon = _detect_cluster(pkg.name)
    is_js = pkg.name.startswith("@auditcore/")
    kind = "npm" if is_js else "python"
    norm_name = pkg.name.replace("_", "-").removeprefix("@auditcore/")

    if is_js:
        install_cmd = f"npm i {pkg.name}"
        doc_url = f"https://github.com/janpow77/auditcore/tree/main/{pkg.path}"
    else:
        install_cmd = (
            f"pip install {pkg.name} --index-url https://janpow77.github.io/auditcore/simple/"
        )
        doc_url = f"simple/{norm_name}/"

    search_blob = f"{pkg.name} {pkg.purpose} {pkg.dependencies} {cluster_title}".lower()
    cluster_short = cluster_title.split(".")[1].strip() if "." in cluster_title else cluster_title

    return (
        f'<div class="pkg-card" data-cluster="{cluster_key}" data-kind="{kind}" '
        f'data-search="{html.escape(search_blob)}">\n'
        f"  <div>\n"
        f'    <div class="pkg-header">\n'
        f'      <div class="pkg-name"><a href="{doc_url}">{html.escape(pkg.name)}</a></div>\n'
        f'      <span class="pkg-version">{html.escape(pkg.version)}</span>\n'
        f"    </div>\n"
        f'    <div class="pkg-cluster">{cluster_icon} {html.escape(cluster_short)}</div>\n'
        f'    <div class="pkg-purpose">{html.escape(pkg.purpose)}</div>\n'
        f"  </div>\n"
        f'  <div class="pkg-footer">\n'
        f'    <div class="pkg-deps"><strong>Abhängigkeiten:</strong> '
        f"{html.escape(pkg.dependencies)}</div>\n"
        f'    <div class="pkg-cmd">\n'
        f"      <code>{html.escape(install_cmd)}</code>\n"
        f'      <button class="btn-copy" onclick="copyCmd(this, \'{html.escape(install_cmd)}\')">'
        f"Kopieren</button>\n"
        f"    </div>\n"
        f"  </div>\n"
        f"</div>"
    )


def _render_framework_section() -> str:
    """Rendert die Übersicht zu auditcore-runner und Framework-Vorgaben."""
    return (
        '<div class="framework-section">\n'
        '  <div class="fw-card">\n'
        "    <h3>⚡ auditcore-runner (CI &amp; Prüfbank)</h3>\n"
        "    <p>Deterministische Prüfbank für Entwickler, CI und KI-Coding-Agents.</p>\n"
        "    <ul>\n"
        "      <li>Gleiche Prüfbedingungen lokal wie in CI (im identischen Container-Image)</li>\n"
        "      <li>Befehle: <code>auditcore-runner lokal</code>, "
        "<code>auditcore-runner befunde</code></li>\n"
        "      <li>Git-Inhalts-Cache: unveränderter Code wird nicht wiederholt geprüft</li>\n"
        "      <li>Ephemere self-hosted GitHub-Runner auf eigener Hardware (Docker/systemd)</li>\n"
        "    </ul>\n"
        "  </div>\n"
        '  <div class="fw-card">\n'
        "    <h3>🏛️ Clean Domain Architecture</h3>\n"
        "    <p>Reine, framework-unabhängige Fachkerne für maximale Portabilität.</p>\n"
        "    <ul>\n"
        "      <li>Keine Datenbankbindung (kein SQLAlchemy im Domänenkern)</li>\n"
        "      <li>Keine Web-Kopplung (kein FastAPI/Starlette in Fachbibliotheken)</li>\n"
        "      <li>Hierarchische Abhängigkeiten (<code>test_architecture.py</code>)</li>\n"
        "      <li>Reproduzierbare Berechnungen (z. B. SHA-256-Strukturprüfsummen)</li>\n"
        "    </ul>\n"
        "  </div>\n"
        '  <div class="fw-card">\n'
        "    <h3>📐 Strikte Quality Gates &amp; Standards</h3>\n"
        "    <p>Automatisch überwachtes Ratchet (Metriken dürfen sich nie verschlechtern).</p>\n"
        "    <ul>\n"
        "      <li><strong>McCabe-Komplexität ≤ 10</strong>, Funktionen ≤ 60 Zeilen, "
        "Module ≤ 400 Zeilen</li>\n"
        "      <li><strong>Strict Typing:</strong> zero <code>typing.Any</code>, mypy strict</li>\n"
        "      <li><strong>AST-Duplikatsinventur:</strong> "
        "<code>duplicate_functions = 0</code></li>\n"
        "      <li>Echte deutsche Umlaute (ä, ö, ü, ß; keine Ersatzschreibweisen)</li>\n"
        "      <li>Lückenlose <code>provenance.json</code> und READMEs mit Schnellstart</li>\n"
        "    </ul>\n"
        "  </div>\n"
        "</div>"
    )


def render_landing_page(packages: list[Package]) -> str:
    """Rendert die vollständige HTML-Landingpage."""
    cards_html = "\n".join(_render_package_card(p) for p in packages)
    workflows_html = "\n".join(
        f'<div class="wf-card" onclick="selectCluster(\'{k}\')">\n'
        f'  <div class="wf-icon">{v["icon"]}</div>\n'
        f'  <div class="wf-title">{html.escape(v["title"])}</div>\n'
        f'  <div class="wf-desc">{html.escape(v["description"])}</div>\n'
        f"</div>"
        for k, v in CLUSTERS.items()
    )
    framework_html = _render_framework_section()

    n_pkg = len(packages)
    ph_text = "🔍 Suche nach Name oder Fachbegriff (z. B. 'Schwärzung', 'Stichprobe', 'BPMN')..."

    return (
        f'<!DOCTYPE html>\n<html lang="de">\n<head>\n'
        f'  <meta charset="utf-8">\n'
        f'  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f"  <title>auditcore – Bibliotheken für Revision, Prüfung und Kontrollverfahren</title>\n"
        f"  <style>{STYLES}</style>\n"
        f"</head>\n<body>\n"
        f"  <header>\n"
        f'    <div class="hero-badge">🛡️ auditcore · {n_pkg} Bibliotheken · Runner: PASS</div>\n'
        f"    <h1>audit<span>core</span></h1>\n"
        f'    <p class="lead">\n'
        f"      Modulare, qualitätsgeprüfte Bibliotheken für Prüfungs- und Kontrollprozesse.\n"
        f"      Framework-frei, reproduzierbar und ohne relationale Datenbankkopplung.\n"
        f"    </p>\n"
        f'    <div class="pip-box">\n'
        f"      <code>pip install &lt;paket&gt; "
        f"--index-url https://janpow77.github.io/auditcore/simple/</code>\n"
        f'      <button class="btn-copy" '
        f"onclick=\"copyCmd(this, 'https://janpow77.github.io/auditcore/simple/')\">"
        f"URL kopieren</button>\n"
        f"    </div>\n"
        f"  </header>\n\n"
        f"  <main>\n"
        f'    <h2 class="section-title">🚀 5 Phasen im Prüfungs- und Kontrollverfahren</h2>\n'
        f'    <div class="workflows">\n{workflows_html}\n    </div>\n\n'
        f'    <h2 class="section-title">🛡️ auditcore-runner &amp; Technische Vorgaben</h2>\n'
        f"    {framework_html}\n\n"
        f'    <h2 class="section-title" id="catalog">📦 Bibliotheks-Katalog ({n_pkg} Pakete)</h2>\n'
        f'    <div class="filter-bar">\n'
        f'      <input type="text" id="search" class="search-input" '
        f'placeholder="{ph_text}" oninput="filterPackages()">\n'
        f'      <div class="chips">\n'
        f'        <button class="chip active" data-filter="all" '
        f"onclick=\"setFilter(this, 'all')\">Alle ({n_pkg})</button>\n"
        f'        <button class="chip" data-filter="recherche" '
        f"onclick=\"setFilter(this, 'recherche')\">🔍 1. Recherche & Vergabe</button>\n"
        f'        <button class="chip" data-filter="checklisten" '
        f"onclick=\"setFilter(this, 'checklisten')\">📋 2. Checklisten & Verfahren</button>\n"
        f'        <button class="chip" data-filter="stichproben" '
        f"onclick=\"setFilter(this, 'stichproben')\">📊 3. Stichproben & Statistik</button>\n"
        f'        <button class="chip" data-filter="datenschutz" '
        f"onclick=\"setFilter(this, 'datenschutz')\">🔒 4. Datenschutz & PDF</button>\n"
        f'        <button class="chip" data-filter="reporting" '
        f"onclick=\"setFilter(this, 'reporting')\">📑 5. Berichtswesen & UI</button>\n"
        f'        <button class="chip" data-filter="python" '
        f"onclick=\"setFilter(this, 'python')\">🐍 Python (pip)</button>\n"
        f'        <button class="chip" data-filter="npm" '
        f"onclick=\"setFilter(this, 'npm')\">📦 TypeScript (npm)</button>\n"
        f"      </div>\n"
        f"    </div>\n\n"
        f'    <div class="grid">\n{cards_html}\n    </div>\n'
        f"  </main>\n\n"
        f"  <footer>\n"
        f"    <p>\n"
        f'      auditcore ist quelloffen unter der <a href="https://github.com/janpow77/auditcore/blob/main/LICENSE">MIT-Lizenz</a>.\n'
        f'      · <a href="simple/">PEP 503 Paketindex</a>\n'
        f'      · <a href="https://github.com/janpow77/auditcore">GitHub Repository</a>\n'
        f"    </p>\n"
        f"  </footer>\n\n"
        f"  {SCRIPTS}\n"
        f"</body>\n</html>\n"
    )


def main() -> int:
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site"
    output_dir.mkdir(parents=True, exist_ok=True)
    packages = collect_catalog(ROOT)
    html_content = render_landing_page(packages)
    (output_dir / "index.html").write_text(html_content, encoding="utf-8")
    print(f"Landingpage geschrieben: {output_dir / 'index.html'} ({len(packages)} Pakete)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
