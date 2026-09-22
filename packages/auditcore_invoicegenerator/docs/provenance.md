# Herkunft und Vertragsgrenzen

Quelle: `janpow77/flowinvoice@fb2d18568d2eaf64574d131ceae51a936b9aac02`,
`docs/demo_data/generate_demo_invoices.py`.
Die gelesenen Quelldateibytes wurden gegen den GitHub-Blob
`8f1596a711b228194b58ffc5db6a6e7d0ed049a3` bestätigt; SHA256 und tatsächlich
beobachtete Characterization-Zeit stehen in `provenance.json`.

Die ursprüngliche Datei verwendet beim Import `random.seed(42)`. Vor Übernahme
wurden 180 Fälle im Original tatsächlich ausgeführt: vollständige Rechnungen
für alle Ländervarianten, alle sechs Fehlerlabels, Positionen jeder Kategorie
an Betragsgrenzen, Currency-/VAT-Katalog, Daten und Fehlereingaben. Ergebnisse
und SHA256 des nachfolgenden RNG-Zustands wurden als Golden-Daten gespeichert.
In diesem Quellpfad gibt es weder aktuelle Uhrzeit noch UUID-Aufrufe. Der
unveränderte historische Datumsbereich ist Teil des Legacyvertrags.

Die erste Golden-Beobachtung erfolgte unter CPython 3.12. Der ursprüngliche
Algorithmus verwendet für die ungerundete Zwischensumme das eingebaute `sum`.
CPython 3.11 liefert bei neun der 180 Fälle andere letzte Binärstellen als
3.12/3.13. Deshalb wurde derselbe unveränderte, SHA256-geprüfte Originalquelltext
zusätzlich unter CPython 3.11.2 in einem isolierten Debian-Container ausgeführt.
`tests/data/legacy-golden-cpython311.json` enthält diese tatsächlich beobachteten
Ergebnisse einschließlich Interpreterversion und Beobachtungszeit. Die Tests
wählen unter CPython 3.11 diesen Originalvergleich, sonst den bisherigen Golden.
Die tatsächlichen CI-Matrizen prüfen CPython 3.11, 3.12 und 3.13.

Die beiden Beobachtungen unterscheiden sich ausschließlich in neun ungerundeten
`amounts.subtotal`-Werten. Positionsbeträge, gerundete Steuer-/Gesamtbeträge, alle
anderen Felder und RNG-Endzustände stimmen exakt überein; ein eigener Test prüft
diese Grenze. Jeder Lauf vergleicht weiterhin das vollständige Ergebnis exakt.
Es werden keine Näherungsvergleiche oder nachträglichen Betragsrundungen eingeführt.
Die Runtime behält damit die native Semantik des Originalcodes auf dem jeweiligen
Interpreter, statt eine fachlich unbeauftragte Rechenänderung vorzunehmen.

Die Extraktion injiziert `Random`, damit reguläre Bibliotheksimporte/-Instanzen
keine globale Zufallsquelle ändern. Alle beobachteten Ziehfolgen bleiben gleich.
`generate_invoice_legacy_global` ist der ausdrücklich benannte Kompatibilitätsweg
für vorhandene sequenzielle Consumer: Er übernimmt den Globalzustand und schreibt
den fortgeschrittenen Zustand zurück, auch bei Ausnahmen. Dieser Adapter ist
nicht für parallele Verwendung derselben Prozessglobalquelle freigegeben.

Das neue `InvoiceScenario`-Profil verwendet die tatsächlich deklarierte
Dummy-Bibliothek für Parteien. Bezugsdatum und Fehlerplan gehören zum expliziten
Szenariovertrag. Diese API ist keine Behauptung, dass Portal-, Worker- oder
steuerrechtliche Berechnungsregeln vereinheitlicht seien.

Beim ursprünglichen Quellabruf wurde kein Lizenzgrant gefunden (`UNKNOWN`).
Am 22.09.2026 bestätigte der Nutzer seine Berechtigung und erteilte ausdrücklich
die MIT-Freigabe für genau diese Quelldatei (`USER_AUTHORIZED_MIT`). `LICENSE`,
`NOTICE` und die strukturierte Provenienz halten diesen neuen Nachweis fest.
Die Rechtebehauptung erstreckt sich nicht auf das gesamte Repository oder andere
Portalquellen. Technische Reviews und tatsächliche Publikation bleiben getrennt.

Der ApplicabilityContext beschreibt die isolierte Testdatenbibliothek, inklusive
Dokument-/Exportfunktionen und versionierter Demo-Regeln/Vorlagen. Er ist kein
Kontext für produktive Rechnungsstellung. Bekannte Benutzer-, Auth-, KI- und
personenbezogene Echtdatenverarbeitung fehlen diesem isolierten Kern; Consumer
werden getrennt bewertet. Anwendbare F-04/F-09/F-15-Nachweise bleiben erforderlich;
ein Unit-Test-Lauf ersetzt keine fachliche oder Veröffentlichungsfreigabe.
