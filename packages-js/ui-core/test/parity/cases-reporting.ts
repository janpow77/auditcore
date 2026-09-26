/**
 * Paritätsfälle des Tabellenexports (Vue `ReportExportPanel` ↔ React
 * `FlowauditReportExport`). Port mit Antworten des echten Python-Backends
 * (auditcore_reporting.web), synthetische Vorhaben.
 */
import type { ReportingPort, ReportTableInput } from '../../src'
import { fakeReportingPort, reportingTables } from '../reporting/fake-port'
import type { ParityCase } from './cases'

export interface ReportingCaseProps {
  port?: ReportingPort | null
  tables?: readonly ReportTableInput[]
  filename?: string
  locale?: 'de' | 'en'
}

export const reportingCases: ReadonlyArray<ParityCase<ReportingCaseProps>> = [
  {
    name: 'Tabellen übergeben, erstes Profil vorgewählt',
    props: () => ({ port: fakeReportingPort(), tables: reportingTables, filename: 'Vorhabenliste' }),
    expect: {
      texts: ['1 Tabelle(n), 3 Zeilen', 'Herkunft des Profils'],
      roles: [['combobox', 'Formatprofil'], ['textbox', 'Dateiname'], ['button', 'Vorschau'], ['button', 'Als Excel exportieren']],
      counts: { '[data-testid="report-sheet-0"]': 0, '[role="alert"]': 0 },
    },
  },
  {
    name: 'ohne Tabellen',
    props: () => ({ port: fakeReportingPort() }),
    expect: { texts: ['Keine Tabellen übergeben.'] },
  },
  {
    name: 'Server ohne Excel-Extra',
    props: () => ({ port: fakeReportingPort(undefined, { excel: false }), tables: reportingTables }),
    expect: { texts: ['Extra „excel“ fehlt'], counts: { 'button[disabled]': 1 } },
  },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeReportingPort('profiles'), tables: reportingTables }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, form: 0 } },
  },
  { name: 'ohne Port', props: () => ({ tables: reportingTables }), expect: { texts: ['Kein Port übergeben'], counts: { form: 0 } } },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeReportingPort(), tables: reportingTables, locale: 'en' }),
    expect: { roles: [['button', 'Preview'], ['combobox', 'Format profile']], texts: ['1 Tabelle(n), 3 Zeilen'] },
  },
]
