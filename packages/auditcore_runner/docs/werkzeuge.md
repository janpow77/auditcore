# Prüfbank: Werkzeuge, Prüfprofile, Befunde

## Ablauf

1. **Autofix** ohne Modell (`lokal <profil> --beheben`): die Fixer der
   Werkzeuge im Profil (ruff, eslint, prettier, stylelint, markdownlint,
   codespell, typos, prek …).
2. **Codemods** ohne Modell: `ast-grep scan --update-all` (Regeln aus
   `sgconfig.yml`), dazu die Codemods aus `[codemods]` der Repo-Datei
   (libcst-Klassen, beliebige Befehle). Sie laufen nach den Autofixern.
3. **Prüfen**: `auditcore-runner lokal <profil>` führt die Werkzeuge im
   Runner-Image aus (`--host`: mit den Werkzeugen des Rechners). Cache je
   Werkzeug über `(werkzeug, version, konfigurations-hash, git-inhalt des pfads)`
   – identischer Inhalt wird nicht erneut geprüft. Ein Werkzeug mit
   Dateimuster (`applies_to`) entfällt, wenn das Repository keine passende
   Datei hat. Ohne Netz (`--network none`) laufen alle Werkzeuge außer
   osv-scanner, grype, trivy (Schwachstellen-Datenbanken), lychee-online und prek.
4. **Befunde**: `auditcore-runner befunde` – einheitliches Modell (Werkzeug,
   Regel, Datei:Zeile, Schwere, Fingerabdruck, Autofix ja/nein), dedupliziert,
   Pfade relativ zum Repository; `--baseline` zeigt nur neue Befunde
   (Fingerabdruck ohne Zeilennummer), `--sarif` für Code Scanning, `--budget`
   begrenzt den Bericht.
5. **Aufgabenpaket**: `befunde --aufgabenpaket datei.md` – nur Befunde, die
   kein Fixer lösen konnte; je Befund Datei:Zeile, Regel, Auszug und
   Fix-Hinweis (je Regel oder je Werkzeug); dazu der empfohlene headless-Aufruf
   (`claude -p … --max-budget-usd …` bzw. `codex exec --json`) mit Budget und
   Runden. Kopfzeile `# Aufgabenpaket <id> (<typ>)`, höchstens 60 000 Zeichen
   (Rest folgt im nächsten Paket) – passend zu Vorlagen wie `befunde-beheben`
   einer Steuerung. Ausgeführt wird nichts.

Vor dem Push: `auditcore-runner hook --schreiben` legt eine prek/pre-commit-
Konfiguration an (`prek install --hook-type pre-push`).

## Katalog

Alle Programme liegen fest gepinnt im Runner-Image (`data/werkzeuge/`:
Binärdateien mit SHA-256, Python- und Node-Werkzeuge mit Lockfile; Dependabot
hält pip und npm aktuell). Lizenzen: `THIRD_PARTY.md`.

| Werkzeug | Bereich | Parser | Autofix/Stufe | Netz |
|---|---|---|---|---|
| ruff (mit S- und D-Regeln) | python | ruff-json | ja | – |
| mypy, pyrefly | python | mypy-text, pyrefly-json | – | – |
| pytest, pytest-testmon, pytest-split-1v2/2v2 | python | junit-xml | – | – |
| pytest-gpu (`-m gpu`, Kosten: GPU) | gpu | junit-xml | – | – |
| vulture, deptry | python | vulture-text, deptry-json | – | – |
| mutmut | python | mutmut-text (überlebende Mutanten) | – | – |
| diff-cover | python | diff-cover-json (ungetestete Änderungen) | – | – |
| import-linter | struktur | import-linter-text | – | – |
| codegate | struktur | codegate-json (nur in auditcore-Repos) | – | – |
| jscpd | struktur | jscpd-json | – | – |
| ast-grep | struktur | ast-grep-json | Codemod | – |
| prek | struktur | – (nur Hooks) | Autofix | ja |
| gitleaks, betterleaks | sicherheit | gitleaks-Format (Geheimnis wird nie übernommen) | – | – |
| Opengrep (Regeln aus `.opengrep/`) | sicherheit | SARIF | – | – |
| osv-scanner, grype, trivy | sicherheit | SARIF | – | ja |
| syft | sicherheit | – (SBOM `sbom.spdx.json`) | – | – |
| zizmor, actionlint | sicherheit | SARIF, actionlint-json | – | – |
| codespell, typos | doku | codespell-text, typos-json | Autofix | – |
| markdownlint | doku | markdownlint-json | Autofix | – |
| lychee / lychee-online | doku | lychee-json | – | – / ja |
| eslint, prettier, stylelint | js | eslint-json, prettier-text, stylelint-json | ja / Autofix | – |
| tsc, vitest, knip, size-limit | js | tsc-text, vitest-junit, knip-json, size-limit-json | – | – |
| playwright, axe, lighthouse | gui | playwright-junit, axe-junit, lighthouse-json | – | – |

Befehle, die Projektabhängigkeiten brauchen (tsc, vitest, Playwright,
pytest-Plugins), nutzen die Installation des Projekts und fallen sonst auf die
Kopie im Image zurück. Weitere Werkzeuge werden als `Tool` (Befehl, Parser,
Autofix, Stufe, Kosten, Netz, Installation) registriert. Ein
Sammel-Orchestrator lässt sich als **ein** Werkzeug mit SARIF-Ausgabe einbinden
(`external_orchestrator`). reviewdog liegt im Image, um SARIF-Berichte als
Review-Kommentare zu posten; es ist kein Prüfwerkzeug.

## GUI-Prüfungen

Die Szenarien gehören ins geprüfte Repository, nicht ins Paket:

- **playwright**: `npx playwright test` mit der `playwright.config.*` des
  Projekts; Bildvergleiche über `toHaveScreenshot` mit Baselines im Repo.
  Baselines im Runner-Image erzeugen (feste Browser, Noto-/DejaVu-Schriften),
  sonst weichen Pixel zwischen Rechnern ab. Für Parität mehrerer
  Implementierungen (etwa Vue und React) vergleichen beide Fassungen gegen
  **denselben** Baseline-Namen.
- **axe**: dieselben Szenarien mit `@axe-core/playwright`, markiert mit `@axe`.
- **lighthouse**: `lhci autorun` mit der `lighthouserc.json` des Projekts;
  Befunde sind die fehlgeschlagenen Zusicherungen. Upload-Ziel `filesystem`
  setzen – ohne Netz gibt es keinen öffentlichen Upload.

## Prüfprofile

| Profil | Auslöser | Inhalt |
|---|---|---|
| `schnell` | lokal | ruff, typos, prettier, gitleaks; Autofix an |
| `pr` | lokal, pr | Linter, Typen, Tests, Geheimnisse, Workflows, Doku, Struktur, JS – ohne Netz |
| `voll` | nacht | `pr` plus pyrefly, vulture, jscpd, diff-cover, Sicherheit und GUI |
| `gui` | lokal, pr | playwright, axe, lighthouse, stylelint, eslint, tsc |
| `sicherheit` | pr, nacht | gitleaks, betterleaks, Opengrep, osv-scanner, grype, trivy, syft, zizmor, actionlint, ruff |
| `gpu` | fuell | pytest-gpu |
| `fuell` | fuell, nacht | mutmut, pytest-split, vulture, jscpd, lychee-online, codegate |

Werkzeuge ohne passende Dateien entfallen, die Auswahl ist daher für jedes
Repository neutral. Je Repo überschreibbar in `.auditcore-runner.toml`
(Schema: `data/schemas/repo-konfiguration.schema.json`):

```toml
[pruefprofile.pr]
werkzeuge = ["ruff", "mypy", "pytest", "gitleaks"]
ausloeser = ["lokal", "pr"]        # lokal, pr, nacht, fuell
zeitlimit_s = 1800
max_befunde = 200
autofix = false

[pruefprofile.pr.werkzeug.mypy]
zeitlimit_s = 900
prioritaet = 10                    # kleiner = früher
aktiv = true

[codemods]
libcst = ["projekt.codemods.AlteApiErsetzen"]
befehle = [["python", "-m", "projekt.umschreiben"]]
```

Je Rechner schaltet die Oberfläche bzw. `~/.config/auditcore-runner/werkzeuge.json`
(`auditcore-runner/werkzeuge/1`) Werkzeuge je Profil an/aus, setzt Zeitlimit und
Priorität; das gilt vor der Repo-Datei.

## Messen

`auditcore-runner messen --repo <owner>/<repo> --tage 14` – CI-Dauern (Median,
p90, Anteil rot) und Token-Verbrauch aus Claude-Code- und Codex-Protokollen je
Arbeitsverzeichnis; `--otel-datei` wertet OTel-Metriken
(`claude_code.token.usage`, `claude_code.cost.usage`) nach `task_type` aus.
