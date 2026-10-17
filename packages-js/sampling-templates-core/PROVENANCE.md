# Herkunft

## Referenz

Fachliche und rechnerische Referenz ist ausschließlich die Excel-Arbeitsmappe
„Stichprobenvorlagen 2021–2027“ nach DelVO (EU) 2023/67, Fassung 4
(25 Blätter): ein Arbeitsentwurf einer Prüfbehörde, Stand Oktober 2026, keine
amtliche Fassung der Kommission. **Die Arbeitsmappe, ihre Zellbeschreibung
(`vorlage_zellen.json`) und die Formelübersichten liegen nicht im Repository.**
Werkzeuge, die sie brauchen, lesen sie aus `AUDITCORE_SAMPLING_TEMPLATES_DIR`
oder aus `.vorlage/` (von git ausgeschlossen); die Tests laufen ohne sie.

## Was aus der Vorlage im Paket steckt

| Inhalt | Ort | Umfang in 0.1.6 |
|---|---|---|
| Rechenwege (Formeln als TypeScript, Zelle für Zelle) | `src/sheets/<Blatt>/compute*.ts`, `src/sheets/shared/*.ts` | alle Blätter: 02–18, 20, X1–X4 |
| Bezeichnungen (Spalte B), Fundstellen und Hinweise (Spalte D bzw. K), Abschnittstitel, Zahlenformate, Vorgaben | `src/sheets/<Blatt>/definition*.ts` | alle Blätter, wörtlich; Bezeichnungen mit Formel in Bezeichnung und Kurzformel getrennt. Altvorlagen: englischer Wortlaut der Vorlage von 2017 |
| Prüfhinweistexte (✔/⚠/✖), wortgleich | `src/sheets/<Blatt>/compute*.ts`, `src/sheets/shared/*.ts` | alle Blätter |
| Texte und Aufbau der Druckfassung (Blatt 20); Programm und Behörde sind Angaben der Prüfbehörde, kein fester Text | `src/sheets/20_Druck_KOM/` | vollständig |
| Tabelle der Zuverlässigkeitsfaktoren (Blatt X1a), 574 Zellen | `src/sheets/X1a_RF_2017/table.ts` | vollständig |
| Englische Arbeitsübersetzung dieser Texte (eigene Übersetzung, als solche gekennzeichnet) | `src/sheets/<Blatt>/texts.en.ts`, `src/catalog/texts.en.ts` | alle Blätter, Katalog |
| z-Werte und Auswahllisten aus Blatt 01 | `src/sheets/01_Parameter/index.ts` | vollständig (z-Werte aus Anhang I DelVO) |
| Blattnamen, Inhaltsangaben, Rechtsgrundlagen und Bezug zur Vorlage 2017 aus Blatt 00; Hinweis zu drei Zeiträumen geschichtet | `src/catalog/catalog.ts`, `src/sheets/registry.ts` | alle 23 Blätter |
| Erwartete Werte der Formelzellen (Zahlen, Prüfhinweistexte) aus der Neuberechnung der Vorlage | `test/golden/*.golden.json` | alle Blätter; Umfang in `docs/abgleich.md` |
| Statistik der verwendeten Excel-Funktionen | `docs/excel-funktionen.md` | Anzahl je Funktion |

Damit wären bei einer Veröffentlichung dieses Stands im Repository versioniert:
die Rechenwege aller Blätter, sämtliche Bezeichnungen, Fundstellen, Hinweise
und Prüfhinweistexte der Vorlage, der Text der Druckfassung, die Tabelle X1a
und die aus der Vorlage errechneten Sollwerte – also der fachliche Gehalt der
Vorlage vollständig, nur nicht die Arbeitsmappe als Datei.

Nicht enthalten: die Arbeitsmappe selbst, der Wortlaut der Formeln als
Excel-Formeln, die Erläuterungstexte der Blätter 00 und 19, die Bilder und
das Zellenlayout.

Beispielwerte (`sample`) und alle Testfälle sind erfunden und stammen aus
keiner Prüfung.

## Charakterisierung

Die Sollwerte (`test/golden/`) stammen seit Fassung 0.1.6 aus **Microsoft
Excel** (Microsoft 365, Version 16.0.20326.20142, 64 Bit, de-de; Excel-Gegenprobe
vom 17.10.2026): Die Eingaben jedes Falls wurden über COM in die geöffnete
Vorlage geschrieben, die Mappe mit `CalculateFull` neu berechnet und jede
Formelzelle bitgenau ausgelesen (10.531 Fälle, 728.895 Zellen, ohne Fehler und
ohne Dialog). Vorher entstanden die Sollwerte mit `scripts/golden_recalc.py`,
das die Vorlage mit LibreOffice (24.2.7.2) ohne Oberfläche neu rechnet; diese
Fassung liegt in der Versionsgeschichte (0.1.5) und weicht in 937 Zellen von
Excel ab. `scripts/golden_recalc.py` bleibt als Hilfsmittel für vorläufige
Sollwerte neuer Fälle. `test/golden.spec.ts` vergleicht jede Zelle
(Zellen mit Ganzzahlformat exakt, übrige relative Toleranz 1e-9, Texte
wortgleich); Ergebnis in `docs/abgleich.md`. Eine Abweichung ist nur
zugelassen, wenn die Webfassung keinen Wert zeigt, die Abweichung als Datum
erklärt ist, eine der genannten Eingaben leer ist und die Gegenprobe mit 0
den Wert der Vorlage ergibt.

Je Blatt gibt es benannte Fälle (Verzweigungen, Schwellen, Teilbelegungen) und
mindestens 100 zufällige vollständige Belegungen mit festem Startwert
(`scripts/random-cases.mjs`). 158 Fälle des Blatts 03 stammen aus einer
unabhängigen Prüfung des Fundaments (`test/cases/03_MUS_1Z.pruefer.json`).
Geprüft sind zwei Richtlinien für fehlende Angaben: die geltende (0
unbegründete Abweichungen) und „wie die Vorlage“ (0 Abweichungen). Vergleiche, Differenzen,
Aufrunden, `VERGLEICH` und Summen sind an Microsoft Excel 16.0.20326 gemessen
(`test/fixtures/excel-semantik.json`: 814 Vergleiche, 193 Rundungen,
10 Summen); die frühere Messung an LibreOffice
(`scripts/measure_semantics.py`, `test/fixtures/libreoffice-semantik.json`)
bleibt zum Vergleich erhalten. Blatt 03 stimmt zusätzlich in 500
zufälligen vollständigen Belegungen mit dem Referenz-Rechenkern `engine.js`
des Ausgangsmaterials überein (lokaler Test, `AUDITCORE_SAMPLING_ENGINE03`).

## Offen vor einer Veröffentlichung

- Zustimmung des Dienstherrn zur Veröffentlichung der aus der Vorlage
  abgeleiteten Inhalte (§ 43 UrhG).
- Lizenz: Das Ausgangsmaterial sah EUPL-1.2 vor; das Repository verlangt MIT
  für alle Workspace-Pakete (`npm run license-check`, `tests/test_npm_publish.py`).
- Jedes Paket unter `packages-js/` wird vom Release-Werkzeug gepackt und
  veröffentlicht; bis zur Klärung darf dieser Stand nicht in ein Release gehen.
- Auslieferung vorab: Die Pakete werden als lokal gepackte Tarballs in eine
  private Anwendung eingebunden (ECOHESION im audit_designer), nicht über ein
  auditcore-Release.
