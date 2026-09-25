# Helfer-Verträge (`auditcore-helpers`)

Stand: auditcore 0.3.0 · Grundlage: die einmaligen Inventuren
[`app-helfer-ts.md`](../reports/app-helfer-ts.md) und `app-helfer-python.md`.

Die Inventuren haben gezeigt, dass dieselben Hilfsfunktionen in fast jeder App
neu geschrieben werden und dabei immer wieder dieselben Fehler entstehen:
`BeleglisteGrid.parseDecimal` macht aus „1.234,56“ den Wert 1,234,
Datumsformatierer zeigen westlich von UTC den Vortag, CSV-Exporte haben keinen
Formelschutz, 422-Fehler erscheinen als „[object Object]“. `auditcore-helpers`
macht aus der einmaligen Inventur eine dauerhafte Prüfung. Sie ist so verankert
wie der Pflicht-Rauchtest (`auditcore-deploy smoke`, Action `functional-smoke`)
und das Code-Gate (Ratchet gegen eine Baseline).

## Bausteine

| Baustein | Ort | Aufgabe |
|---|---|---|
| Vertragsfälle | [`contracts/common-cases/*.json`](../../contracts/common-cases) | Versionierte Ein-/Ausgabe-Fälle, gleich für TypeScript und Python (JSON-Schema `schema.json`) |
| Festlegungen | [`contracts/common-cases/DECISIONS.md`](../../contracts/common-cases/DECISIONS.md), `decisions.json` | Ersatzwert, Zeitzone, Dateigrößen, Mehrdeutigkeit – **vorläufig**, zentral änderbar |
| Scan | `auditcore-helpers scan` | Hilfsfunktionen (Python-AST, TypeScript-Compiler-API inkl. Vue-SFC-Skriptblöcken), Duplikatgruppen, Abgleich mit dem Katalog der auditcore-Bibliotheken |
| Lint | `auditcore-helpers lint` | Deklarative Fehlmuster-Regeln (`src/auditcore/tools/helpers/data/rules.json`), zwei davon führen erkannte Helfer tatsächlich aus |
| Verträge | `auditcore-helpers contracts` | Führt die Vertragsfälle gegen die Funktionen aus, die die App im Manifest `.auditcore/helpers.json` nennt |
| Ratchet | `auditcore-helpers check` | Alle drei Schritte, Vergleich mit `.auditcore/helpers-baseline.json` |
| Action | [`.github/actions/helper-contracts`](../../.github/actions/helper-contracts/action.yml) | Einbindung in die App-Workflows (per SHA) |
| Nachtlauf | [`scripts/helpers_nightly.sh`](../../scripts/helpers_nightly.sh) + `scripts/systemd/` | Lauf über alle App-Repositorys unter `~/Projekte` auf der NUC |

### Vertragsfälle (Status vorläufig; `parse-number` 1.1.0, übrige 1.0.0)

| Vertrag | Fälle | Inhalt |
|---|---:|---|
| `parse-number` | 84 | Modi `de`, `en`, `auto`; Tausenderpunkt, Dezimalkomma, „1.5“ und „1.234“ in `de` ungültig (mehrdeutig), höchstens zwei Nachkommastellen, nur Trennzeichen = leer, negativ (auch U+2212), €/EUR, Leerraum und U+00A0; enthält alle Fälle aus flowinvoice `german-amount-cases.json` |
| `format-money` | 10 | „1.234,50 €“ mit U+00A0, kaufmännische Rundung, String-Eingabe, Ersatzwert |
| `format-date` | 9 | TT.MM.JJJJ in Europe/Berlin, reine Datumswerte ohne Verschiebung, Date-Objekte, ungültig |
| `format-datetime` | 7 | „15.07.2026, 12:05“, Sommer-/Winterzeit, Zeitumstellung |
| `format-filesize` | 13 | Basis 1024, KB/MB/GB/TB, Dezimalkomma |
| `iban-valid` | 9 | Länderlänge und Prüfziffer mod 97 |
| `lei-valid` | 7 | ISO 17442, Prüfziffer mod 97 |
| `csv-cell` | 13 | Trenner „;“, Quoting, Formelschutz „'“ vor `= + - @` Tab CR |
| `csv-document` | 3 | UTF-8-BOM, CRLF, Formelschutz |
| `api-error-message` | 6 | FastAPI `detail` als String und 422-Liste, `{error: {code, message}}`, Error, String, Ersatztext |
| `empty-value` | 4 | Ersatzwert „—“ für null/undefined/""/NaN |

Beide Sprachen haben eine Referenzumsetzung, die alle Fälle besteht
(`tests/fixtures/helpers/reference`); damit ist belegt, dass die Fälle
widerspruchsfrei sind. Beim Ausführen setzt der Läufer die Prozess-Zeitzone auf
`America/New_York` (`probe_timezone`), damit fehlendes `timeZone` und
`new Date('JJJJ-MM-TT')` auffallen.

### Regeln

| ID | Art | Sprachen | Erkennt |
|---|---|---|---|
| HC-NUM-01 | Funktion | TS, Python | Zahlparser ersetzt nur das Komma (Muster `BeleglisteGrid.parseDecimal`) |
| HC-NUM-02 | Funktion | TS, Python | Zahlparser entfernt jeden Punkt, „1.5“ wird 15 |
| HC-NUM-10 | Ausführung | TS, Python | Erkannte Zahlparser werden isoliert mit den `probe`-Fällen von `parse-number` ausgeführt; Abweichungen werden gemeldet (z. B. „1.234,56 → 1.234“, „abc → 0“) |
| HC-DATE-01 | Aufruf | TS | `toLocaleDateString`/`toLocaleTimeString`/`Intl.DateTimeFormat`/datumsbezogenes `toLocaleString` ohne `timeZone` (auch in Vue-Templates) |
| HC-DATE-02 | Muster | TS | `new Date('JJJJ-MM-TT')`, `new Date(x.split('T')[0])` |
| HC-DATE-10 | Ausführung | TS | Erkannte Datumsformatierer werden in Europe/Berlin und America/New_York ausgeführt; unterschiedliche Ergebnisse = Zeitzonenfehler, unabhängig vom Ausgabeformat |
| HC-MONEY-01 | Muster | TS, Python | Handgebaute €-Formatierung (`toFixed(2) + ' €'`, `f"{x:.2f} €"`, Platzhalter-Tausch) |
| HC-CSV-01 | Datei | TS, Python | CSV-Export ohne Formelschutz |
| HC-CSV-02 | Datei | TS | CSV-Download ohne BOM |
| HC-ERR-01 | Funktion | TS | Fehlertext-Funktion liest `detail`, wertet die 422-Liste nicht aus |
| HC-ERR-02 | Muster | TS | `detail` direkt als Meldung (`detail || '…'`, `toast.error(….detail)`) |

Ausgeführt wird nur, was ohne die App lauffähig ist: Standardbibliothek,
literale Modulkonstanten und die Modulfunktionen, die der Helfer selbst
aufruft. Alles andere zählt als „nicht isoliert ausführbar“ und wird nicht
gemeldet. Fehlermeldungen werden auf eine Zeile gekürzt; von
Validierungsfehlern mitgelieferte Eingabewerte (`input_value=…`, etwa
Geheimnisse aus einer `.env`) werden durch `***` ersetzt.

Eine einzelne Fundstelle lässt sich begründet unterdrücken, in derselben oder
der Zeile davor:

```ts
// auditcore-helpers: ignore HC-ERR-02 Backend liefert hier nur Text
```

Ganze Regeln schaltet nur das Manifest ab, immer mit Begründung.

### Katalog der Bibliotheken

`src/auditcore/tools/helpers/data/catalog.json` ordnet Namensmuster den
auditcore-Bibliotheken zu (z. B. `formatDate` → `@flowaudit/ui formatDate`,
`sha256_file` → `auditcore_common.hashing.sha256_file`). Zusätzlich vergleicht
der Scan die normalisierten Funktionsrümpfe mit allen Funktionen der
Python-Pakete und `@flowaudit/*`-Pakete des auditcore-Checkouts
(`--library-root`); ein Treffer heißt „wortgleiche Kopie“. Nur Ziele mit Status
`vorhanden` zählen im Ratchet („existiert schon in Bibliothek X“); `geplant`
(z. B. `@flowaudit/common parse/number`) erscheint als Hinweis.

## Befehle

```bash
auditcore-helpers toolchain                   # Node-Werkzeugkette (typescript, tsx) einmalig in ~/.cache/auditcore
auditcore-helpers scan  <repo>                # Hilfsfunktionen, Duplikate, Bibliotheksabgleich
auditcore-helpers lint  <repo> [--strict]     # Fehlmuster
auditcore-helpers contracts <repo> [--strict] # Vertragsfälle laut Manifest
auditcore-helpers check <repo> [--init-baseline | --update-baseline] [--compare-ref origin/main] [--no-fail]
auditcore-helpers rules                       # Regelkatalog
```

Gemeinsame Optionen: `--manifest`, `--cases <auditcore>/contracts/common-cases`,
`--library-root <auditcore>`, `--no-node` (nur Python), `--output bericht.json`,
`--markdown bericht.md`, `--summary "$GITHUB_STEP_SUMMARY"`,
`--format text|json|markdown`. Exitcodes von `check`: 0 = PASS/WARN,
1 = FAIL, 2 = nicht ausführbar.

Die Node-Werkzeugkette kommt aus dem mitgelieferten Lockfile
(`src/auditcore/tools/helpers/node/package-lock.json`); das App-Repository
braucht dafür nichts. Für TS-Verträge müssen nur die `node_modules` der App
installiert sein, falls der Helfer Pakete importiert.

## Manifest `.auditcore/helpers.json`

Beispiel für regulierung: [`examples/helpers.regulierung.example.json`](examples/helpers.regulierung.example.json).

| Feld | Bedeutung |
|---|---|
| `schema_version` | `1` |
| `app` | Name im Bericht |
| `python` | Interpreter für Python-Verträge (z. B. `backend/.venv/bin/python`), sonst der des Werkzeugs |
| `scan.exclude` | Glob-Muster, die Scan und Lint auslassen (Skripte, generierter Code) |
| `lint.disable` | `{"HC-…": "Begründung"}` |
| `bindings[]` | je Bindung: `contract`, `language` (`ts`/`python`), `module` (TS: Dateipfad; Python: Modulname oder `.py`-Pfad), `export` (auch `Klasse.methode`), optional `id`, `args`, `select`, `tags`, `exclude_tags`, `skip` (`{"fall-id": "Begründung"}`), `result_path`, `python_path`, `python`, `cwd` |

`args` bildet die Falleingabe auf die Parameter der App-Funktion ab: ein Name
(`"text"`), ein Pfad (`{"path": "error.response.data"}` für fetch-basierte
Helfer), ein fester Wert (`{"literal": "—"}`) oder ein Optionsobjekt
(`{"object": {"mode": "mode"}}`). Ohne `args` werden die Parameter des
Vertrags in ihrer Reihenfolge übergeben. `select` wählt Fälle nach
Eingabefeldern (z. B. `{"mode": "de"}`). Python-Verträge laufen in einem
eigenen Prozess (`python -I -B`, Arbeitsverzeichnis = erster `python_path`).

## Ratchet `.auditcore/helpers-baseline.json`

Jeder Befund hat einen zeilenunabhängigen Schlüssel:
`library|<datei>|<funktion>|<bibliothek>`, `lint|<regel>|<datei>|<fingerabdruck>`,
`contract|<bindung>|<fall>`. Wie beim Code-Gate gilt:

- mehr als in der Baseline → **FAIL** (neues Duplikat einer Bibliotheksfunktion, neues Fehlmuster, neue Vertragsverletzung);
- weniger als in der Baseline → **FAIL**, bis `--update-baseline` im selben PR absenkt;
- ohne Baseline ist der Maßstab 0; `--init-baseline` legt sie einmalig an;
- eine Anhebung gegenüber `--compare-ref` braucht `ausnahme_begruendung[<schlüssel>]`, sonst FAIL.

## Einbindung in eine App (Schritt für Schritt)

Die Einbindung erfolgt mit der jeweiligen App-Migration, nicht zentral.

1. **Lokal messen:** im App-Repository
   `auditcore-helpers check . --no-fail --cases ~/Projekte/auditcore/contracts/common-cases --library-root ~/Projekte/auditcore --markdown /tmp/helpers.md`
   und den Bericht lesen.
2. **Manifest anlegen:** `.auditcore/helpers.json` nach dem Beispiel; zentrale
   Helfer (Zahl, Datum, Betrag, Fehlertext, CSV) an die Verträge binden,
   Wegwerfskripte über `scan.exclude` ausnehmen. Steht `.auditcore/` in der
   `.gitignore`, die Ausnahmen `!.auditcore/helpers.json` und
   `!.auditcore/helpers-baseline.json` ergänzen.
3. **Baseline anlegen:** `auditcore-helpers check . --init-baseline …` und
   `.auditcore/helpers-baseline.json` committen. Der heutige Stand ist damit
   eingefroren, jede neue Abweichung wird rot.
4. **Workflow-Job ergänzen** (Action per Commit-SHA einbinden):

   ```yaml
   helper-contracts:
     runs-on: ubuntu-latest
     steps:
       - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
         with:
           fetch-depth: 0
       - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
         with:
           python-version: '3.12'
       - uses: actions/setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af
         with:
           node-version: '20'
       - run: npm ci
         working-directory: frontend
       - uses: janpow77/auditcore/.github/actions/helper-contracts@<commit-sha>
         with:
           compare-ref: ${{ github.event_name == 'pull_request' && format('origin/{0}', github.base_ref) || '' }}
   ```

   Für Python-Verträge, die App-Abhängigkeiten importieren, vorher die
   Backend-Abhängigkeiten installieren und im Manifest `python` setzen.
5. **Beheben statt anheben:** Wer einen Befund behebt, senkt die Baseline im
   selben PR (`--update-baseline`). Neue Befunde werden behoben oder begründet
   unterdrückt; eine Anhebung der Baseline braucht `ausnahme_begruendung`.
6. **Umstellung auf die Bibliothek:** Sobald `@flowaudit/common` bzw. die
   Erweiterungen von `auditcore_common` bereitstehen, die lokalen Helfer
   ersetzen und die Bindungen auf die Bibliotheksfunktion (oder ihren
   Wrapper) umstellen; die Baseline sinkt dabei.

## Nächtlicher Lauf auf der NUC

`scripts/helpers_nightly.sh` exportiert den auditcore-Stand aus `origin/main`
(der Checkout bleibt unberührt), installiert ihn in
`~/.local/state/auditcore/helpers-nightly/venv` und prüft jedes Git-Repository
unter `~/Projekte` (ohne auditcore und `*-wt`) mit `check --no-fail`. Die App-
Repositorys werden nur gelesen. Berichte: `~/.local/state/auditcore/helpers-nightly/<datum>/`
mit `INDEX.md` (Übersicht) sowie je Repository JSON, Markdown und Log;
`latest` zeigt auf den letzten Lauf.

Einschalten (installiert Skript und systemd-User-Timer, täglich 02:30):

```bash
git -C ~/Projekte/auditcore fetch origin && git -C ~/Projekte/auditcore show origin/main:scripts/helpers_nightly.sh | bash -s -- --enable
```

Ausschalten: `systemctl --user disable --now auditcore-helpers-nightly.timer`.
Einzellauf: `bash ~/.local/share/auditcore/helpers_nightly.sh`; Auswahl über
`HELPERS_REPOS="flowinvoice regulierung"`.

## Erweitern

- **Neue Regel:** Eintrag in `data/rules.json` mit ID, Art, Meldung, Abhilfe,
  `spec` je Sprache und mindestens einem Positiv- und einem Negativbeispiel.
  `tests/test_helpers_rules.py` prüft jedes Beispiel automatisch.
- **Neuer Vertrag oder Fall:** Datei in `contracts/common-cases/` (Schema
  `schema.json`), Version anheben, Referenzumsetzung in
  `tests/fixtures/helpers/reference` ergänzen; `tests/test_helpers_contracts.py`
  verlangt, dass beide Sprachen alle Fälle bestehen.
- **Festlegung ändern:** nur `decisions.json` und `DECISIONS.md`; Falldateien
  verweisen mit `{"$decision": …}` darauf. Mit der Nutzerentscheidung wechselt
  der Status von „vorläufig“ auf „verbindlich“.
- **Katalog:** neue Bibliotheksfunktionen in `data/catalog.json` mit Status
  `vorhanden` eintragen, sobald sie in `main` sind.

## Grenzen

- Namens- und Textmuster finden nicht jede Variante; die Verträge prüfen nur
  gebundene Funktionen, die Ausführungsregeln nur isoliert lauffähige Helfer.
- `HC-DATE-01`/`HC-ERR-02` sind Textregeln und können im Einzelfall anschlagen,
  obwohl die Stelle korrekt ist; dafür gibt es die begründete Unterdrückung.
- Vue-SFCs werden als Skriptblöcke analysiert; Vertragsbindungen auf `.vue`-
  Dateien sind nicht möglich (Helfer gehören in `.ts`-Module bzw. Composables).
- Zeitstempel ohne Zonenangabe sind bewusst nicht Teil der Verträge (siehe
  `DECISIONS.md`).
