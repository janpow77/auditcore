# Stichprobenumfang nach Leitfaden (`SampleSizePlanner` ↔ `FlowauditSampleSizePlanner`)

Planung des Stichprobenumfangs nach dem KOM-Leitfaden EGESIF_16-0014-01
(Backend `auditcore_sampling.guidance`, Status „nach Leitfaden“). Gerüst mit
`npm run ui:neu -- samplesize SampleSizePlanner`; gerechnet wird ausschließlich
im Backend, die Oberfläche erfasst Eingaben und zeigt Umfang, Aufteilung,
Herleitung mit Fundstellen und Hinweise.

| Schicht | Datei |
|---|---|
| Kern | `packages-js/ui-core/src/samplesize/` (`createSamplesizeController`, `samplesizeMessages`, `createSamplesizeRestPort`, `createSamplesizeMemoryPort`, Formular `model.ts`, Anzeige `view.ts`) |
| Stil | `packages-js/ui-core/styles/samplesize.css` |
| Vue / Web Component | `SampleSizePlanner` / `<flowaudit-sample-size-planner>` (`packages-js/ui/src/samplesize/`) |
| React | `FlowauditSampleSizePlanner` (`packages-js/ui-react/src/samplesize/`) |
| Paritätsfälle | `packages-js/ui-core/test/parity/cases-samplesize.ts` (Antworten des echten Backends: `packages/auditcore_sampling/tools/ui_fixtures.py`) |

## Vertrag

Eigenschaften: `port` (z. B. `createSamplesizeRestPort({ baseUrl: '/api/sampling' })`),
`request` (Vorbelegung mit einer Anfrage des REST-Vertrags), `locale`.
Ereignisse: `plan-calculated` (React `onPlanCalculated`, Nutzdaten: Antwort
von `POST /guidance/size`), `error` (React `onError`).

Anteile (erwartete Fehlerquote, Wesentlichkeit) werden in Prozent mit
deutschem Dezimalkomma erfasst und als Anteil gesendet; vorbelegt ist nur die
Wesentlichkeit von 2 %. Faktorprofil, Konfidenzniveau und alle Pflichtangaben
wählt die Prüferin oder der Prüfer ausdrücklich; fehlende oder ungültige
Angaben werden am Feld gemeldet, ohne das Backend zu fragen.

REST: [samplesize-rest.md](samplesize-rest.md).

## Offen

- Demo-Seite (`packages-js/ui/demo/pages/samplesize/`) und Browser-Test mit Python-Backend (`e2e/samplesize.api-e2e.ts`).
