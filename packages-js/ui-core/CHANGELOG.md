# Changelog @flowaudit/ui-core

## 0.1.0 – unveröffentlicht

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
- `createStore`, `createRunner`, `createDelay` als gemeinsame Grundlage der
  Controller; `downloadText`, `printHtml`, `deliverExport`.
- Stile (`style.css`): Designtoken, Basis, Tabelle, Synopse, Datenschutz, Geo
  (mit Leaflet-Grundstilen), Risiko-Merkmale, Screening, Datei-Import,
  Stichprobe, Benford, Dokumentvergleiche.
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
