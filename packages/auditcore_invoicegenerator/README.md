# auditcore_invoicegenerator

Eigenständig installierbare Testrechnungsbibliothek mit vollständigen Parteien,
Positionen, numerischen Beträgen, Datumsfeldern und expliziten Fehlerfällen.
Die Anwendung bleibt ein eigenes Repository. Einzige Paketpflicht:
`auditcore_dummygenerator==0.1.1`; keine Plattform-, Web- oder DB-Pflichtabhängigkeit. PDF ist ein optionales Extra.

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
enthalten; PDF ist seit 0.2.0 optional verfügbar. Scan/UBL/XRechnung sind nicht implementiert.

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

### Optionaler PDF-Renderer ab 0.2.0

```bash
pip install 'auditcore_invoicegenerator[pdf]==0.2.1'
```

```python
from pathlib import Path
from auditcore_invoicegenerator import render_pdf

Path("synthetic-invoice.pdf").write_bytes(render_pdf(invoices[0]))
```

Der Renderer liefert Bytes und verändert keine Eingaben. Er druckt Parteien,
Rechnungs-/Leistungs-/Fälligkeitsdatum, alle Positionen, Einzelpreise, Mengen,
Währung, Steuerbetrag und Summen mit automatischem Seitenumbruch. Beabsichtigte
Rechenfehler werden nicht korrigiert; die Lösungshinweise in `metadata` werden
nicht auf der Rechnung verraten. Jede Seite trägt eine sichtbare Kennzeichnung
als synthetische Testrechnung. Bei identischen Daten und derselben ReportLab-
Version entstehen identische Bytes, unabhängig von der aktuellen Uhrzeit.

Die Standardschrift unterstützt Windows-1252 einschließlich deutscher Umlaute.
Andere Zeichen, Steuerzeichen, nichtendliche Zahlen und übergroße Eingaben werden
mit `ValueError` abgewiesen, statt Zeichen unsichtbar zu verlieren. Grenzen:
2000 Zeichen je Textfeld, 2000 Positionen, 200000 Zeichen insgesamt, Betrags-/
Mengengrößen höchstens 10^15. Die Anzeige nutzt zwei Nachkommastellen; die
fachlichen Floatwerte des Eingabedatensatzes bleiben unverändert.

Es werden ausschließlich Klartextzeichen gezeichnet: kein HTML/RML, keine Bilder,
Links, Skripte, Dateianhänge, Schrift- oder Netzwerkdownloads. Fehlendes ReportLab
führt erst beim PDF-Aufruf zu `PDFDependencyError` mit Installationshinweis. Der
JSON-/Generator-Kern lässt sich weiterhin ohne dieses Extra verwenden.

Das pip-Extra verwendet ReportLab ab 4.5.1 und unter 6 als getestete moderne
Abhängigkeitslinie; dieser Wert ist keine pauschale CVE-Grenze. Debian Bookworm
führt eine separat gepatchte Linie `3.6.12-1+deb12u1`, siehe
[Debian Security Tracker](https://security-tracker.debian.org/tracker/source-package/python-reportlab)
und [DSA-5791-1](https://security-tracker.debian.org/tracker/DSA-5791-1), das den
Fix für CVE-2023-33733 in genau dieser Debian-Revision ausweist.
APT-Kompatibilität muss mit dem tatsächlichen Debian-Paket geprüft werden;
die Upstream-Version allein beschreibt dessen Backports nicht. Der Renderer
verwendet keine ReportLab-Markupauswertung oder externen Bildquellen. Eine
Freigabe beliebiger ungepatchter alter PyPI-Versionen wird daraus nicht abgeleitet.

PDF ist ein Anzeigeformat dieser Testrechnungen, kein PDF/A-, Signatur-,
Barrierefreiheits-, UBL-, Scan- oder Rechtskonformitätsnachweis.

### Kernpaket

Lokale Wheels beziehungsweise freigegebene Paketquelle vorausgesetzt:

```text
# requirements.txt
auditcore_invoicegenerator==0.2.1
```

`pip install -r requirements.txt` löst die deklarierte Dummy-Abhängigkeit auf.
Debian-Abbildung: `python3-auditcore-invoicegenerator` mit
`Depends: python3-auditcore-dummygenerator (= 0.1.1-1)` nach Paketierungsreview.
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
