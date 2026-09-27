/**
 * Paritätsfälle der Berichtsvorlagen (Vue `ReportTemplates` ↔ React
 * `FlowauditReportTemplates`). Port mit Antworten des echten Python-Backends
 * (auditcore_reporting.web, neutrale mitgelieferte Vorlagen), synthetische Daten.
 */
import type { ReporttemplatesPort, TemplateData } from '../../src'
import { fakeTemplatesPort } from '../reporttemplates/fake-port'
import type { ParityCase } from './cases'

export interface ReporttemplatesCaseProps {
  port?: ReporttemplatesPort | null
  data?: TemplateData | null
  filename?: string
  locale?: 'de' | 'en'
}

export const reporttemplatesCases: ReadonlyArray<ParityCase<ReporttemplatesCaseProps>> = [
  {
    name: 'Vorlagen geladen, erste Vorlage mit Datenvertrag',
    props: () => ({ port: fakeTemplatesPort(), filename: 'Prüfbericht' }),
    expect: {
      texts: ['Version 1.0.0 · Freigegeben', 'Beispieldaten der Vorlage', 'Datenvertrag', 'Pflichtbaustein', 'Art. 74 VO (EU) 2021/1060'],
      roles: [['combobox', 'Vorlage'], ['combobox', 'Format'], ['combobox', 'Gestaltung'], ['textbox', 'Dateiname'], ['button', 'Vorschau'], ['button', 'Bericht erzeugen']],
      counts: { '[role="alert"]': 0, 'option': 7, '[data-testid="template-preview"]': 0 },
    },
  },
  {
    name: 'Daten der Anwendung übergeben',
    props: () => ({ port: fakeTemplatesPort(), data: { aktenzeichen: 'AZ-1' } }),
    expect: { texts: ['Daten: Daten der Anwendung'] },
  },
  {
    name: 'keine Vorlagen',
    props: () => ({ port: fakeTemplatesPort({ empty: true }) }),
    expect: { texts: ['Keine Vorlagen vorhanden.'], counts: { form: 0 } },
  },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeTemplatesPort({ failing: 'templates' }) }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, form: 0 } },
  },
  { name: 'ohne Port', props: () => ({}), expect: { texts: ['Kein Port übergeben'], counts: { form: 0 } } },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeTemplatesPort(), locale: 'en' }),
    expect: { roles: [['button', 'Preview'], ['combobox', 'Template']], texts: ['Datenvertrag'] },
  },
]
