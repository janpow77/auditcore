# Code-Qualitätsmaßstäbe und Ratchet-Gate

Die Maßstäbe unten sind verbindlich und werden per Code erzwungen, nicht nur
beschrieben: `auditcore-codegate check` (Quelltext:
`src/auditcore/tools/quality/codegate*.py`) misst jedes Paket und vergleicht es
mit `quality/baseline.json`. Weil der Altbestand die Maßstäbe noch nicht erfüllt,
gilt ein **Ratchet**: Kein Wert darf steigen, jede Verbesserung wird sofort
festgeschrieben, neue Pakete müssen die Maßstäbe vollständig erfüllen.

## Maßstäbe

### Python (`src/auditcore`, `packages/auditcore_*/src`)

| Maßstab | Metrik im Gate |
|---|---|
| McCabe-Komplexität ≤ 10 je Funktion (ruff C901) | `complexity_over_10` |
| Module ≤ 400 Zeilen | `modules_over_400_lines` |
| Funktionen ≤ 60 Zeilen | `functions_over_60_lines` |
| `Any` nur sparsam | `any_usages` (jede Verwendung von `Any`/`typing.Any`) |
| `mypy --strict` je Paket fehlerfrei | `mypy_strict_errors` |
| Bezeichner (def/class) Englisch; Deutsch nur in Strings, Daten und festen fachlichen Schlüsseln | `non_english_identifiers` (Heuristik: Umlaute oder deutsche Wortstämme, auch in Umlaut-Ersatzschreibung) |
| Keine paketübergreifend kopierten Funktionen; gemeinsame Hilfen gehören nach `auditcore_common` | `duplicate_functions` (siehe unten) |

#### `duplicate_functions` – paketübergreifende Duplikate

Jeder Funktionsrumpf wird auf AST-Ebene normalisiert (`codegate_duplicates.py`):
Docstring, Dekoratoren, Annotationen und Name entfallen, lokal gebundene
Bezeichner werden der Reihe nach zu `v0, v1, …`, Text- und Byte-Konstanten
werden zu einem Platzhalter (Meldungen und Ressourcennamen unterscheiden sich
auch zwischen sonst gleichen Kopien). Freie Namen, Attribute und Zahlen
bleiben. Gezählt wird eine Funktion ihres Pakets, wenn eine Funktion mit
derselben Normalform in einem anderen Paket existiert und der Rumpf
**mindestens 2 Anweisungen und 25 AST-Knoten** hat. Die Schwelle ist bewusst
niedriger als „5 Anweisungen“: der Profil-Fingerprint (zwei Anweisungen, neun
Kopien) fiele sonst heraus; Ein-Ausdruck-Methoden wie `reference` zählen
nicht. `auditcore_common` ist der kanonische Ort: seine Funktionen zählen nie,
eine Paketkopie davon schon. Jede Fundstelle nennt im Bericht die Gegenstücke.
Ausgangswert bei Einführung (main nach `auditcore_common` 0.1.0, 25.09.2026):
**33** in 12 Paketen; die fachliche Inventur steht in [duplikate.md](duplikate.md).

Eine nach Paketaufnahme eingeführte Metrik wird mit `--update-baseline` mit
ihrem Erstwert erfasst; die Anhebungsprüfung meldet das als WARN
„Einführung der Metrik“, danach gilt die Ratsche.

#### `warnings` nur für Deprecation-Aliase

Die Architekturtests der Pakete (`packages/auditcore_*/tests/test_architecture.py`)
lassen das Standardmodul `warnings` zu (Entscheidung vom 25.09.2026) –
**ausschließlich**, damit ein umbenannter öffentlicher Name einen Alias mit
`DeprecationWarning` behalten kann (Muster: modulweites `__getattr__`, das die
neue Funktion liefert und `warnings.warn(..., DeprecationWarning, stacklevel=2)`
aufruft; Beispiel `auditcore_funding_sources.designer`). Erlaubt ist nur
`import warnings` mit `warnings.warn(…, DeprecationWarning …)`; Filter,
`catch_warnings`, andere Kategorien und `from warnings import …` sind verboten.
`tests/test_warnings_usage.py` prüft das für `src/auditcore` und alle
`packages/auditcore_*/src` zugleich.

Messdetails, damit die Zahlen reproduzierbar sind:

- C901 läuft mit `ruff check --isolated --ignore-noqa`: Projektkonfiguration und
  `# noqa: C901` wirken nicht. Ein `noqa` senkt die Zahl also nicht.
- mypy läuft je Paket mit `--strict --config-file "" --no-site-packages
  --ignore-missing-imports --python-version 3.11`; die Quellen aller Pakete
  liegen im `MYPYPATH`. Das Ergebnis hängt damit nicht davon ab, welche
  Drittpakete lokal installiert sind. Die mypy-Version steht in der Baseline;
  weicht sie ab, meldet das Gate mypy-Abweichungen nur als `WARN`, bis die
  Baseline erneuert ist.
- Tests (`tests/`) werden nicht gemessen.

### TypeScript/Vue (`packages-js/*`, sobald vorhanden)

Verbindliche Einstellungen der gemeinsamen Konfiguration (ESLint flat config und
`tsconfig.base.json`):

```js
// eslint.config.js (Auszug, verbindlich)
rules: {
  '@typescript-eslint/no-explicit-any': 'error',
  complexity: ['error', 12],
  'max-lines': ['error', { max: 400, skipBlankLines: false, skipComments: false }],
  '@eslint-community/eslint-comments/no-unlimited-disable': 'error',
  '@eslint-community/eslint-comments/require-description': 'error',
},
// Vue-SFC: 'max-lines': ['error', { max: 250 }] für files: ['**/*.vue']
```

```jsonc
// tsconfig.base.json (Auszug, verbindlich)
{ "compilerOptions": { "strict": true, "noUncheckedIndexedAccess": true } }
```

Ausnahmen nur zeilenweise mit Begründung:
`// eslint-disable-next-line @typescript-eslint/no-explicit-any -- <Grund>`.
Dateiweite `/* eslint-disable */` sind unzulässig.

Das Python-Gate misst davon unabhängig von ESLint:

| Maßstab | Metrik im Gate |
|---|---|
| Skript-/TS-Dateien ≤ 400 Zeilen (ohne `*.d.ts`, `node_modules`, `dist`) | `files_over_400_lines` |
| Vue-SFC ≤ 250 Zeilen | `vue_sfc_over_250_lines` |
| keine dateiweiten `eslint-disable` | `eslint_file_disables` |
| zeilenweise Disables nur mit `-- Grund` | `eslint_unjustified_line_disables` |
| `any` nur mit begründeter Zeilenausnahme | `explicit_any` |

JS-Pakete erscheinen in der Baseline als `js:<name>`.

## Regeln des Gates

| Situation | Ergebnis |
|---|---|
| Metrik eines Pakets steigt | **FAIL** |
| Metrik sinkt, Baseline nicht abgesenkt | **FAIL** – Baseline im selben PR absenken |
| neues Paket (nicht in der Baseline) mit Verstoß | **FAIL** – Baseline 0 für alle Metriken |
| Paket gelöscht, Eintrag noch in der Baseline | **FAIL** – `--update-baseline` entfernt ihn |
| Baseline-Wert höher als auf dem Zielzweig, ohne `ausnahme_begruendung` | **FAIL** |
| Baseline-Wert höher, mit `ausnahme_begruendung` | **WARN**, sichtbar als „ANHEBUNG“ im Bericht |

Exit-Codes: `0` bestanden (auch mit WARN), `1` rot, `2` nicht ausführbar
(z. B. ruff/mypy fehlt). Ein nicht ausführbares Gate ist nie grün.

## Kommandos für Entwickler

```bash
pip install -e '.[dev]'                         # bringt ruff und mypy mit
auditcore-codegate check                        # vollständiger Lauf wie in CI
python scripts/verify_code_quality.py           # dasselbe ohne Installation
python scripts/verify_code_quality.py --skip-mypy          # Schnelllauf (pre-commit)
auditcore-codegate check --package auditcore_risk          # nur ein Paket
auditcore-codegate check --format json --output gate.json  # maschinenlesbar
auditcore-codegate check --compare-ref origin/main         # inkl. Anhebungsprüfung
```

Der JSON-Bericht enthält je Paket die Metriken und jede einzelne Fundstelle
(`findings`: Metrik, Datei, Zeile, Detail).

## Anleitung: Baseline nach einem Refactoring absenken

Für jeden Refactoring-PR (z. B. aus `worktrees/refactor-<paket>`):

1. Paket refaktorieren, Tests grün.
2. `auditcore-codegate check --package auditcore_<paket>` zeigt die gesunkenen
   Werte als FAIL „gesunken … Baseline absenken“.
3. `auditcore-codegate check --package auditcore_<paket> --update-baseline`
   senkt genau die Werte dieses Pakets ab. Das Kommando senkt nur ab, es hebt
   nie an.
4. `quality/baseline.json` im **selben** PR committen
   (`refactor(<paket>): … ` plus Baseline-Diff).
5. Kollidiert die Baseline beim Rebase mit einem anderen Refactoring-PR: die
   Datei vom Zielzweig übernehmen und Schritt 3 wiederholen – die Werte werden
   neu gemessen, nicht von Hand zusammengeführt.

`--update-baseline` ohne `--package` behandelt alle Pakete und entfernt
Einträge gelöschter Pakete.

## Anhebung (nur ausnahmsweise)

Eine Anhebung wird von Hand in `quality/baseline.json` eingetragen, immer mit
Begründung je Metrik:

```json
"auditcore_risk": {
  "metrics": {"complexity_over_10": 12, "...": 0},
  "ausnahme_begruendung": {"complexity_over_10": "Warum, bis wann, Ticket"}
}
```

Die CI vergleicht die Baseline mit dem Zielzweig (`--compare-ref`) und listet
jede Anhebung im Job-Summary. Ohne Begründung ist der Job rot. Ein Wechsel der
mypy-Version kann Werte heben; `--update-baseline` trägt dafür automatisch die
Begründung „Werkzeugwechsel mypy X -> Y“ ein, damit auch das sichtbar bleibt.

## Wo das Gate verankert ist

- **CI:** `.github/workflows/code-quality-gate.yml`, Job `code-quality-gate`
  (ohne Pfadfilter, als Required Check vorgesehen), mit Anhebungsprüfung gegen
  den Zielzweig und Bericht im Job-Summary.
- **Release-Blocker:** `scripts/verify_domain_packages.py` führt das Gate für die
  zu bauenden Pakete vor dem ersten Build als Check `code-quality-gate` aus und
  bricht bei Rot ab; `scripts/prepare_library_release.py` verlangt diesen Check als
  ausgeführtes PASS in den Nachweisen (`REQUIRED_CHECKS`).
- **pre-commit:** Hook `code-quality-gate` in `.pre-commit-config.yaml`
  (Schnelllauf ohne mypy).
- **CLI:** `auditcore-codegate check` (Eintrag in `pyproject.toml`).
- **Bauauftrag:** `docs/prompts/CLAUDE_LIBRARY_BUILD.md`, Abschnitt 4.
- **Tests des Gates:** `tests/test_codegate.py` (synthetische Mini-Pakete).

`ruff` C901 ist bewusst **nicht** global in `pyproject.toml` aktiviert: Das
würde `main` sofort rot machen. Die Begrenzung regelt allein der Ratchet.
