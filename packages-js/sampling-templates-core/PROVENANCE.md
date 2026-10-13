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

| Inhalt | Ort | Umfang in 0.1.0 |
|---|---|---|
| Rechenwege (Formeln als TypeScript, Zelle für Zelle) | `src/sheets/<Blatt>/compute.ts`, `src/sheets/shared/statistical.ts` | Blätter 02, 03, 04, 17 |
| Bezeichnungen (Spalte B), Fundstellen (Spalte D bzw. K), Abschnittstitel, Zahlenformate, Vorgaben | `src/sheets/<Blatt>/definition.ts` | Blätter 02, 03, 04, 17, wörtlich; Bezeichnungen mit Formel in Bezeichnung und Kurzformel getrennt |
| Prüfhinweistexte (✔/⚠/✖), wortgleich | `src/sheets/<Blatt>/compute.ts`, `src/sheets/shared/statistical.ts` | Blätter 02, 03, 04, 17 |
| Englische Arbeitsübersetzung dieser Texte (eigene Übersetzung, als solche gekennzeichnet) | `src/sheets/<Blatt>/texts.en.ts`, `src/catalog/texts.en.ts` | Blätter 01–03, Katalog |
| z-Werte und Auswahllisten aus Blatt 01 | `src/sheets/01_Parameter/index.ts` | vollständig (z-Werte aus Anhang I DelVO) |
| Blattnamen, Inhaltsangaben, Rechtsgrundlagen und Bezug zur Vorlage 2017 aus Blatt 00; Hinweis zu drei Zeiträumen geschichtet | `src/catalog/catalog.ts`, `src/sheets/registry.ts` | alle 23 Blätter |
| Erwartete Werte der Formelzellen (Zahlen, Prüfhinweistexte) | `test/golden/*.golden.json` | 262 Fälle, 11.313 Zellen (Blätter 02, 03, 04, 17) |
| Statistik der verwendeten Excel-Funktionen | `docs/excel-funktionen.md` | Anzahl je Funktion |

Nicht enthalten: die Arbeitsmappe selbst, der Wortlaut der Formeln, Hinweis-
und Erläuterungstexte anderer Blätter, das Layout.

Beispielwerte (`sample`) und alle Testfälle sind erfunden und stammen aus
keiner Prüfung.

## Charakterisierung

`scripts/golden_recalc.py` schreibt die Eingaben jedes Falls in eine Kopie der
Vorlage, rechnet sie mit LibreOffice (hier 24.2.7.2) ohne Oberfläche neu und
liest die Formelzellen aus. `test/golden.spec.ts` vergleicht jede Zelle
(Zellen mit Ganzzahlformat exakt, übrige relative Toleranz 1e-9, Texte
wortgleich); Ergebnis in `docs/abgleich.md`. Eine Abweichung ist nur
zugelassen, wenn die Webfassung keinen Wert zeigt, die Abweichung als Datum
erklärt ist, eine der genannten Eingaben leer ist und die Gegenprobe mit 0
den Wert der Vorlage ergibt.

158 der 198 Fälle des Blatts 03 stammen aus einer unabhängigen Prüfung des
Fundaments (`test/cases/03_MUS_1Z.pruefer.json`). Vergleiche und Aufrunden
sind an LibreOffice gemessen (`scripts/measure_semantics.py`,
`test/fixtures/libreoffice-semantik.json`: 451 Vergleiche, 81 Rundungen);
Microsoft Excel ist nicht gegengeprüft. Blatt 03 stimmt zusätzlich in 500
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
