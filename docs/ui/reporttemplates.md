# Berichtsvorlagen (`ReportTemplates` ↔ `FlowauditReportTemplates`)

Gerüst erzeugt mit `npm run ui:neu -- reporttemplates ReportTemplates`, danach
fachlich ausgebaut. Oberfläche zu den Vorlagen-Endpunkten des REST-Vertrags
`reporting_ui/1` ([reporting-rest.md](reporting-rest.md#berichtsvorlagen)).

| Schicht | Datei |
|---|---|
| Kern | `packages-js/ui-core/src/reporttemplates/` (`createReporttemplatesController`, `createReportTemplatesRestPort`, `reporttemplatesMessages`, Anzeige `schemaFields`, `textBlockRows`, `formatOptions`) |
| Stil | `packages-js/ui-core/styles/reporttemplates.css` |
| Vue / Web Component | `ReportTemplates` / `<flowaudit-report-templates>` (`packages-js/ui/src/reporttemplates/`) |
| React | `FlowauditReportTemplates` (`packages-js/ui-react/src/reporttemplates/`) |
| Paritätsfälle | `packages-js/ui-core/test/parity/cases-reporttemplates.ts` (6 Fälle, Antworten des echten Python-Backends als Fixtures) und 2 Interaktionsfolgen in `ui-react/test/parity/reporttemplates.spec.tsx` |
| Demo und Browsertest | `packages-js/ui/demo/pages/reporttemplates/ReportTemplatesPage.vue`, `packages-js/ui/e2e/reporttemplates.api-e2e.ts` (mit `demo/api_server.py`) |

## Ablauf

1. Vorlagen laden (`GET /templates`); die erste Vorlage und die erste
   Gestaltung sind sichtbar vorgewählt, ihr Datenvertrag wird geladen
   (`GET /templates/{id}`).
2. Datenvertrag (Felder der obersten Ebene mit Typ und Pflicht) und
   Textbausteine (Pflichtbaustein, bedingt, Rechtsgrundlage) aufklappbar.
3. **Vorschau** (`POST /templates/{id}/preview`): Prüfung der Daten gegen den
   Datenvertrag mit allen Fundstellen oder die HTML-Fassung im iframe mit
   `sandbox=""` (keine Skripte, kein Zugriff auf die Anwendung) sowie die
   verwendeten Textbausteine.
4. **Bericht erzeugen** (`POST /templates/{id}/render`) als DOCX, PDF oder
   HTML; Formate ohne Extra auf dem Server sind gesperrt und werden gemeldet.

## Vertrag

```ts
import { ReportTemplates, createReportTemplatesRestPort } from '@auditcore/ui'   // Vue
import { FlowauditReportTemplates } from '@auditcore/ui-react'                   // React
const port = createReportTemplatesRestPort({ baseUrl: '/api/reporting' })
```

Eigenschaften: `port`, `data` (Daten gemäß Datenvertrag; ohne Daten gelten die
Beispieldaten der Vorlage, sichtbar gekennzeichnet), `filename` (ohne Endung),
`locale`. Ereignisse: `template-select` (`TemplateDetail`),
`preview-completed` (`TemplatePreview`), `report-rendered` (`DownloadFile`),
`error` – React `onTemplateSelect`, `onPreviewCompleted`, `onReportRendered`,
`onError`. Der Bericht wird im Browser angeboten (`saveFile`). Ändern sich
Gestaltung oder Daten nach einer Vorschau, wird sie als veraltet markiert; ein
Wechsel der Vorlage verwirft sie.
