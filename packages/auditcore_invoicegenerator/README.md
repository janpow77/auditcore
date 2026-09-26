# auditcore_invoicegenerator

## Zweck

Synthetische Testrechnungen mit vollständigen Parteien, Positionen, Beträgen und Datumsfeldern, expliziten Fehlerfällen und einem charakterisierten historischen Flowinvoice-Profil; JSON-Ausgabe, PDF optional.

Für Tests und Trainingsdaten von Anwendungen, die Rechnungen prüfen oder
auslesen (etwa `auditcore_invoicesynth`, Flowinvoice). Alle Rechnungen sind
synthetisch: kein System zur verbindlichen Rechnungsstellung, keine
steuerrechtliche Auskunft. Scan, UBL und XRechnung sind nicht implementiert.

## Installation

Aus dem Paketindex von auditcore (PEP 503, jede Datei mit SHA-256 verlinkt):

```bash
python -m pip install auditcore_invoicegenerator \
  --index-url https://janpow77.github.io/auditcore/simple/
```

Hashgebunden in einer `requirements.txt` (zuletzt veröffentlicht: 0.2.2 im
Release v0.4.1; weitere Versionen und Hashes unter
`https://janpow77.github.io/auditcore/simple/auditcore-invoicegenerator/`):

```text
auditcore_invoicegenerator @ https://github.com/janpow77/auditcore/releases/download/v0.4.1/auditcore_invoicegenerator-0.2.2-py3-none-any.whl#sha256=540994598e88ff77e01966823264e196b71a2fe34800a2010af45befdf1715f9
```

Die Abhängigkeit `auditcore_dummygenerator` braucht in einer hashgebundenen
Datei eine eigene Zeile. Debian/Ubuntu über die signierte APT-Quelle eines
Releases ([Einrichtung](../../docs/deployment/package-feed.md)); APT
installiert `python3-auditcore-dummygenerator` mit:

```bash
sudo apt-get install python3-auditcore-invoicegenerator
```

Extras: `[pdf]` – PDF-Renderer über ReportLab (`reportlab>=4.5.1,<6`);
`[dev]` – Test- und Prüfwerkzeuge.

## Schnellstart

```python
import json
from datetime import date

from auditcore_invoicegenerator import InvoiceScenario, duplicate_invoice, to_json

scenario = InvoiceScenario(42, base_date=date(2026, 1, 15), country="DE")
invoices = scenario.generate_batch(3, errors={2: "wrong_total", 3: "missing_vat_id"})
invoices.append(duplicate_invoice(invoices[0], new_id="DOC-DUPLICATE"))

assert [i["metadata"]["injected_errors"] for i in invoices] == [
    [], ["wrong_total"], ["missing_vat_id"], ["duplicate"]
]
assert len(json.loads(to_json(invoices))) == 4
```

```pycon
>>> invoices[1]["amounts"]["total"], invoices[1]["metadata"]["correct_values"]["amounts.total"]
(22702.77, 22701.77)
```

Historisches Profil (Legacy-Ziehfolge nur mit derselben Instanz):

```python
from auditcore_invoicegenerator import FlowInvoiceDemoProfile, suppliers

profile = FlowInvoiceDemoProfile(seed=42)
legacy = profile.generate_invoice(1, suppliers()[0])
assert "line_items" in legacy
```

## API-Überblick

<!-- api-overview:start (generiert: python scripts/docs/api_overview.py --write) -->
Öffentliche Namen aus `auditcore_invoicegenerator.__all__` (19):

| Name | Art | Kurzbeschreibung (erste Docstring-Zeile) | Modul |
|---|---|---|---|
| `Amounts` | TypedDict | Displayed numeric totals; tax rates are training profile values. | `models` |
| `InvoiceRecord` | TypedDict | Complete legacy-compatible record, with scenario metadata when explicitly requested. | `models` |
| `LineItem` | TypedDict | A displayed synthetic invoice position using the selected profile's rounding. | `models` |
| `Party` | TypedDict | Synthetic organization details; identifiers are not official registrations. | `models` |
| `PDFDependencyError` | Ausnahme | The explicitly selected PDF extra is not installed. | `pdf` |
| `render_pdf` | Funktion | Render one synthetic invoice as deterministic PDF bytes with automatic pagination. | `pdf` |
| `FLOWINVOICE_DEMO_PROFILE` | Konstante | – | `profiles` |
| `PROBLEM_TYPES` | Konstante | – | `profiles` |
| `FlowInvoiceDemoProfile` | Klasse | Stateful local RNG with the exact characterized single-invoice legacy draw order. | `profiles` |
| `InvoiceScenario` | Klasse | Generate synthetic parties and complete invoices with explicit expected defects. | `scenarios` |
| `ScenarioError` | Typalias | – | `scenarios` |
| `generate_invoice` | Funktion | Generate one repeatable legacy-profile invoice using a fresh independent RNG. | `profiles` |
| `generate_invoice_legacy_global` | Funktion | Compatibility adapter for the original demo's explicit process-global RNG contract. | `profiles` |
| `get_currency` | Funktion | Return the historical demonstration currency assignment. | `profiles` |
| `get_vat_rate` | Funktion | Return the historical demonstration rate; this is not current tax advice. | `profiles` |
| `problem_suppliers` | Funktion | Return synthetic training labels; these do not assert real sanctions or wrongdoing. | `profiles` |
| `suppliers` | Funktion | Return independent copies of the historical synthetic supplier catalog. | `profiles` |
| `duplicate_invoice` | Funktion | Copy the same invoice identity into an independent record for duplicate-detection tests. | `scenarios` |
| `to_json` | Funktion | Render valid UTF-8-ready JSON data without files, PDF dependencies or input mutation. | `scenarios` |

Öffentliche Module:

| Modul | Kurzbeschreibung |
|---|---|
| `auditcore_invoicegenerator.models` | Public JSON-compatible records for synthetic invoice scenarios. |
| `auditcore_invoicegenerator.pdf` | Optional deterministic, plain-text PDF rendering for synthetic invoice records. |
| `auditcore_invoicegenerator.profiles` | Named Flowinvoice demo profile retaining observed RNG order and float rounding. |
| `auditcore_invoicegenerator.scenarios` | New explicit scenario contract using the independently installed dummy-data library. |
<!-- api-overview:end -->

## Profile und Konfiguration

Zwei getrennte, versionierte Profile (IDs, Versionen, Inhaltshashes in der
mitinstallierten `provenance.json`, fachlicher Status `DRAFT`):

- `invoice-scenario-v1` (`InvoiceScenario`, Laufzeitkennung
  `synthetic-scenario-v1`): Länder DE und AT; Parteien- und Rechnungszufall
  getrennt, gleicher Seed und Bezugsdatum liefern auf frischen Instanzen
  gleiche Ergebnisse. Fehlerfälle `wrong_total`, `missing_vat_id`,
  `date_before_reference` und explizite Duplikate; `metadata.injected_errors`
  benennt die Abweichung, `metadata.correct_values` die Vergleichswerte. Ein
  Aufruf verändert weder globalen Zufallszustand noch übergebene Fehlerpläne.
- `flowinvoice-demo-fb2d185` (`FlowInvoiceDemoProfile`,
  `FLOWINVOICE_DEMO_PROFILE`): feste Datumsbereiche, Empfänger,
  Positionskataloge, Länder-/Währungstabellen der Flowinvoice-Demoquelle.
  `generate_invoice(..., seed=42)` erzeugt je Aufruf eine frische Instanz.
  `generate_line_items` schöpft den Zielbetrag ausdrücklich nicht exakt aus.

Regeln für Profiländerungen: [docs/versioning.md](docs/versioning.md).

### PDF-Renderer (Extra `pdf`)

```python no-run
from pathlib import Path
from auditcore_invoicegenerator import render_pdf

Path("synthetic-invoice.pdf").write_bytes(render_pdf(invoices[0]))
```

`render_pdf` liefert Bytes und verändert keine Eingaben: Parteien, Datumsfelder,
alle Positionen, Steuer und Summen mit Seitenumbruch; beabsichtigte
Rechenfehler werden nicht korrigiert, Lösungshinweise aus `metadata` nicht
gedruckt. Jede Seite ist als synthetische Testrechnung gekennzeichnet. Gleiche
Daten und gleiche ReportLab-Version ergeben identische Bytes. Die
Standardschrift unterstützt Windows-1252 einschließlich Umlauten; andere
Zeichen, Steuerzeichen, nichtendliche Zahlen und übergroße Eingaben
(2 000 Zeichen je Feld, 2 000 Positionen, 200 000 Zeichen gesamt, Beträge bis
10^15) werden mit `ValueError` abgewiesen. Fehlt ReportLab, meldet erst der
Aufruf `PDFDependencyError`. Kein PDF/A-, Signatur-, Barrierefreiheits- oder
Rechtskonformitätsnachweis.

## Herkunft und Charakterisierung

Das historische Profil stammt aus `janpow77/flowinvoice`
`docs/demo_data/generate_demo_invoices.py` (Commit `fb2d1856`). 180 vor der
Extraktion aufgezeichnete Fälle prüfen vollständige Ausgaben, Ausnahmetypen und
den Zustand der Zufallsquelle nach jedem Aufruf (**legacy-exakt**, einschließlich
Float-/`round`-Reihenfolge); der Quellpfad nutzt feste Datumskonstanten und
keine UUID- oder Uhrzeitfunktion. `InvoiceScenario` und der PDF-Renderer sind
Neuimplementierungen in auditcore. Firmen, Straßen und Orte kommen aus
`auditcore_dummygenerator`. Herkunftsdetails: [docs/provenance.md](docs/provenance.md).

## Bewusste Verhaltensabweichungen

Gegenüber der Quelle: der Prozess-globale Zufallsgenerator ist durch eine
instanzeigene `random.Random`-Quelle ersetzt, der Import seedet den Prozess
nicht mehr. `generate_invoice_legacy_global` ist ein ausdrücklich zu wählender
Kompatibilitätsadapter, der den globalen Zufallszustand wie das Original
verbraucht (nur sequenziell). Die globale 500er-Fehlerverteilung, CSV-Exporte und Dateischreibvorgänge
der Quelle bleiben Anwendungscode. Profile und Katalogkopien verhindern
unbeabsichtigte globale Katalogänderungen.

## Abhängigkeiten

Python ≥ 3.11. Pflicht: `auditcore_dummygenerator==0.1.3`. Optional
`reportlab>=4.5.1,<6` über `[pdf]` – eine getestete Versionslinie, keine
pauschale CVE-Grenze; Debian Bookworm führt die gepatchte Linie
`3.6.12-1+deb12u1` (Fix für CVE-2023-33733 laut
[DSA-5791-1](https://security-tracker.debian.org/tracker/DSA-5791-1)), deren
APT-Kompatibilität gesondert zu prüfen ist. Keine Plattform-, Web- oder
Datenbankabhängigkeit.

## Sicherheit und Datenschutz

Nur synthetische Daten; die USt-IdNr. ist sichtbar ein Platzhalter
(`SYNTHETIC-NOT-A-REGISTERED-VAT-ID`). Problemlabel wie `sanctions` oder
`ted_concentration` sind synthetische Trainingslabels und keine
Feststellungen über reale Personen oder Organisationen. Der PDF-Renderer
zeichnet ausschließlich Klartext: kein HTML/RML, keine Bilder, Links, Skripte,
Anhänge, Schrift- oder Netzwerkdownloads.

## Lizenz und Herkunftsnachweis

MIT (`LICENSE`). Am 22.09.2026 hat der Berechtigte die konkrete
Flowinvoice-Quelldatei ausdrücklich unter MIT freigegeben
(`USER_AUTHORIZED_MIT`); keine Umlizenzierung des gesamten Quellrepositories.
Details: `NOTICE`, `provenance.json`, [docs/provenance.md](docs/provenance.md).

## Änderungen

Siehe [CHANGELOG.md](CHANGELOG.md).
