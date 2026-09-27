# Prüfbank: Werkzeuge, Prüfprofile, Befunde

## Ablauf

1. **Autofix** ohne Modell (`lokal <profil> --beheben`: ruff --fix, eslint --fix).
2. **Prüfen**: `auditcore-runner lokal <profil>` führt die Werkzeuge im
   Runner-Image aus (`--host`: mit den Werkzeugen des Rechners). Cache je
   Werkzeug über `(werkzeug, version, konfigurations-hash, git-inhalt des pfads)`
   – identischer Inhalt wird nicht erneut geprüft. Die Werkzeug-Caches (ruff,
   mypy) liegen im Volume `auditcore-runner-werkzeug-cache`.
3. **Befunde**: `auditcore-runner befunde` – dedupliziert, nach Datei gruppiert,
   eine Zeile je Befund, Token-Schätzung; `--baseline` zeigt nur neue Befunde
   (Fingerabdruck ohne Zeilennummer, Verschieben erzeugt nichts Neues),
   `--sarif` für Code Scanning, `--budget` begrenzt den Bericht.
4. **Aufgabenpaket**: `befunde --aufgabenpaket datei.md` – je Befund
   Datei:Zeile, Regel, Auszug und Hinweis; dazu der empfohlene headless-Aufruf
   (`claude -p … --max-budget-usd …` bzw. `codex exec --json`) mit
   `OTEL_RESOURCE_ATTRIBUTES=task_type=…,paket_id=…`. Ausgeführt wird nichts.

Vor dem Push: `auditcore-runner hook --schreiben` legt eine prek/pre-commit-
Konfiguration an (`prek install --hook-type pre-push`).

## Verifizierte Codemods

Strukturelle Änderungen laufen zuerst in einer temporären Kopie des sauberen
Git-Arbeitsbaums. Erst wenn alle in `auditcore-verification.json` hinterlegten
Kategorien durch `auditcore-refactor verify` mit `PASS` enden, übernimmt die
Prüfbank die geänderten Dateien in den Arbeitsbaum. Ein fehlendes Werkzeug,
eine erfolglose Transformation oder eine unvollständige Verifikation lässt das
Original unverändert.

```bash
# YAML-Regel liegt zur Review im Repository
auditcore-runner codemod ast-grep codemods/print-zu-logger.yml --pfad .

# Voll qualifizierter LibCST-Codemod; das Modul muss installiert/importierbar sein
auditcore-runner codemod libcst mein_projekt.codemods.RenameApi --pfad .
```

ast-grep, LibCST und `auditcore-refactor` werden als getrennte Programme
aufgerufen. Rezepte gehören versioniert ins Ziel-Repository; LibCST-Module sind
ausführbarer Code und müssen vor dem Lauf geprüft werden. Der Befehl lehnt einen
bereits veränderten oder unversionierte Dateien enthaltenden Arbeitsbaum ab,
damit er keine Arbeit des Benutzers überschreiben kann.

## Katalog

| Werkzeug | Bereich | Parser | Autofix |
|---|---|---|---|
| ruff (mit S- und D-Regeln) | python | ruff-json | ja |
| mypy | python | mypy-text | – |
| pytest | python | junit-xml | – |
| gitleaks | sicherheit | gitleaks-json (Geheimnis wird nie übernommen) | – |
| eslint | js | eslint-json | ja |
| zizmor | sicherheit | SARIF | – |
| actionlint | sicherheit | actionlint-json | – |
| codegate | struktur | codegate-json (nur in auditcore-Repos) | – |

Weitere Werkzeuge werden als `Tool` (Befehl, Parser, Autofix, Kosten,
Installation) registriert. Ein Sammel-Orchestrator lässt sich als **ein**
Werkzeug mit SARIF-Ausgabe einbinden (`external_orchestrator`); Normalisierung,
Baseline, Cache und Aufgabenpaket übernimmt das Paket.

## Prüfprofile

Eingebaut: `schnell`, `pr`, `voll`, `sicherheit`, `gui`, `gpu`, `fuell`. Je Repo
überschreibbar in `.auditcore-runner.toml`:

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
```

Je Rechner schaltet die Oberfläche bzw. `~/.config/auditcore-runner/werkzeuge.json`
(`auditcore-runner/werkzeuge/1`) Werkzeuge je Profil an/aus, setzt Zeitlimit und
Priorität; das gilt vor der Repo-Datei.

## Messen

`auditcore-runner messen --repo <owner>/<repo> --tage 14` – CI-Dauern (Median,
p90, Anteil rot) und Token-Verbrauch aus Claude-Code- und Codex-Protokollen je
Arbeitsverzeichnis; `--otel-datei` wertet OTel-Metriken
(`claude_code.token.usage`, `claude_code.cost.usage`) nach `task_type` aus.
