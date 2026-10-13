# Spezifikation auditcore_dummybundle 0.1.0

Stand 13.10.2026. Grundlage ist der Vorlagenvorschlag „Dummydaten-Generator für
ecohesion.flowaudit.de“ vom selben Tag. Was dort als nicht belegt geführt
wird, ist hier nicht erfunden, sondern leer oder als Platzhalter erkennbar.

## 1 Zweck und Abgrenzung

Das Paket erzeugt aus einem Startwert und einem Bezugsdatum ein
zusammenhängendes Bündel synthetischer Tabellen und projiziert es in
Vorlagen. Daneben erzeugt es freie Tabellen aus einem Rezept. Es schreibt
keine Dateien, kennt kein Web-Framework und keine Datenbank.

`auditcore_dummygenerator` bleibt unverändert: `generator.py` ist über den
Implementierungshash an 27 Profile gebunden und gegen 58 Altfälle
festgeschrieben. Das Bündel ist deshalb ein Schwesterpaket und nutzt vom
Feldgenerator die Firmenliste und die Kataloge DE/AT (Städte mit
Postleitzahl, Vor- und Nachnamen, Verwendungszwecke).

## 2 Die eine Betragsverteilung

`amounts.allocate(total, weights)` teilt einen Betrag proportional auf;
jeder Teil außer dem letzten wird auf den Cent abgerundet, der letzte nimmt
den Rest. `amounts.split_random` zieht dafür gestreute Gewichte und hält einen
Mindestbetrag je Teil ein. Gerechnet wird ausschließlich in `Decimal`;
`quantize` und `share` runden kaufmännisch. Diese Fassung ist für die
Anwendungen gedacht, die die Verteilung bisher getrennt programmiert haben.

## 3 Kanonische Tabellen des Bündels

| Tabelle | Eine Zeile je | Bindung |
|---|---|---|
| `operations` | Vorhaben | Summe der Finanzierungsquellen = förderfähige Ausgaben |
| `claims` | Mittelabruf | Summe je Vorhaben ≤ bewilligter Betrag; förderfähig = Anforderung − Kürzungen |
| `receipts` | Beleg | Summe der projektbezogenen Beträge = Anforderung des Mittelabrufs |
| `payment_applications` | Zahlungsantrag und Priorität, dazu „Endsumme“ | Summe der Mittelabrufe bis zum Stichtag abzüglich Herausnahmen, aufgelaufen |
| `corrections`, `findings` | Korrektur bzw. Feststellung | Betrag ≤ anerkannter Betrag des Belegs |
| `accounts_head`, `accounts_annex1` … `accounts_annex7` | Zeile der Anlage | Abstimmung nach Abschnitt 4 |
| `population` | Stichprobeneinheit | Summe = Spalte (B) des abschließenden Zahlungsantrags |

Jede Einheit zieht aus einer eigenen Zufallsfolge, abgeleitet aus Startwert
und fachlichem Schlüssel (`seeds.stream(seed, "receipt", <Mittelabruf>, <Nr.>)`).
Mehr Vorhaben verschieben die vorhandenen nicht.

Zeitgerüst: Das Geschäftsjahr (1. Juli bis 30. Juni) ist dasjenige, in dem
das Bezugsdatum liegt. Bewilligung und Beginn des Durchführungszeitraums
liegen davor, das Ende danach. Mittelabrufe werden so früh gestellt, dass ihre
Auszahlung im Geschäftsjahr liegt; ein Mittelabruf zählt zu dem
Zahlungsantrag, dessen Stichtag seine Auszahlung abdeckt. Zahlungsanträge
tragen als Einreichungsdatum das Ende eines Zeitraums nach Art. 91 Abs. 1
(31.10., 30.11., 31.12., 28.2., 31.5., 31.7.); der letzte ist der
abschließende Antrag.

Korrekturen gehen zwei Wege. Eine **Herausnahme** ist ein negativer Betrag in
einem späteren Zahlungsantrag desselben Geschäftsjahres und steht in Anlage 2;
sie wird nur gebucht, wo der Antrag im Zeitraum nicht negativ wird. Ein
**unmittelbarer Abzug** steht nur in der Rechnungslegung und erklärt die
Differenz der Anlage 4. Herausnahmen stehen als negative Einheiten in der
Grundgesamtheit.

## 4 Invarianten

Die acht Summenproben (`run_checks`, je ein Test in `tests/test_sum_checks.py`):

1. Summe der projektbezogenen Beträge der Belege = Anforderung des Mittelabrufs.
2. anerkannt = projektbezogener Betrag − Kürzung; Differenz = anerkannt − förderfähig.
3. Summe der förderfähigen Beträge der Mittelabrufe eines Vorhabens ≤ bewilligte förderfähige Ausgaben.
4. Zahlungsantrag je Priorität = Summe der Mittelabrufe bis zum Stichtag abzüglich Herausnahmen; aufgelaufen nicht fallend.
5. Summe der Grundgesamtheit = Spalte (B) des abschließenden Zahlungsantrags.
6. Anlage 4: (E) = (A) − (C) = Summe der Abzüge; Anlage 1 (A) = Anlage 4 (C).
7. Anlage 2 (A) = Summe der Herausnahmen; die Aufteilung nach Geschäftsjahr geht auf.
8. Öffentlicher Beitrag = förderfähiger Betrag × öffentlicher Anteil je Mittelabruf; der Rundungsrest der Summenzeilen ist ausgewiesen.

Dazu als Eigenschaftstests für jeden Startwert (`tests/test_properties.py`):
Datumsfolgen (Antrag < Bewilligung ≤ Beginn; Rechnung ≤ Zahlung ≤ Antrag des
Mittelabrufs; Antrag ≤ Eingang < Auszahlung, höchstens 80 Tage), brutto =
netto + Umsatzsteuer, Bemessungsgrundlage − Skonto = projektbezogener Betrag,
gleiche Eingabe ergibt gleiche Ausgabe.

Der Skontobetrag ist die Differenz aus Bemessungsgrundlage und
projektbezogenem Betrag und kann um einen Cent vom gerundeten Satz abweichen;
so bleibt Probe 1 exakt.

## 5 Vorlagen

Vorlagen sind Daten (`template_data/*.json`), kein Code. Eine Spalte nimmt
ihren Wert aus einem kanonischen Feld (`field`, auch über die Elternzeile als
`operation.<Feld>` oder `claim.<Feld>`), ist eine Konstante (`const`) oder
bleibt leer und begründet das in `note`. `split_by` erzeugt eine Tabelle je
Mittelabruf, `total_row` eine Summenzeile, `row_kinds` wählt Zeilenarten,
`free` beschreibt das Gegenstück der Spalte in der freien Tabelle.

| Vorlage | Tabellen | Öffentlich | Bemerkung |
|---|---|---|---|
| V0 Vorhabenstamm | 1 | ja | Beihilferegelung leer |
| V1 Belegliste zum Mittelabruf (ausführlich, 37 Spalten) | je Mittelabruf | ja | Aufbau einer in der Förderpraxis gebräuchlichen Belegliste; sieben Auswahlspalten leer |
| V2 Belegliste der Vorhabenprüfung | je Mittelabruf | ja | Spalten A–Z; V–Z leer |
| V3 Gesamtbelegliste des Vorhabens | 1 | ja | V1 mit „Quelldatei“ |
| V4 Mittelabruf | 2 | ja | nur Datenfelder, kein Formular |
| V5 Zahlungsantrag (Anhang XXIII) | 2 | ja | ohne Regionenkategorien; Anlagen 1–4 nicht erzeugt |
| V6 Rechnungslegung (Anhang XXIV) | 8 | ja | Anlagen 3 und 7 mit Nullbeträgen, Anlage 6 ohne Zeilen |
| V7 Abzüge und Korrekturen | 2 | ja | ohne Wiedereinziehungen |
| V8 Liste der Vorhaben | 1 | ja | vier Spalten leer |
| V9 Grundgesamtheit | 1 | ja | ohne Stichprobenziehung |
| N1 Belegliste zum Mittelabruf (kompakt) | 1 | ja | Inhalte von V1 in kompakter Form unter allgemeinen Spaltennamen |

Alle elf Profile sind am 13.10.2026 vom Rechteinhaber freigegeben
(`docs/profile-versioning.md`); der Schalter `public` bleibt als Mechanismus
erhalten.

Nicht gebaut: Personal- und Stundenliste, Vergabeübersicht (Aufbau nicht
belegt). Nicht übernommen: Szenario, Fälle, Lösungen und Handouts des
Seminars, Teilnehmer- und Mandantenbezug, Programm- und CCI-Angaben eines
Landes, Kürzungsgrundkatalog, Kostenartenbezeichnungen aus Bescheiden.

**Abgleich V5/V6 mit dem Amtsblatt.** Quelle: ABl. L 231 vom 30.6.2021,
S. 159, deutsche Fassung, abgerufen am 13.10.2026 über
`http://publications.europa.eu/resource/celex/32021R1060` (Ursprungsfassung).
Die Zuordnung der Spalten (A)–(E) des Hauptvordrucks und der Anlagen 1, 2, 4
und 7 der Rechnungslegung ist bestätigt; die Köpfe sind wörtlich übernommen,
Fußnotenzeichen entfernt. Offen: konsolidierte Fassung und Berichtigungen; ob
der Hauptvordruck je Geschäftsjahr aufgelaufen zu führen ist, sagt die
Verordnung nicht wörtlich (das Bündel weist aufgelaufen aus und führt den
Zeitraumbetrag als Rechenhilfe); Berechnung der technischen Hilfe.

## 6 Auffälligkeiten

Eingestreut nach dem Bau des stimmigen Bündels, nur in Tabellen, die
ausgegeben werden. Die Datentabellen tragen keine Spalte, die das Ergebnis
verrät; die Lösung ist eine eigene Ausgabe, nur auf Wunsch. Ihre Felder
tragen das Präfix `gt_`: `gt_code`, `gt_title`, `gt_table`, `gt_row_number`
(Zeile im Datenbereich, beginnend mit 1; eine obenstehende Summenzeile zählt
mit), `gt_row_key`, `gt_field`, `gt_original`, `gt_planted`,
`gt_expected_amount`, `gt_reason`, `gt_affected_checks`. Aggregierte Tabellen
behalten die Werte des stimmigen Bündels.

Dreizehn Auffälligkeiten: bezahlt vor Rechnung; förderfähig über gezahlt;
negative Beträge; Beleg außerhalb des Durchführungszeitraums; Doppelbeleg;
fehlendes Zahlungsdatum; Skonto nicht abgezogen; Umsatzsteuer trotz
Vorsteuerabzug; Kostenart außerhalb des Kostenplans; Rechenfehler;
Direktauftrag über der eingestellten Wertgrenze; Mittelabruf über der Summe
der Belege; Auszahlungsfrist von 80 Tagen überschritten. Nicht gebaut sind
„Häufungsmuster“ (nicht bestimmt genug) und „Stundensatz oder Stunden
falsch“ (setzt die nicht gebaute Stundenliste voraus). Die Wertgrenze für
Direktaufträge ist ein Parameter des Generators, keine Rechtsaussage.

## 7 Freie Tabelle

Ein Rezept (`auditcore.dummybundle.recipe`, Fassung 1) nennt Lauf (Startwert,
Bezugsdatum, Zeilen, Land), Paketversion und Felder. Feldtypen: laufende
Nummer, Nummer mit Muster, Person, Firma mit Rechtsform, Anschrift,
Gebietskennung, E-Mail-Adresse, Datum im Bereich, Datum nach oder vor anderer
Spalte, Betrag, Betrag aus anderer Spalte, berechnete Spalte (Summe,
Differenz, Produkt, Spalte mal Satz), ganze Zahl, Dezimalzahl, Auswahl mit
Gewichten, Wahrheitswert, Text, IBAN, BIC, USt-IdNr., Konstante. Jedes Feld
kann einen Anteil leerer Werte und eine Regel tragen: `when` (Wert abhängig
von einer anderen Spalte) oder `sum_to` (Summe der Spalte, auch je Gruppe,
gleich Vorgabewert).

Erzeugt wird spaltenweise in Abhängigkeitsreihenfolge; die Reihenfolge der
Ausgabe bleibt die des Rezepts. Jede Spalte hat ihre eigene Zufallsfolge. Das
Laden ist streng: unbekannte Schlüssel, Typen, Parameter, Verweise, Kreise und
doppelte Namen werden mit Pfad abgewiesen. Eine Definition, die sich nicht
erfüllen lässt (Text als Rechenspalte, Minimum über Maximum), wird vor der
Ausgabe gemeldet. Aus einem Rezept anderer Paketversion entsteht ein Hinweis:
gleiche Daten sind nur mit derselben Version zugesagt.

Nicht enthalten: Telefonnummern (kein belegter Bereich nicht zugeteilter
Nummern), ein Merkmal „eindeutig“, Verteilungen nach Klassen.

## 8 Kennungen und Namen

Firmennamen kommen aus der Liste `companies` von `auditcore_dummygenerator`
und werden wie dort gezogen (ein Name je Ziehung, mit Zurücklegen). Die Liste
hat zehn Einträge; in größeren Bündeln wiederholen sich Namen, Begünstigte
unterscheidet die Kennung `BEN-…`. Es sind generische Beispielnamen;
Ähnlichkeiten mit bestehenden Unternehmen sind zufällig und nicht
beabsichtigt.

IBAN: Bankteil mit führender `0`, richtige Prüfzahl über
`auditcore_identifiers.iban_check_digits`, im Standard um eins verfehlt (nie
kongruent modulo 97). USt-IdNr.: Prüfziffer über `de_vat_check_digit` bzw.
`at_uid_check_digit`, im Standard um eins verschoben. BIC: fest
`SYNT<Land>X0`. Garantiert ist die verfehlte Prüfziffer; die übrigen
Vorkehrungen sind Übung, kein belegter Sperrbereich. `valid=True` bzw.
`identifiers_valid` ist eine ausdrückliche Wahl für den Test von Prüfroutinen.

## 9 REST-Vertrag `dummybundle_ui/1`

`web.catalogue`, `web.generate`, `web.recipe_from_template`,
`web.check_recipe` sind frei von Web-Frameworks. Fehler haben die Form
`{"error": {"code", "message", "path"}}` mit Status 422, 413 (zu groß) oder
503 (Zeitgrenze). `web.Limits` begrenzt Vorhaben, Mittelabrufe, Belege,
Zeilen, Felder, Tabellen, Vorschauzeilen, Zeit und Rumpfgröße; nicht
öffentliche Vorlagen erscheinen nur mit `include_private=True`. Es gibt
keinen parallelen Weg; `_meta.max_workers` ist stets 1.

## 10 Offene Punkte

- Belegter Testbereich für Bankleitzahl, IBAN und Steuernummer.
- `auditcore_invoicesynth.enrich._split_amount` ist eine weitere eigene
  Zerlegung; sie ist an eine Zufallsfolge gebunden und bleibt unverändert.
