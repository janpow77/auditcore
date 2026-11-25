# Changelog auditcore_dummybundle

## 0.3.1 – 2026-11-24

- Bindung an `auditcore_identifiers==0.3.1` (nur die Zusammenfassung von
  `POST /check/batch` geändert, die das Paket nicht nutzt). Gleicher Startwert
  ergibt dieselben Daten wie 0.3.0; nur die Paketversion in `meta.version`,
  im Rezept und in `library` lautet 0.3.1. Neue Version, weil die exakte Bindung
  an 0.3.0 sonst neben `auditcore_identifiers` 0.3.1 nicht installierbar wäre.

## 0.3.0 – 2026-11-23

**Verhaltensänderung:** Gleicher Startwert ergibt andere Daten als 0.2.0 –
in der Ländermischung DE+AT (Rechnungssteller und ihre USt-IdNr., damit der
Steuersatz je Beleg, Vergabearten), in AT-Bündeln (Vergabearten), beim
gezahlten Betrag von Belegen ohne Vorsteuerabzug (bis zu einem Cent) und bei
den eingestreuten Auffälligkeiten `payment_deadline_exceeded` und
`direct_award_above_limit` (AT). Vorhaben und Mittelabrufe bleiben gleich.

- **Ländermischung DE+AT:** Rechnungssteller kommen aus dem Land des
  Vorhabens; der Lieferantenpool wechselt zwischen DE und AT ab. Der
  Steuersatz folgt dem Land des Rechnungsstellers (DE 19 %, AT 20 %). Bisher
  stellten österreichische Lieferanten deutschen Vorhaben 19 % in Rechnung
  und umgekehrt, obwohl eine grenzüberschreitende Leistung zwischen
  Unternehmern keine Inlandssteuer des Leistenden trägt. Neues Belegfeld
  `supplier_country`.
- **Vergabeart nach dem Recht des Auftraggebers:** Österreichische öffentliche
  Auftraggeber tragen „Direktvergabe (BVergG 2018)“, „Offenes Verfahren
  (BVergG 2018)“ oder „Nicht offenes Verfahren mit vorheriger Bekanntmachung
  (BVergG 2018)“ (§ 31 Abs. 2, 3 und 11, § 33 BVergG 2018) statt VOB/VOL. Die
  Auffälligkeit `direct_award_above_limit` setzt die Bezeichnung des Landes.
- **Skonto:** Neues Belegfeld `discount_gross` (Skonto auf den Bruttobetrag);
  brutto − `discount_gross` = gezahlter Betrag gilt auf den Cent. Ohne
  Vorsteuerabzug ist der gezahlte Betrag gleich dem projektbezogenen.
  `discount_amount` bleibt das Skonto auf die Bemessungsgrundlage (V4).
  Negative Belege negieren beide Skontofelder mit.
- **Vorlage N1 0.2.0:** Spalte „Skontobetrag“ zeigt `discount_gross` und hat
  einen Spaltenhinweis. Das Profil hat einen neuen Inhaltshash und steht bis
  zur neuen Freigabe des Rechteinhabers auf „Entwurf“ / `NOT_GRANTED`
  (`provenance.json` → `profile_release.pending`). Die übrigen zehn Profile
  sind unverändert freigegeben.
- **Auszahlungsfrist überschritten:** Die eingestreute Verzögerung endet
  spätestens am Bezugsdatum, am Stichtag des Zahlungsantrags des
  Mittelabrufs und vor der Aufdeckung einer Korrektur; die Grundgesamtheit
  übernimmt das Auszahlungsdatum. Bisher lagen Auszahlungen mit Status
  „ausgezahlt“ hinter dem Bezugsdatum.
- Hinweis zum Feldtyp `company` berichtigt: Namen sind innerhalb einer Spalte
  verschieden und wiederholen sich erst nach 25.920 Zeilen.
- Pin `auditcore_identifiers==0.3.0`.

## 0.2.0 – 2026-10-17

**Verhaltensänderung:** Gleicher Startwert ergibt andere Daten als 0.1.0.

- Firmennamen aus dem Namensbaukasten von `auditcore_dummygenerator` 0.2.0
  statt aus dessen Zehnerliste `companies`: Begünstigte, Lieferanten und
  Spalten `company` der freien Tabelle tragen innerhalb eines Bündels
  verschiedene Namen; die Rechtsform folgt `entity_form`
  (öffentlich-rechtlich → AöR, Zweckverband, Eigenbetrieb).
- Weil die Namensziehung keine Zahl mehr aus dem Strom des Vorhabens bzw.
  Lieferanten verbraucht, verschieben sich dort auch die folgenden Werte
  (USt-IdNr., IBAN, Anschrift usw.).
- Pin `auditcore_dummygenerator==0.2.0`.

## 0.1.0 – 2026-10-13

Erstfassung. Zusammenhängende Bündel (Vorhaben → Mittelabrufe → Belege →
Zahlungsanträge → Rechnungslegung) mit Summenbindung in Dezimalrechnung,
Vorlagenprofile als Daten, freie Tabelle aus einem Rezept, Auffälligkeiten mit
getrennter Lösung, REST-Vertrag `dummybundle_ui/1`.

- `amounts.allocate` und `amounts.split_random`: die eine Fassung der
  Betragsverteilung mit Restausgleich (`Decimal`, centgenau, Rest in den
  letzten Teil).
- `build_bundle`, `run_checks`: kanonische Tabellen und die acht Summenproben.
- Elf Vorlagenprofile V0 bis V9 und N1 (Belegliste zum Mittelabruf, kompakt),
  alle öffentlich, vom Rechteinhaber am 13.10.2026 freigegeben, jedes mit
  Inhaltshash. Köpfe von V5 und V6 aus dem Amtsblatt (ABl. L 231 vom
  30.6.2021, deutsche Fassung, Abruf 13.10.2026).
- Freie Tabelle: 21 Feldtypen, Regeln `when` und `sum_to`, Anteil leerer
  Werte, eigene Zufallsfolge je Spalte, strenges Laden des Rezepts.
- 13 Auffälligkeiten; Lösung mit `gt_`-Feldern nur auf Wunsch.
- IBAN und USt-IdNr. standardmäßig mit gezielt verfehlter Prüfziffer.
- Firmennamen aus der Liste `companies` von `auditcore_dummygenerator`.
