# auditcore_dummybundle

## Zweck

Zusammenhängende synthetische Testbündel vom Vorhaben über Mittelabrufe und Belege bis zur Rechnungslegung: centgenaue Summenbindung, Vorlagenprofile, freie Tabelle aus einem Rezept, Auffälligkeiten mit getrennter Lösung.

Für Anwendungen, die Übungs- und Testdaten ausgeben (ECOHESION, Seminare,
Importtests). Ergänzt `auditcore_dummygenerator`, das einzelne Felder und
flache Tabellen erzeugt und unverändert bleibt. Nicht enthalten sind
Dateiexporte (Excel, ZIP), HTTP-Routen, Speicherung, Stichprobenziehung
(`auditcore_sampling`) und alles, was Aufbau oder Kataloge einer bestimmten
Behörde nachbildet, ohne dass es belegt und freigegeben ist.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt);
`auditcore_dummybundle` 0.1.0 erscheint mit dem Release v0.13.0:

```bash
python -m pip install 'auditcore_dummybundle==0.1.0' \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden über die Requirements-Datei des Releases; sie bindet das Paket
und seine auditcore-Abhängigkeiten an die Prüfsummen der signierten
[SHA256SUMS](https://github.com/janpow77/auditcore/releases/download/v0.13.0/SHA256SUMS).
Dieselben Prüfsummen stehen im Index unter
`https://janpow77.github.io/auditcore/simple/auditcore-dummybundle/`:

```bash
python -m pip install -r https://github.com/janpow77/auditcore/releases/download/v0.13.0/requirements-auditcore_dummybundle.txt
```

Wer die Zeilen selbst in eine `requirements.txt` schreibt, nimmt die Prüfsumme
von `auditcore_dummybundle-0.1.0-py3-none-any.whl` aus den signierten
`SHA256SUMS` und bindet die drei Pflichtabhängigkeiten mit; ihre Wheels sind
seit v0.12.0 unverändert:

```text
auditcore_common @ https://github.com/janpow77/auditcore/releases/download/v0.12.0/auditcore_common-0.2.1-py3-none-any.whl#sha256=701d8cab0a17c7a77cae51065af340f1d90c0b37414505d3fd7eac383ec26271
auditcore_dummygenerator @ https://github.com/janpow77/auditcore/releases/download/v0.12.0/auditcore_dummygenerator-0.1.4-py3-none-any.whl#sha256=1aae51ecdeb252d33f3f64eae9ed246e26c412b2a9112f4cd45f6ee6ea9dda0a
auditcore_identifiers @ https://github.com/janpow77/auditcore/releases/download/v0.12.0/auditcore_identifiers-0.2.1-py3-none-any.whl#sha256=ae335c04653b3b3f62692951aee68774cadb68cf37606dd6c39914f2a7e8a67a
```

Debian/Ubuntu über die signierte APT-Quelle des Releases
([Einrichtung](../../docs/deployment/package-feed.md)):

```bash
sudo apt-get install python3-auditcore-dummybundle
```

Extras: keine außer `[dev]` – Test- und Prüfwerkzeuge (pytest, hypothesis,
ruff, mypy).

## Schnellstart

Ein Bündel aus Startwert und Bezugsdatum, die acht Summenproben und die
Belegliste als Vorlage:

```python
from datetime import date
from decimal import Decimal

from auditcore_dummybundle import BundleConfig, build_bundle, generate_templates, run_checks

config = BundleConfig(seed=42, base_date=date(2026, 1, 1), operations=3)
bundle = build_bundle(config)
assert all(check.passed for check in run_checks(bundle))

claim = bundle.table("claims")[0]
receipts = [r for r in bundle.table("receipts") if r["claim_id"] == claim["claim_id"]]
assert sum(r["project_related"] for r in receipts) == claim["requested"]
assert isinstance(claim["requested"], Decimal)

result = generate_templates(config, ["N1", "V5"])
assert result.meta["marking"] == "SYNTHETISCH" and result.meta["seed"] == 42
assert [table.name for table in result.tables] == ["Belegliste", "ZA Kopf", "ZA Ausgaben"]
assert generate_templates(config, ["N1", "V5"]) == result  # gleicher Startwert, gleiche Daten
```

Eine freie Tabelle aus einem Rezept, mit berechneter Spalte und Summenbindung:

```python
from decimal import Decimal

from auditcore_dummybundle import generate_table, parse_recipe

recipe = parse_recipe(
    {
        "format": "auditcore.dummybundle.recipe",
        "format_version": 1,
        "run": {"seed": 7, "base_date": "2026-01-01", "rows": 25, "country": "AT"},
        "fields": [
            {"name": "Nr", "type": "sequence"},
            {"name": "Netto", "type": "amount", "rule": {"kind": "sum_to", "total": "10000.00"}},
            {
                "name": "USt",
                "type": "computed",
                "params": {"operation": "rate", "fields": ["Netto"], "rate": "0.20"},
            },
            {"name": "IBAN", "type": "iban"},
        ],
    }
)
table = generate_table(recipe)
assert sum(row[1] for row in table.rows) == Decimal("10000.00")
assert all(row[3].startswith("AT") for row in table.rows)
```

## API-Überblick

Gliederung: `build_bundle` liefert die kanonischen Tabellen, `run_checks` die
acht Summenproben, `generate_templates` und `generate_recipe` die Ausgabe
(`Result` mit Tabellen, Metadaten und – nur auf Wunsch – der Lösung),
`auditcore_dummybundle.web` den REST-Vertrag `dummybundle_ui/1` ohne
Web-Framework.

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_dummybundle.__all__` (41):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `ANOMALIES` | Konstante | – | `anomalies` |
| `MARKING` | Konstante | Marker carried by every output. | `model` |
| `AnomalyKind` | Datenklasse | One anomaly: code, German title and description, target table, broken checks. | `anomalies` |
| `BudgetExceededError` | Ausnahme | The cooperative time budget of a run is used up. | `errors` |
| `Budget` | Datenklasse | Cooperative time limit; generators call :meth:`tick` in their loops. | `model` |
| `Bundle` | Datenklasse | Canonical tables of one run, keyed by table name. | `bundle` |
| `BundleConfig` | Datenklasse | Everything that determines a bundle; equal configurations give equal bundles. | `config` |
| `BundleError` | Ausnahme | Configuration, recipe or template does not satisfy the generator contract. | `errors` |
| `BundleLimits` | Datenklasse | Upper bounds a host may tighten for a public endpoint. | `config` |
| `CheckOutcome` | Datenklasse | Result of one sum check; ``failures`` name the rows that break it. | `checks` |
| `Column` | Datenklasse | One output column: header as shown, value kind for exporters. | `model` |
| `Options` | Datenklasse | Output choices that do not change the generated values. | `generate` |
| `Recipe` | Datenklasse | A validated free table definition. | `recipe` |
| `RecipeLimits` | Datenklasse | Upper bounds a host may tighten for a public endpoint. | `recipe` |
| `Result` | Datenklasse | Generated tables, run metadata and (only on request) the solution. | `model` |
| `SolutionEntry` | Datenklasse | One planted anomaly; every key of :meth:`as_row` carries the ``gt_`` prefix. | `model` |
| `Table` | Datenklasse | One output table with ordered columns and positional rows. | `model` |
| `Template` | Datenklasse | A versioned template profile. | `templates` |
| `accounting_year` | Funktion | Accounting year (1 July to 30 June) that contains ``base_date``. | `config` |
| `allocate` | Funktion | Split ``total`` proportionally to ``weights``; the parts add up exactly. | `amounts` |
| `anomaly_codes` | Funktion | Codes of all anomalies in catalogue order. | `anomalies` |
| `bic` | Funktion | Fixed, recognisably synthetic BIC: bank part ``SYNT``, test location ``X0``. | `identifiers` |
| `build_bundle` | Funktion | Build the consistent bundle for ``config``; equal configurations give equal bundles. | `bundle` |
| `derive_seed` | Funktion | Stable 64-bit seed for ``seed`` and the domain ``keys``. | `seeds` |
| `document` | Funktion | Whole result as JSON document: ``_meta``, ``tables`` and, if requested, ``solution``. | `export` |
| `generate_recipe` | Funktion | Generate the free table of ``recipe``. | `generate` |
| `generate_table` | Funktion | Generate the table of ``recipe``; equal recipes give equal tables. | `table` |
| `generate_templates` | Funktion | Build one bundle for ``config`` and project it into the chosen templates. | `generate` |
| `get_template` | Funktion | Template ``template_id``; non-public profiles only with ``include_private``. | `templates` |
| `iban` | Funktion | IBAN-shaped text for ``DE`` or ``AT`` with a missed (default) check number. | `identifiers` |
| `parse_config` | Funktion | Strictly read run parameters; ``seed`` and ``base_date`` are mandatory. | `config` |
| `parse_recipe` | Funktion | Strictly read a recipe; raises :class:`BundleError` naming the offending path. | `recipe` |
| `plant_anomalies` | Funktion | Plant the configured anomalies; ``tables`` limits them to tables that are output. | `anomalies` |
| `quantize` | Funktion | Round ``value`` commercially (half up) to a multiple of ``quantum``. | `amounts` |
| `recipe_document` | Funktion | Recipe as a JSON-ready document that :func:`recipe.parse_recipe` reads back unchanged. | `table` |
| `run_checks` | Funktion | Evaluate the eight sum checks on the canonical tables of ``bundle``. | `checks` |
| `share` | Funktion | ``amount`` times ``rate``, rounded commercially to ``quantum``. | `amounts` |
| `split_random` | Funktion | Split ``total`` into ``parts`` scattered amounts of at least ``minimum`` each. | `amounts` |
| `template_recipe` | Funktion | Recipe document that rebuilds the template's list as a free table to adapt. | `templates` |
| `templates` | Funktion | All packaged template profiles by identifier, in catalogue order. | `templates` |
| `vat_id` | Funktion | VAT identifier for ``DE`` or ``AT`` with a missed (default) check digit. | `identifiers` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_dummybundle.accounts` | Accounts of the accounting year (Annex XXIV appendices) and the audit population. |
| `auditcore_dummybundle.amounts` | Decimal amounts: rounding, shares and allocation with remainder balancing. |
| `auditcore_dummybundle.anomalies` | Anomalies for practice, planted after the consistent bundle has been built. |
| `auditcore_dummybundle.applications` | Payment applications to the Commission, aggregated from the paid claims. |
| `auditcore_dummybundle.bundle` | The coherent bundle: operations, claims, receipts, payment applications, accounts. |
| `auditcore_dummybundle.catalogs` | Catalogues: lists of the field generator plus neutral labels of this package. |
| `auditcore_dummybundle.chain` | Operations and their payment claims: the upper half of the bundle chain. |
| `auditcore_dummybundle.checks` | The eight sum checks every bundle without planted anomalies passes to the cent. |
| `auditcore_dummybundle.config` | Run parameters of a bundle: strict reading, defaults and limits. |
| `auditcore_dummybundle.corrections` | Corrections after the declaration to the Commission, and their findings. |
| `auditcore_dummybundle.errors` | Errors of the bundle generator. |
| `auditcore_dummybundle.export` | JSON-ready form of a result: metadata first, exact amounts as text. |
| `auditcore_dummybundle.fieldgen` | Value generators of the free table, one per field type, working column by column. |
| `auditcore_dummybundle.fieldtypes` | Field types of the free table and their parameters, as data. |
| `auditcore_dummybundle.generate` | Entry points: tables for templates of one bundle, or for a free recipe. |
| `auditcore_dummybundle.identifiers` | Synthetic IBAN, BIC and VAT identifiers that fail every check by construction. |
| `auditcore_dummybundle.model` | Value types shared by the bundle, the free table and the exports. |
| `auditcore_dummybundle.parsing` | Strict readers for configuration and recipe values (German error messages). |
| `auditcore_dummybundle.receipts` | Receipts of a payment claim: amounts bound to the claim, dates and evidence. |
| `auditcore_dummybundle.recipe` | The recipe of a free table: strict reading, defaults and dependency order. |
| `auditcore_dummybundle.seeds` | Sub-streams of one seed, derived from domain keys instead of call order. |
| `auditcore_dummybundle.table` | The free table: columns from a recipe, rules between columns, sum binding. |
| `auditcore_dummybundle.templates` | Template profiles: column layouts as data, projected from the canonical bundle. |
| `auditcore_dummybundle.web` | REST contract ``dummybundle_ui/1`` (framework-free): catalogue, generation, recipes. |
<!-- api-overview:end -->

## Profile und Konfiguration

- **Vorlagenprofile** (`template_data/*.json`, Version 0.1.0, Stand
  „Freigegeben“): V0 Vorhabenstamm, V1 Belegliste zum Mittelabruf
  (ausführlich, 37 Spalten), V2 Belegliste der Vorhabenprüfung, V3
  Gesamtbelegliste des Vorhabens, V4 Mittelabruf, V5 Zahlungsantrag (Anhang
  XXIII), V6 Rechnungslegung (Anhang XXIV, Anlagen 1–7), V7 Abzüge und
  Korrekturen, V8 Liste der Vorhaben, V9 Grundgesamtheit und N1 Belegliste
  zum Mittelabruf (kompakt). Alle elf sind öffentlich; ein Profil mit
  `"public": false` erschiene nur mit `Options(include_private=True)`. Jede
  Vorlage nennt Rechtsgrundlage, Quellen und offene Punkte; nicht belegte
  Spalten bleiben leer und sagen im Feld `note`, warum.
- **Freigabe:** Der Rechteinhaber hat die elf Vorlagenprofile am 13.10.2026
  freigegeben. Jedes Profil trägt Inhaltshash und Freigabevermerk; beim Laden
  wird der Hash geprüft. Die Freigabe gilt nicht für die Profile von
  `auditcore_dummygenerator` (dort unverändert `NOT_GRANTED`) und nicht für
  Texte Dritter: Die Tabellenköpfe der Anhänge XXIII und XXIV sind
  Unionsrecht. Einzelheiten: [docs/profile-versioning.md](docs/profile-versioning.md).
- **Laufparameter** (`BundleConfig`): `seed` und `base_date` sind Pflicht;
  dazu Land, Fonds, Zahl der Vorhaben, Mittelabrufe und Belege, Prioritäten,
  Zahlungsanträge, öffentlicher Anteil, Kofinanzierungssatz, Vorsteuerabzug,
  Skonto- und Kürzungsanteil, Korrekturen, Auffälligkeiten mit Anteil und
  `identifiers_valid`. Die Vorgabewerte sind Einstellungen des Generators,
  keine Regeln eines Programms.
- **Rezept** der freien Tabelle (`auditcore.dummybundle.recipe`, Fassung 1):
  Felder mit Typ, Parametern, Anteil leerer Werte und Regel; 21 Feldtypen und
  die Regeln `when` und `sum_to` stehen als Daten in `fieldtypes.py`.
- **Grenzen** für Gastgeber: `BundleLimits`, `RecipeLimits`, `web.Limits`
  (Vorhaben, Zeilen, Felder, Tabellen, Zeitgrenze, Rumpfgröße).
- Keine Umgebungsvariablen, keine Dateien, kein paralleler Weg.

Einzelheiten: [docs/spezifikation.md](docs/spezifikation.md).

## Herkunft und Charakterisierung

Neuimplementierung in auditcore nach dem Vorlagenvorschlag vom 13.10.2026; es
wurde kein Code aus anderen Repositories übernommen. Die Rechenregeln folgen
dem Generator eines Seminars zur Rechnungslegung, dessen Szenario, Fälle und
Lösungen ausdrücklich nicht übernommen sind. Charakterisiert durch die acht
Summenproben als Einzeltests und durch Hypothesis-Eigenschaftstests (jeder
Startwert: Summen gehen auf, Datumsfolgen stimmen, gleiche Eingabe ergibt
gleiche Ausgabe). Die Köpfe der Vorlagen V5 und V6 stammen aus der deutschen
Fassung des Amtsblatts (ABl. L 231 vom 30.6.2021, abgerufen am 13.10.2026).

## Bewusste Verhaltensabweichungen

Keine gegenüber einem Altbestand: Das Paket ersetzt kein vorhandenes Modul.
Gegenüber `auditcore_dummygenerator` gilt bewusst anderes: Beträge sind
`Decimal` statt Gleitkomma, IBAN und USt-IdNr. tragen eine gezielt verfehlte
Prüfziffer, und unbekannte Feldtypen werden abgewiesen statt leer ausgegeben.
Firmennamen zieht das Bündel aus der Liste `companies` des Feldgenerators, so
wie dieser es selbst tut; bei mehr Zeilen als Listeneinträgen wiederholen sie
sich.

## Abhängigkeiten

Python ≥ 3.11 und drei exakt gebundene auditcore-Pakete, sonst nur die
Standardbibliothek: `auditcore_common==0.2.1` (Hashing, REST-Vertragsfehler),
`auditcore_dummygenerator==0.1.4` (Firmenliste sowie Kataloge DE/AT für Orte,
Namen und Verwendungszwecke) und `auditcore_identifiers==0.2.1` (Prüfziffern). Bewusst
keine Abhängigkeit von Faker, NumPy, openpyxl, einem Web-Framework oder einer
Datenbank.

## Sicherheit und Datenschutz

Kein Netzwerkzugriff, keine Dateien, keine Speicherung, keine Geheimnisse.
Eingaben sind Spaltendefinitionen und Laufparameter und werden streng geprüft;
Datendateien nimmt das Paket nicht an. Jede Ausgabe trägt die Kennzeichnung
`SYNTHETISCH`, Startwert, Bezugsdatum und Paketversion in den Metadaten und
auf Wunsch als eigene Spalte.

- **IBAN und USt-IdNr.** sind im Standard garantiert formal ungültig: Die
  richtige Prüfziffer wird mit `auditcore_identifiers` berechnet und gezielt
  verfehlt. „Formal gültig“ gibt es nur auf ausdrückliche Wahl; solche
  Kennungen können zufällig einer vergebenen entsprechen. Zusätzlich beginnt
  die Bankleitzahl mit `0`, und der BIC lautet fest `SYNT<Land>X0` – das sind
  Vorkehrungen, keine belegten Sperrbereiche.
- **Firmen** tragen generische Beispielnamen aus der Liste des
  Feldgenerators. Ähnlichkeiten mit bestehenden Unternehmen sind zufällig und
  nicht beabsichtigt; jede Datei ist als synthetisch gekennzeichnet.
- **Personen** sind im Standard Rollenbezeichnungen („Sachbearbeitung 3“).
  Die Namenskataloge des Feldgenerators enthalten häufige echte Vor- und
  Nachnamen und sind nur auf Wahl im Spiel.
- **Anschriften** verbinden erfundene Straßennamen mit echten,
  zusammengehörigen Postleitzahlen und Städten.
- Die Daten sind Übungsmaterial; sie begründen keine Feststellung und keine
  fachliche oder rechtliche Aussage.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Neuimplementierung ohne übernommenen Fremdcode; Freigabe des
Rechteinhabers für die Bibliotheken in auditcore vom 22.09.2026
(`USER_AUTHORIZED_MIT`). Herkunft, Methodenquellen und Grenzen: `NOTICE` und
`provenance.json`.

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
