# Changelog @flowaudit/ui-core

## 0.1.0 – unveröffentlicht

Erste Fassung, herausgelöst aus `@flowaudit/ui` 0.2.0.

- Sprachkern (`defineMessages`, `translate`, `translator`, Standardsprache mit
  Beobachtern), Texte der Basiskomponenten, Synopse und Datenschutz.
- Synopse: Datentypen `auditcore_documents.web`, Wortvergleich, View-Model,
  Exporte (HTML, Markdown), REST-Client, Zustandsautomat
  `createSynopsisController` mit `selectSynopsis`, Tastennavigation.
- Datenschutz: Vertrag `dataprotection_ui/1`, REST-Port, `registerView`,
  `dsfaView`, Exporte, Zustandsautomaten `createVvtController` und
  `createDsfaController`.
- Dokumentvergleiche: Formularmodell mit Prüfung wie `POST /comparisons`
  (`formProblems`, `toCompareFields`), Liste (`summaryView`,
  `filterSummaries`), Import (`parseImport`), Zustandsautomat
  `createComparisonsController` mit `comparisonsView`; REST-Client um
  `importResult` (`POST /comparisons/import`) ergänzt. Stile
  `styles/documents.css`, Fixture aus dem echten Dienst
  (`test/fixtures/documents-comparisons.json`).
- `createStore`, `createRunner`, `createDelay` als gemeinsame Grundlage der
  Controller; `downloadText`, `printHtml`, `deliverExport`.
- Stile (`style.css`): Designtoken, Basis, Tabelle, Synopse, Dokumentvergleiche, Datenschutz.
