/**
 * Paritätsfälle der Benford-Analyse (Vue `BenfordPanel` ↔ React
 * `FlowauditBenford`). Port mit Antworten des echten Python-Backends,
 * synthetische Werte.
 */
import type { BenfordMetricsRequest, BenfordPort } from '../../src'
import { benfordAnalysisMetrics, fakeBenfordPort } from '../sampling/fake-port'
import type { ParityCase } from './cases'

export interface BenfordCaseProps {
  port?: BenfordPort | null
  values?: readonly (number | null)[]
  locale?: 'de' | 'en'
  metrics?: BenfordMetricsRequest | null
  autoAnalyse?: boolean
  hideInputs?: boolean
}

/** Einstellungen von flowinvoice: Chi²-Test bei α = 0,05, auffällige Ziffern mit |z| > 2,576 ohne Korrektur. */
export const flowinvoiceMetrics: BenfordMetricsRequest = {
  chi_square: { significance_level: 0.05 },
  digit_z: { continuity_correction: false, z_critical: 2.576 },
}

export const benfordCases: ReadonlyArray<ParityCase<BenfordCaseProps>> = [
  {
    name: 'übergebene Werte, erster Test vorgewählt',
    props: () => ({ port: fakeBenfordPort(), values: [123, 45.6, null, 0] }),
    expect: {
      texts: ['4 Werte übernommen', 'Quelle des Profils'],
      roles: [['combobox', 'Test'], ['combobox', 'Bewertungsprofil'], ['button', 'Analysieren']],
      counts: { 'fieldset': 0, '[data-testid="benford-chart"]': 0 },
    },
  },
  {
    name: 'ohne Werte',
    props: () => ({ port: fakeBenfordPort() }),
    expect: { texts: ['Keine Werte übergeben.'], counts: { 'input[type="file"]': 1 } },
  },
  {
    name: 'Fehler beim Laden',
    props: () => ({ port: fakeBenfordPort('profiles') }),
    expect: { texts: ['Anfrage abgelehnt: Dienst nicht erreichbar'], counts: { '[role="alert"]': 1, 'form': 0 } },
  },
  {
    name: 'englisch mit Rückfall auf Deutsch',
    props: () => ({ port: fakeBenfordPort(), values: [12, 34], locale: 'en' }),
    expect: { texts: ['2 Werte übernommen'], roles: [['button', 'Analyse'], ['combobox', 'Assessment profile']] },
  },
  {
    name: 'Kennzahlen vorgegeben, automatisch analysiert, Eingaben ausgeblendet',
    props: () => ({ port: fakeBenfordPort(undefined, undefined, benfordAnalysisMetrics), values: [123, 45.6], metrics: flowinvoiceMetrics, autoAnalyse: true, hideInputs: true }),
    expect: {
      texts: [
        'Chi²-Test', '8 FG, p < 0,0001', 'Kritische Werte: α = 0,1: 13,362 · α = 0,05: 15,507 · α = 0,01: 20,09',
        'Bei α = 0,05 verworfen (p < α)', 'Auffällige Ziffern', '|z| > 2,576, ohne Stetigkeitskorrektur',
      ],
      counts: { form: 0, 'input[type="file"]': 0, '[data-testid="benford-conspicuous"]': 1, '[data-testid="benford-significance"]': 1 },
    },
  },
  {
    name: 'Kennzahlen als Auswahl im Formular',
    props: () => ({ port: fakeBenfordPort(), values: [123, 45.6], metrics: flowinvoiceMetrics }),
    expect: {
      roles: [['checkbox', 'Chi²-Test mit kritischen Werten'], ['checkbox', 'Auffällige Ziffern (z je Ziffer)']],
      counts: { 'input[type="checkbox"]:checked': 2, '[data-testid="benford-significance"]': 0 },
    },
  },
]
