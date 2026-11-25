# Changelog @auditcore/ui-core

## Unveröffentlicht

- Neu: Bereich `redaction` für „PDF schwärzen“: Typen des Vertrags `pdf_redaction/1`, `createRedactionRestPort`, Zustandsautomat `createRedactionController` (Kriterien, Plan, Auswahl, Seitenbilder, eigene Bereiche, Zeigergesten, Ergebnis), Anzeige `redactionReview` und `redactionReportRows`, Texte `redactionMessages` (de/en), Stil `styles/redaction.css`, Fokusführung `focusRedactionHeading` und `focusRedactionAddArea`. Bereiche lassen sich mit der Maus verschieben (`startMove`, `moveRedactionBox`); während des Schwärzens ist die Auswahl gesperrt.

## 0.4.2 – 2026-11-24

- Hochrechnung: `residualRemarks(residual)` liefert die Begründung für
  „entfällt“ (`not_applicable`, Zeilen L und M) und die Hinweise (`notes`) der
  RER; neue Texte `rerNotApplicable` („Warum L und M entfallen“ / „Why rows L and
  M do not apply“) und `rerNotes` („Hinweise zur Restfehlerquote“ / „Notes on the
  residual error rate“). Typ `ResidualErrorRate` um `not_applicable_template` und
  `residual_negative` ergänzt.
- Hochrechnung: Der Controller merkt sich die Anfrage der RER
  (`lastResidualRequest`) und gibt sie beim Export als `residual` mit
  (`ExtrapolationExportRequest`), aber nur, wenn `library` des Katalogs
  `auditcore_extrapolation` ≥ 0.3.1 meldet (`extrapolationExportsResidual`);
  ältere Backends nähmen das Feld in den Fingerabdruck der Auswertung auf. Neue
  Hochrechnung und `applyInputs()` verwerfen RER und Anfrage wie bisher das
  Ergebnis. Antworten von `evaluate()` und `computeResidual()`, die erst nach
  einer späteren Hochrechnung oder neuen Eingaben eintreffen, und eine RER, die
  während einer laufenden Hochrechnung gestartet wurde, werden verworfen;
  bisher konnte eine verspätete RER-Antwort die alte RER samt Begründung unter
  die neue Hochrechnung und in den Export bringen. `ExtrapolationPort.exportEvaluation` nimmt `ExtrapolationExportRequest`
  an; Ports mit dem bisherigen Typ `EvaluationRequest` bleiben zuweisbar.
- Kennungen: Die Zusammenfassung der Stapelprüfung nennt Zeilen, die nur dem
  Format nach gültig sind, getrennt (`summaryFormat`, Feld
  `IdentifierBatchSummary.format_valid`). Tragen die Zeilen `verdict`
  (`auditcore_identifiers` ≥ 0.3.0), zählt `identifierBatchCounts()` aus den
  Zeilen; so stimmt die Summe auch gegen 0.3.0, das diese Zeilen zusätzlich
  unter `valid` zählt.
- Kennungen: `IdentifierResult` kennt `verdict`, `verdict_label`,
  `check_digit` und `check_digit_label`. Ergebnis „nur Format gültig“ (Text
  `statusFormatValid`, Farbe Warnung) statt „gültig“ in Tabelle, CSV und
  Einzelergebnis, Begründung `formatValidText`; „Nur Auffälligkeiten zeigen“
  behält diese Zeilen (bei den Legacy-Profilen ist jede gültige Zeile
  `format_valid`, der Filter blendet dort also nur noch nichts aus). Englische Texte für Status, Begründung und
  Zusammenfassung ergänzt.

## 0.4.1 – 2026-10-17

- Begriff: Die 2-%-Schwelle der Fehlerquote heißt in den Texten jetzt „Signifikanzschwelle“ statt „Wesentlichkeitsschwelle“ bzw. „Wesentlichkeit“, wie in der Delegierten Verordnung (EU) 2023/67, Anhang I Nr. 1, und in der VO (EU) 2021/1060, Anhang XX Nr. 5.9. Betroffen sind `extrapolationMessages` (`materiality`, `rerExceeds`, `rerWithin`) und `samplesizeMessages` (`materiality_rate`). Schlüssel, Felder und REST-Vertrag bleiben unverändert.

## 0.3.0 – 2026-09-29

Gemeinsamer Kontenformularvertrag, Controller, REST-Port, Styles und Bildlogik.
Noch nicht veröffentlicht.


## 0.4.0 – 2026-10-11

- Datenschutz-Assistent: Statuswerte der Ansicht „Status und Sperren“ erscheinen als ausgeschriebene Texte mit Umlauten (`axisValue_*`, `axisValueLabel(t, value)`); unbekannte Werte wie bisher mit Leerzeichen statt Unterstrichen.
- Neu: Datenschutz-Assistent im Kern `dataprotection`: `createAssistantController` (geführter oder freier Modus, Antworten mit Revision, Fehler je Frage, Prüfpunkte), `createAssistantRestPort` auf die Arbeitsbereichs-Endpunkte von `auditcore_dataprotection.web` 0.6.0, `assistantView`, `questionOptions`, `stepReachable`, Texte und Stil in `styles/dataprotection.css` (`docs/ui/dataprotection-paritaet.md`).
- Runner-Konsole: Klassen hinzufügen und umbenennen (`runnerKlasseHinzu`, `runnerKlasseUmbenennen`, Prüfung `RUNNER_KLASSEN_NAME`), Art `cpu`/`gpu` je Klasse (Grafikspeicher und Kartenauswahl nur bei `gpu`), `auth_art` im Status.
- Neu `runner` (Runner-Konsole der Prüfbank `auditcore_runner`): `createRunnerController` (Status, Profil-Entwurf mit Prüfen/Anwenden, Konflikt mit feldweisen Unterschieden, Werkzeug-Einstellungen, Prioritäten), `createRunnerRestPort` auf die JSON-API von `auditcore-runner ui` (Schreib-Kopfzeile, 409 → Konflikt), `createRunnerMemoryPort`, Ansichtsmodelle, Stil `styles/runner.css` (`docs/ui/runner.md`).
- Neu `attributes` (Merkmalsstichprobe, Discovery, Stop-or-go; `createAttributesController`, `createAttributesRestPort`).
- Hochrechnung: Teilstichproben mit eigenen Teilschichten und dritter Stufe (`model-subsample.ts`, `subsampleEditorView`, Aktionen `addSubStratum`, `updateSubStratum`, `removeSubStratum`, `toggleNestedSubsample`, `editNestedSubsample`), Programme bei mehreren Zeiträumen (`StratumRow.group`).
- Neu: Bestandsprüfung – Kern `batchchecks`: `createBatchchecksController`, `buildBatchchecksRequest`, `createBatchchecksRestPort`, Anzeige, Stil `batchchecks.css`; Vertrag `documents_batch_checks/1` (`docs/ui/batch-checks-rest.md`).
- Hochrechnung: Aufbau der Stichprobe (ein Zeitraum, mehrere Zeiträume, Gruppe von Programmen), Teilstichproben je Einheit, Systembewertung für die Neuberechnung des Konfidenzniveaus (Leitfaden 7.7); neue Funktionen in `model-design.ts`, `view-details.ts`, Controller-Aktionen `setDesign`, `setSystemAssessment`, `setPopulationUnits`, `toggleSubsample`, `editSubsample`, `updateSubsample`, `addSubItem`, `updateSubItem`, `removeSubItem`; Typen des erweiterten Vertrags `evaluation/1`.
- Neu `samplesize`: Kern des Planers für den Stichprobenumfang nach KOM-Leitfaden (`createSamplesizeController`, `createSamplesizeRestPort` auf `auditcore_sampling.guidance/1`, `createSamplesizeMemoryPort`, Texte, Formular, Anzeige), Stil `styles/samplesize.css`.
- Benford: Typen `BenfordMetricsRequest`, `ChiSquareMetric`, `DigitZMetric`;
  `activeMetrics`, `offeredMetrics`, `benfordChiTexts`, `benfordDigitZTexts`,
  `benfordMetricLabel`; Controller mit `metrics`/`autoAnalyse` in der Quelle,
  `valuesChanged()` und `setMetric()`. Fixture `benford-analysis-metrics.json`
  aus `auditcore_statistics.web`.

## 0.2.0 – 2026-09-26 – Release v0.4.2

- **Breaking:** Paketname `@auditcore/ui-core` statt `@flowaudit/ui-core` (npm-Scope einheitlich mit den Python-Paketen `auditcore_*`). Imports, `package.json`-Einträge und Tarball-Namen (`auditcore-ui-core-<version>.tgz`) anpassen; siehe `docs/ui/umbenennung-auditcore.md`. Web-Component-Tags und CSS-Präfixe unverändert.

Erste Veröffentlichung als Release-Datei. Ein früher Stand 0.1.0 (#149) war vor dem Release als Tarball in Anwendungen eingebunden (regulierung, audit_designer); seitdem kamen die unten genannten Kerne dazu (Risiko/Screening/Stichprobe/Benford, Vergleiche, Datenbank-Kanban, Belegerkennung, Kennungen, UTM, Tabellenexport, Hochrechnung). Deshalb 0.2.0 statt 0.1.0. Build mit Vite 8 (#169); Abhängigkeiten `@auditcore/common` 0.1.1, `@auditcore/kanban-core` 0.2.1.

## 0.1.0 – nicht als Release-Datei veröffentlicht

Erste Fassung, herausgelöst aus `@flowaudit/ui` 0.2.0.

- Hochrechnung: Vertrag `auditcore_extrapolation.evaluation/1`, REST-Port
  `createExtrapolationRestPort`, Formularlogik (`buildEvaluationRequest`,
  `buildResidualRequest`), Zustandsautomat `createExtrapolationController`,
  Anzeige (`terMetrics`, `residualMetrics`, Herleitung), Stile
  `styles/extrapolation.css`, Paritätsfälle `cases-extrapolation.ts`.
- Sprachkern (`defineMessages`, `translate`, `translator`, Standardsprache mit
  Beobachtern), Texte der Basiskomponenten, Synopse und Datenschutz.
- Synopse: Datentypen `auditcore_documents.web`, Wortvergleich, View-Model,
  Exporte (HTML, Markdown), REST-Client, Zustandsautomat
  `createSynopsisController` mit `selectSynopsis`, Tastennavigation.
- Datenschutz: Vertrag `dataprotection_ui/1`, REST-Port, `registerView`,
  `dsfaView`, Exporte, Zustandsautomaten `createVvtController` und
  `createDsfaController`.
- Geo-Karte: Vertrag `auditcore_geo.web`, Modell, REST-Port, Leaflet-Kartenansicht
  (`createLeafletView`, dynamisch geladen) und `createGeoController`/`selectGeo`.
- Fokusfalle `createFocusTrap` für Dialoge.
- Datenbankansicht als Kanban: Zustandsautomat `createDbKanbanController`
  (Laden, Gruppierung, Verschieben mit Rücknahme bei Fehlern, Tastatur,
  Anlegen) und `dbKanbanView`; Gruppierung und Port aus
  `@flowaudit/kanban-core` 0.2.0 (neue Laufzeitabhängigkeit). Stile
  `styles/dbkanban.css`.
- `createStore`, `createRunner`, `createDelay` als gemeinsame Grundlage der
  Controller; `downloadText`, `printHtml`, `deliverExport`.
- Stile (`style.css`): Designtoken, Basis, Tabelle, Synopse, Datenschutz, Geo
  (mit Leaflet-Grundstilen), Risiko-Merkmale, Screening, Datei-Import,
  Stichprobe, Benford, Dokumentvergleiche, Datenbankansicht.
- Risiko-Merkmale: Vertrag `auditcore_risk.web`, REST-Port, View-Logik
  (Zustand je Datensatz, Verteilung, Filter, Detaileinträge), Formate und
  Textschlüssel, Zustandsautomat `createRiskController` mit `selectRisk`
  (Filter, Datensatzauswahl, Nachladen der Profilbeschreibung mit Prüfung
  des Fingerabdrucks).
- Screening: Vertrag `screening_review/1`, REST-Port, View-Logik,
  Laufformular (`buildRunRequest`, `runFormDefaults`), Zustandsautomat
  `createScreeningController` mit `selectScreening`. Bisher interne Helfer
  der Vue-Komponenten heißen im Kern eindeutig: `formatScreeningDate`,
  `BreakdownTone`, `ScreeningDecisionForm`, `ScreeningRunFormState`.
- Stichprobe: Vertrag `auditcore_sampling.web`, REST-Port, Eingabeprüfung
  und Anfragen (`model`), Anzeigefunktionen (`view`), Zustandsautomat
  `createSamplingController`.
- Benford: Vertrag `auditcore_statistics.web`, REST-Port, Diagrammgeometrie
  (`chart`), Anzeigefunktionen, Zustandsautomat `createBenfordController`.
- Datei-Import (`tabular`): `createTableImportController`, `importPreview`,
  `tabularMessages` – gemeinsam für Stichprobe und Benford. Allgemeine Namen
  der drei Gruppen tragen im Kern ein Präfix (`sampling…`, `benford…`,
  `import…`), damit sie im Haupteinstieg nicht kollidieren.
- Dokumentvergleiche: Formularmodell mit Prüfung wie `POST /comparisons`
  (`formProblems`, `toCompareFields`), Liste (`summaryView`,
  `filterSummaries`), Import (`parseImport`), Zustandsautomat
  `createComparisonsController` mit `comparisonsView`; REST-Client um
  `importResult` (`POST /comparisons/import`) ergänzt. Stile
  `styles/documents.css`, Fixture aus dem echten Dienst
  (`test/fixtures/documents-comparisons.json`).
- Stile (`style.css`): Designtoken, Basis, Tabelle, Synopse, Datenschutz, Geo (mit Leaflet-Grundstilen), Kanban (`kanban.css`, aus `@flowaudit/ui` verschoben).
- Kanban-Texte `kanbanMessages`, `kanbanDialogMessages` (aus `@flowaudit/ui`
  verschoben).
