# Changelog auditcore_dummybundle

## 0.1.0 – unveröffentlicht

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
