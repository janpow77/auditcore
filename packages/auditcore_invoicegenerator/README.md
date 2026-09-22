# auditcore_invoicegenerator

Eigenständig installierbare Testrechnungsbibliothek mit vollständigen Parteien,
Positionen, numerischen Beträgen, Datumsfeldern und expliziten Fehlerfällen.
Die Anwendung bleibt ein eigenes Repository. Einzige Paketpflicht:
`auditcore_dummygenerator==0.1.0`; keine Plattform-, Web-, DB- oder PDF-Abhängigkeit.

```python
from datetime import date
from auditcore_invoicegenerator import InvoiceScenario, duplicate_invoice, to_json

scenario = InvoiceScenario(42, base_date=date(2026, 1, 15), country="DE")
invoices = scenario.generate_batch(3, errors={2: "wrong_total", 3: "missing_vat_id"})
invoices.append(duplicate_invoice(invoices[0], new_id="DOC-DUPLICATE"))
print(to_json(invoices))
```

`InvoiceScenario` verwendet installierte Dummy-Generatorfunktionen für Firmen,
Straßen, Hausnummern, Städte und Postleitzahlen. Länder DE/AT sind ausdrücklich
unterstützt. Parteien- und Rechnungszufall sind getrennt; gleicher Seed und
Bezugsdatum liefern auf frischen Instanzen gleiche vollständige Ergebnisse.
Instanzen werden sequenziell benutzt. Ein Aufruf verändert weder globalen
Zufallszustand noch übergebene Fehlerpläne. Der JSON-Renderer ist vollständig
enthalten; PDF/Scan/UBL/XRechnung sind nicht implementiert oder versprochen.

Fehler: `wrong_total`, `missing_vat_id`, `date_before_reference` und explizite
Duplikate. `metadata.injected_errors` benennt die beabsichtigte Abweichung;
`metadata.correct_values` erhält die vorherigen Vergleichswerte. Alle Rechnungen
sind synthetisch. Die verwendete VAT-ID ist sichtbar ein Platzhalter und weder
offizielle Registrierung noch Gültigkeitsbehauptung.

## Charakterisiertes historisches Profil

```python
from auditcore_invoicegenerator import FlowInvoiceDemoProfile, suppliers

profile = FlowInvoiceDemoProfile(seed=42)
invoice = profile.generate_invoice(1, suppliers()[0])
```

`flowinvoice-demo-fb2d185` erhält die beobachtete Rechnungslogik aus Flowinvoices
Demoquelle: feste Datumsbereiche, Empfänger, Positionskataloge, Länder-/Währungs-
tabellen, Float-/round-Reihenfolge und Zufallsziehungen. `generate_line_items`
garantiert ausdrücklich keine exakte Ausschöpfung seines Zielbetrags. Das sind
historische Trainingsregeln, keine aktuelle steuerrechtliche Auskunft.

180 vor Extraktion tatsächlich aufgezeichnete Fälle prüfen vollständige Ausgaben,
Ausnahmetypen und den Zustand der Zufallsquelle nach jedem Aufruf. Datum und UUID
werden nicht erfunden fixiert: der ausgewählte Quellpfad benutzt feste Datums-
konstanten und überhaupt keine UUID-/Wallclock-Funktion. Die Bibliothek ersetzt
nur den Prozessglobal-RNG durch eine instanzeigene `random.Random`-Quelle; der
Import seedet den Prozess nicht mehr. Die ursprüngliche globale 500er-Fehler-
verteilung, CSV-Exporte und main-Dateischreibvorgänge bleiben Anwendungscode.

Die einzelfallbezogene Komfortfunktion `generate_invoice(..., seed=42)` erzeugt
für jeden Aufruf eine frische Instanz. Für eine fortlaufende Legacy-Ziehfolge
muss dieselbe `FlowInvoiceDemoProfile`-Instanz verwendet werden. Profile und
Katalogkopien verhindern unbeabsichtigte globale Katalogveränderungen.

Problemlabel wie `sanctions` und `ted_concentration` sind ausschließlich
synthetische Trainingslabels. Sie sind keine Feststellungen über reale Personen
oder Organisationen. Der Portal-Generator besitzt einen anderen Vertrag und
wurde nicht damit gleichgesetzt.

## Installation und Prüfungen

Lokale Wheels beziehungsweise freigegebene Paketquelle vorausgesetzt:

```text
# requirements.txt
auditcore_invoicegenerator==0.1.0
```

`pip install -r requirements.txt` löst die deklarierte Dummy-Abhängigkeit auf.
Debian-Abbildung: `python3-auditcore-invoicegenerator` mit
`Depends: python3-auditcore-dummygenerator (= 0.1.0-1)` nach Paketierungsreview.
Eine normale venv sieht APT-Systempakete nicht automatisch.

```bash
pytest packages/auditcore_invoicegenerator/tests
ruff check packages/auditcore_invoicegenerator
mypy packages/auditcore_invoicegenerator/src
```

Das Paket steht unter MIT. Am 22.09.2026 hat der berechtigte Nutzer die konkrete
Flowinvoice-Quelldatei ausdrücklich dafür freigegeben (`USER_AUTHORIZED_MIT`).
`LICENSE`, `NOTICE` und `provenance.json` dokumentieren Lizenz und Herkunft.
Diese Freigabe behauptet keine Umlizenzierung des gesamten Quellrepositories oder
anderer Portalquellen. Technische Releaseprüfungen bleiben eigenständig.
