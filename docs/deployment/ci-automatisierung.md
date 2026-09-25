# CI-Automatisierung: was ohne Menschen läuft

Prüfungen und Routinekorrekturen laufen in auditcore weitgehend automatisch in
GitHub Actions (überwiegend auf den NUC-Runnern, siehe
[self-hosted-runner.md](self-hosted-runner.md)). Diese Seite beschreibt, was
automatisch passiert, wo weiterhin ein Mensch oder Claude gebraucht wird und wie
man einzelne Teile abschaltet.

## Überblick

| Baustein | Datei | Auslöser | Ergebnis |
|---|---|---|---|
| Sammel-Check `ci-ok` | `.github/workflows/ci-ok.yml` | jeder PR | grün, wenn alle übrigen Workflows des Commits grün sind |
| Autofix | `.github/workflows/autofix.yml` | PR aus diesem Repository | Commit „chore(autofix): …“ |
| Branches aktuell halten | `.github/workflows/update-pr-branches.yml` | Push auf main | Merge von main in offene PR-Branches, Label „konflikt“ |
| Dependabot | `.github/dependabot.yml` | montags 05:00 | gruppierte Update-PRs für pip, npm, GitHub Actions |
| Dependabot-Auto-Merge | `.github/workflows/dependabot-automerge.yml` | Dependabot-PR | Auto-Merge für Patch/Minor von Entwicklungswerkzeugen |
| Nächtliche Vollprüfung | `.github/workflows/nightly.yml` | täglich 01:17 UTC, manuell | Issue „Nightly rot“ anlegen/kommentieren/schließen |
| Auto-Merge (Repo) | Repo-Einstellung | `gh pr merge --auto` | Squash-Merge nach grünen Required Checks, Branch wird gelöscht |

## Required Checks und `ci-ok`

Branch-Protection auf main verlangt `code-quality-gate` und `ci-ok`.

Die Fach-Workflows `domain-packages` und `js-packages` haben Pfadfilter und
starten nur, wenn ihr Bereich betroffen ist. Direkt als Required Check würden sie
jeden PR blockieren, bei dem sie nicht starten. `ci-ok` löst das: Der Workflow
startet bei jedem PR, wartet auf alle anderen Workflow-Läufe desselben Commits
(REST `actions/runs?head_sha=…`) und ist nur grün, wenn keiner fehlschlägt.
Nicht gestartete Workflows gelten als nicht betroffen. `autofix` und
`dependabot-automerge` zählen nicht mit, weil sie nichts prüfen.

- Neue Prüf-Workflows werden automatisch mitgezählt; an der Branch-Protection
  muss dafür nichts geändert werden.
- Wird ein fehlgeschlagener Lauf von Hand neu gestartet, muss `ci-ok` ebenfalls
  neu gestartet werden („Re-run“ im Lauf von `ci-ok`).
- `ci-ok` läuft bewusst auf `ubuntu-latest` (öffentliches Repository, kostenlos),
  damit der Warte-Job keinen NUC-Runner belegt. Zeitlimit: 110 Minuten.

## Auto-Merge

Repo-Einstellungen: `allow_auto_merge=true`, `delete_branch_on_merge=true`.
PRs werden direkt nach dem Öffnen angemeldet, statt auf die CI zu warten:

```bash
gh pr merge <nr> --auto --squash
```

Auto-Merge gibt es nur über GraphQL (`enablePullRequestAutoMerge`), nicht über
REST. Ist das GraphQL-Kontingent erschöpft, die Anmeldung nach dem Reset nachholen.

## Autofix

Läuft bei jedem PR aus diesem Repository (nie bei Forks, nie bei Dependabot,
nicht bei Entwürfen) und nur für die im PR geänderten Dateien:

1. `ruff check --fix` (nur sichere Korrekturen) und `ruff format` für geänderte
   `.py`-Dateien. ruff nimmt je Datei die Konfiguration des nächstgelegenen
   `pyproject.toml`, also die des jeweiligen Pakets.
2. `eslint --fix` für geänderte Dateien in `packages-js/` und `scripts/js/`.
3. `auditcore-codegate check --update-baseline`, wenn `src/`, `packages/` oder
   `packages-js/` betroffen sind. `scripts/ci_baseline_lower_only.py` übernimmt
   davon **nur Absenkungen**. Anhebungen, neue oder entfernte Pakete, neue
   Begründungen und Werkzeugversionen bleiben unverändert; eine mypy-Metrik wird
   nur abgesenkt, wenn die mypy-Version der Baseline entspricht.

Ergibt das Änderungen, entsteht ein Commit „chore(autofix): ruff, eslint,
Baseline abgesenkt“ (je nach Inhalt) auf dem PR-Branch – vorausgesetzt, der
Deploy-Key ist eingerichtet (siehe unten).

Sicherheitsmodell:

- Kein `pull_request_target`. Der Job `fix` führt den PR-Code aus (pip-Installation,
  ESLint-Konfiguration), hat aber nur Leserechte und keine Secrets. Er erzeugt
  nur einen Patch.
- Der Job `push` führt keinen PR-Code aus. Er prüft, dass der Patch nur
  Python-Dateien, JS/TS/Vue-Dateien unter `packages-js/`/`scripts/js/` und
  `quality/baseline.json` berührt, wendet ihn an und pusht. Git-Hooks sind dabei
  abgeschaltet.
- Endlosschleife: Ist der letzte Commit ein „chore(autofix)“-Commit, läuft nichts.
  Die Korrekturen sind außerdem idempotent.

Wer lokal weiterarbeitet, holt den Autofix-Commit vor dem nächsten Push:
`git pull --no-rebase`.

## Branches aktuell halten

Nach jedem Push auf main mergt `update-pr-branches` (mit Deploy-Key) main in alle offenen PRs aus
diesem Repository (keine Entwürfe, keine Dependabot-PRs). Merge statt Rebase,
kein Force-Push. Pro Lauf höchstens 25 Aktualisierungen mit 15 Sekunden Pause.
Bei einem Konflikt bleibt der Branch unverändert, und der PR bekommt das Label
**„konflikt“**. Das Label verschwindet beim nächsten konfliktfreien Lauf.

## Deploy-Key `AUTOMATION_DEPLOY_KEY` (einmalig vom Maintainer einzurichten)

GitHub startet für Pushes mit dem `GITHUB_TOKEN` keine Workflows. Ein
Autofix-Commit oder ein aktualisierter Branch hätte dann keine CI, die Required
Checks blieben aus, und der PR hinge. Deshalb pushen `autofix` und
`update-pr-branches` nur per SSH mit einem Deploy-Key (Schreibrecht), dessen
privater Schlüssel als Actions-Secret `AUTOMATION_DEPLOY_KEY` hinterlegt ist.

**Ohne das Secret** pushen beide Workflows nichts: `autofix` legt die Korrekturen
nur als Artefakt `autofix-patch` ab (Hinweis im Lauf), `update-pr-branches`
markiert nur Konflikte mit dem Label „konflikt“ (über `mergeable_state`).

- Das Secret steht nur den Jobs `autofix/push` und `update-pr-branches/update`
  zur Verfügung. Beide führen keinen PR-Code aus. Fork-PRs erhalten keine Secrets.
- Direkte Pushes auf main verhindert die Branch-Protection auch für den Deploy-Key.
- Einrichten oder erneuern (lokal, als Maintainer):
  ```bash
  ssh-keygen -t ed25519 -N '' -C auditcore-automation -f /tmp/automation_key
  gh api -X POST repos/janpow77/auditcore/keys -f title='auditcore-automation' \
    -f key="$(cat /tmp/automation_key.pub)" -F read_only=false
  gh secret set AUTOMATION_DEPLOY_KEY --repo janpow77/auditcore < /tmp/automation_key
  shred -u /tmp/automation_key /tmp/automation_key.pub
  # alten Schlüssel entfernen: gh api repos/janpow77/auditcore/keys, dann DELETE …/keys/<id>
  ```

## Dependabot

Wöchentlich (montags 05:00 Europe/Berlin), gruppiert:

- **pip**: Root und jedes `packages/*`-Verzeichnis. Gruppen `python-dev-tools`
  (ruff, mypy, pytest*, bandit, pip-audit, build, twine, setuptools, wheel,
  coverage, types-*, cyclonedx-*) und `python-runtime` (alles andere).
- **npm**: Root-Workspace. Gruppen `npm-dev-tools` (devDependencies) und
  `npm-runtime` (dependencies).
- **github-actions**: Workflows und `.github/actions/*`, Gruppe `github-actions`.
  Actions bleiben per SHA gepinnt; Dependabot aktualisiert SHA und Versionskommentar.

Gruppen enthalten nur Patch- und Minor-Updates. Major-Updates kommen als
Einzel-PRs.

`dependabot-automerge` meldet einen Dependabot-PR zum Auto-Merge an, wenn das
Update Patch oder Minor ist **und** zu `python-dev-tools`, `npm-dev-tools` oder
`github-actions` gehört (bzw. bei Einzel-PRs eine npm-devDependency oder eine
Action ist). Gemergt wird erst nach grünem `code-quality-gate` und `ci-ok`.
Laufzeitabhängigkeiten und Major-Updates bleiben offen und brauchen eine
Prüfung durch einen Menschen.

Einschränkung: Weil die Auto-Merge-Anmeldung mit dem `GITHUB_TOKEN` erfolgt,
löst der Merge-Commit auf main keine Workflows aus (kein `update-pr-branches`,
keine main-CI). Die nächtliche Vollprüfung deckt das ab.

## Nächtliche Vollprüfung

`nightly.yml` läuft täglich um 01:17 UTC auf main und manuell
(`gh workflow run nightly.yml --repo janpow77/auditcore`):

- `quality.yml` (volle Python-Matrix 3.11–3.13, Plattform-Lebenszyklus mit APT),
- `domain-packages.yml` (alle Fachpakete, pip und APT, optionale Renderer),
- JS-Gesamtlauf (Node 20/22: Lizenzprüfung, Lint, Typecheck, Tests, Build),
- Installation aller Pakete aus dem Paketindex
  `https://janpow77.github.io/auditcore/simple/` (nur `--index-url`), `pip check`
  und Import je Paket unter Python 3.11–3.13.

Schlägt ein Teil fehl, legt der Job `report` das Issue **„Nightly rot“** (Label
`nightly`) an oder kommentiert das offene. Ist die nächste Nacht grün, wird das
Issue mit Link auf den Lauf geschlossen.

## Was weiterhin Menschen oder Claude braucht

- Inhaltliche Fehler: rote Tests, mypy-Fehler, Lint-Regeln ohne sichere
  Autokorrektur, Komplexität und Modulgröße (Refaktorierung).
- Baseline-Anhebungen mit `ausnahme_begruendung`, neue Pakete in der Baseline,
  Werkzeugwechsel (neue ruff- oder mypy-Version in der Baseline).
- PRs mit Label „konflikt“: Konflikt lokal mit `git merge origin/main` lösen.
- Dependabot: Laufzeitabhängigkeiten, Major-Updates, rot gewordene Update-PRs.
- Issue „Nightly rot“: Ursache finden und beheben.
- Releases, Veröffentlichung auf PyPI und im Paketindex, Deploys.
- Fork-PRs: Freigabe der Workflow-Läufe und Review.

## Abschalten

Einzelne Workflows abschalten, ohne Code zu ändern:

```bash
gh workflow disable autofix.yml --repo janpow77/auditcore
gh workflow disable update-pr-branches.yml --repo janpow77/auditcore
gh workflow disable dependabot-automerge.yml --repo janpow77/auditcore
gh workflow disable nightly.yml --repo janpow77/auditcore
gh workflow enable <datei> --repo janpow77/auditcore   # wieder an
```

`ci-ok` nicht abschalten, solange es Required Check ist. Sonst wartet jeder PR
für immer. Vorher die Branch-Protection zurücksetzen:

```bash
gh api -X PATCH repos/janpow77/auditcore/branches/main/protection/required_status_checks \
  -F strict=false -f 'contexts[]=code-quality-gate'
```

Weitere Schalter:

- Auto-Merge im Repository: `gh api -X PATCH repos/janpow77/auditcore -F allow_auto_merge=false`.
- Dependabot-Versions-Updates: `.github/dependabot.yml` entfernen oder
  `open-pull-requests-limit: 0` setzen.
- Autofix-Pushes und Branch-Aktualisierung stoppen, Prüfungen behalten:
  `gh secret delete AUTOMATION_DEPLOY_KEY --repo janpow77/auditcore` und den
  Schlüssel unter `repos/janpow77/auditcore/keys` löschen. Die Workflows liefern
  dann nur noch Patch-Artefakte bzw. Konflikt-Labels.
