# Spezifikation auditcore_invoicegenerator

Stand: 26.09.2026, Paketversion 0.2.3. Charakterisierung: 180 am Original
(`janpow77/flowinvoice@fb2d1856`, `docs/demo_data/generate_demo_invoices.py`)
beobachtete Fälle in `tests/data/legacy-golden.json` bzw.
`tests/data/legacy-golden-cpython311.json` (Herkunft: `docs/provenance.md`).
Eigenschaftstests: `tests/test_spezifikation.py`.

## Zweck

Das Paket erzeugt synthetische Testrechnungen – Lieferant, Empfänger,
Positionen, Netto-, Steuer- und Gesamtbetrag, Rechnungs-, Leistungs- und
Fälligkeitsdatum – für Anwendungen, die Rechnungen auslesen oder prüfen
(Belegerkennung, Plausibilitätsprüfungen, Trainingsdaten). Fehlerfälle werden
nur auf ausdrücklichen Wunsch eingebaut und mit den richtigen Vergleichswerten
beschriftet. Es ist kein Rechnungsstellungssystem und gibt keine
steuerrechtliche Auskunft.

## Verträge

| Baustein | Eingabe | Ausgabe | Nebenwirkungen |
|---|---|---|---|
| `InvoiceScenario(seed, *, base_date, country="DE")` | ganzzahliger Seed, Bezugsdatum, Land `DE` oder `AT` | Szenario (Profil `invoice-scenario-v1`, Laufzeitkennung `synthetic-scenario-v1`) | keine; Parteien-Zufall aus `auditcore_dummygenerator`, Rechnungs-Zufall aus dem Altprofil, getrennt |
| `InvoiceScenario.generate(index, *, error="none")` | Index ≥ 1, Fehler `none`, `wrong_total`, `missing_vat_id`, `date_before_reference` | `InvoiceRecord` mit `metadata.profile`, `seed`, `base_date`, `injected_errors`, `correct_values` | – |
| `InvoiceScenario.generate_batch(total, *, errors=None)` | Anzahl ≥ 0, Fehlerplan `{Index (1-basiert): Fehler}` | Liste der Rechnungen 1…`total` | Fehlerplan bleibt unverändert |
| `duplicate_invoice(invoice, *, new_id)` | Rechnung, neue Dokumentkennung | unabhängige Kopie mit gleicher Rechnungsidentität, `injected_errors=["duplicate"]`, `duplicate_of` | Eingabe bleibt unverändert |
| `to_json(invoices)` | Rechnungen | UTF-8-fähiger JSON-Text (`ensure_ascii=False`, Einzug 2, `allow_nan=False`) mit Zeilenende | – |
| `render_pdf(invoice)` (Extra `pdf`) | eine Rechnung | PDF-Bytes, jede Seite als synthetische Testrechnung gekennzeichnet; beabsichtigte Rechenfehler werden gedruckt, Lösungshinweise nicht | – |
| `FlowInvoiceDemoProfile(seed=42)` | Seed | historisches Profil `flowinvoice-demo-fb2d185` mit instanzeigener Zufallsquelle | – |
| `generate_invoice(index, supplier, problem_type=None, *, seed=42)` | wie Original, Fehlerlabels aus `PROBLEM_TYPES` | Rechnung im Altformat, je Aufruf frische Zufallsquelle | – |
| `generate_invoice_legacy_global(...)` | wie Original | Rechnung im Altformat | verbraucht den prozessweiten Zufallszustand wie das Original |
| `suppliers()`, `problem_suppliers()`, `get_vat_rate(land)`, `get_currency(land)` | – bzw. Ländercode | Kopien der historischen Kataloge bzw. Demo-Steuersatz und Währung | – |

Rundung: Positionsbeträge `round(Einzelpreis · Menge, 2)`, Steuer
`round(Netto · Satz, 2)`, Gesamt `round(Netto + Steuer, 2)`; der Nettobetrag ist
die ungerundete `float`-Summe der Positionen (Altverhalten, siehe unten).
Steuersätze und Währungen sind historische Demowerte, keine geltenden Sätze.

## Invarianten

| Nr. | Invariante | Test |
|---|---|---|
| I1 | Frische Szenarien mit gleichem Seed, Bezugsdatum und Land erzeugen gleiche Rechnungen. | `test_i1_same_seed_and_reference_date_give_same_invoices` |
| I2 | Jede Szenariorechnung hat mindestens eine Position mit positivem Betrag; Positionsbetrag = `round(Preis · Menge, 2)` oder – bei gekappter Position – der Einzelpreis; Netto = Summe der Positionen; Steuer und Gesamt folgen den Rundungsregeln oben. | `test_i2_amounts_are_consistent` |
| I3 | Fehler entstehen nur auf Verlangen: Ohne Fehler ist `injected_errors` leer und die Rechnung gleich der fehlerfreien; mit Fehler weicht genau das benannte Feld ab, und `correct_values` enthält die Werte der fehlerfreien Rechnung. | `test_i3_errors_only_when_requested` |
| I4 | Szenariodaten: Rechnungsdatum = Bezugsdatum + (Index − 1) Tage, Leistungsdatum einen Tag davor, Fälligkeit 30 Tage danach. | `test_i4_scenario_dates_follow_the_reference_date` |
| I5 | Fehlerplan, Eingaberechnung und Kataloge werden nicht verändert; ein Duplikat ist eine unabhängige Kopie, die sich nur in `id` und `metadata` unterscheidet. | `test_i5_inputs_are_not_mutated` |
| I6 | `json.loads(to_json(r)) == r`; der Text endet mit einem Zeilenumbruch. | `test_i6_json_round_trip` |
| I7 | Altprofil ohne Fehlerlabel: Rechnungsdatum im festen Bereich 15.01.2025–30.01.2026, Leistungsdatum 1–14 Tage davor, Fälligkeit +30 Tage, Kennung `DOC-nnnnn`, `metadata` ohne Fehler. | `test_i7_legacy_profile_dates_and_identity` |
| I8 | `InvoiceScenario` und `FlowInvoiceDemoProfile` verändern den prozessweiten Zufallszustand nicht. | `test_i8_generation_leaves_the_global_random_state_alone` |
| I9 | Index < 1, Wahrheitswerte und Nicht-Ganzzahlen als Position (auch im Fehlerplan) werden mit `ValueError` abgewiesen. | `test_i9_invalid_positions_are_rejected` |
| I10 | Gleiche Rechnung und gleiche ReportLab-Version ergeben byte-gleiche PDF; die Eingabe bleibt unverändert. | `test_i10_pdf_is_deterministic` |

## Fehlerfälle

| Eingabe | Ergebnis |
|---|---|
| Land außer `DE`/`AT` in `InvoiceScenario` | `ValueError` |
| Index < 1, `bool` oder keine Ganzzahl; Anzahl < 0; Fehlerindex außerhalb des Stapels; unbekannter Fehler | `ValueError` |
| `render_pdf` ohne Extra `pdf` | `PDFDependencyError` (erst beim Aufruf) |
| PDF-Eingabe mit Zeichen außerhalb Windows-1252, Steuerzeichen, nichtendlichen Zahlen, mehr als 2 000 Zeichen je Feld, 2 000 Positionen, 200 000 Zeichen gesamt oder Beträgen über 10^15 | `ValueError` |
| `FlowInvoiceDemoProfile.generate_batch` mit negativer oder nicht ganzzahliger Anzahl | `ValueError` |

## Abgrenzung

- Keine gültigen Steuer- oder Registerkennungen: Szenarien setzen
  `SYNTHETIC-NOT-A-REGISTERED-VAT-ID`; das Altprofil trägt historische
  Demowerte. Prüfung von Kennungen: `auditcore_identifiers`.
- Keine E-Rechnungsformate (XRechnung, UBL, ZUGFeRD), kein Scan-Rendering,
  keine PDF/A-, Signatur- oder Barrierefreiheitszusage.
- Die Fehlerlabels des Altprofils (`sanctions`, `duplicate` …) sind
  Trainingsbeschriftungen, keine Aussagen über reale Unternehmen.
- Dateien, CSV-Exporte und die 500er-Fehlerverteilung des Originals bleiben
  Anwendungscode.

## Bewusste Abweichungen vom Altverhalten

| Altverhalten | Gewolltes Verhalten | Nachweis |
|---|---|---|
| Import setzt `random.seed(42)`, alle Aufrufe teilen den prozessweiten Zufall | instanzeigene `random.Random`; Import ohne Nebenwirkung | I8, `tests/test_invoices.py` |
| globale Kataloge konnten versehentlich verändert werden | `suppliers()`/`problem_suppliers()` liefern Kopien | `tests/test_invoices.py` |

Beibehaltene Altfehler (Legacy-Varianten; nicht für neue fachliche Annahmen
gedacht):

| Legacy-Variante | Verhalten | Empfehlung |
|---|---|---|
| `FlowInvoiceDemoProfile` | legacy-exakte Ziehfolge; `amounts.subtotal` ist die **ungerundete** `float`-Summe (unter CPython 3.11 in neun der 180 Fälle andere letzte Binärstellen als unter 3.12) | für exakte Summen in Tests Positionen mit `Decimal` nachrechnen |
| `FlowInvoiceDemoProfile.generate_line_items` | schöpft den Zielbetrag nicht aus (höchstens fünf Positionen, Abbruch unter 200 Restbetrag) | nicht als Zielbetragsgenerator verwenden |
| `get_vat_rate` | historische Demo-Steuersätze (z. B. RU 0,00) | keine steuerliche Aussage ableiten |
| `generate_invoice_legacy_global` | verbraucht und schreibt den prozessweiten Zufallszustand wie das Original; nur sequenziell | nur für den charakterisierten Altverbraucher |
