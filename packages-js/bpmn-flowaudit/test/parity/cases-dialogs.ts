/**
 * Shared parity cases of the editor dialogs and side views: the Vue version
 * (`@auditcore/bpmn-vue`) and the React version (`@auditcore/bpmn-react`) are
 * rendered with the same inputs and checked against the same expectations
 * and against each other (DOM). Synthetic data only.
 */
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { issue, loadDefinitions, modelFromDefinitions, type DiagramInfo, type ExportData, type ProcessModel, type Suggestion } from '../../src'
import type { Expectation } from './expectation'

export interface DialogCase<P> {
  name: string
  props: () => P
  expect: Expectation
  /** Selector and value of a text input to type into (same interaction on both sides). */
  type?: { selector: string; value: string }
  /** Selector of an element to click (index among the matches). */
  click?: { selector: string; index?: number }
  /** Expectation after the interaction. */
  after?: Expectation
}

const exportData: ExportData = { colors: [{ fill: '#fff', stroke: '#000', label: 'Standard', meaning: 'Standard', count: 1 }], markers: [], legalBases: [] }

export const EXPORT_CASE: DialogCase<Record<string, unknown>> = {
  name: 'Exportdialog mit Vertraulichkeit und Excel',
  props: () => ({ open: true, defaultTitle: 'Bewilligung', subtitle: 'Verfahren', data: exportData, confidentiality: 'vs_nfd', excel: true }),
  expect: { roles: [['dialog', 'Exportieren'], ['button', /PDF/]], counts: { '.fa-export__formats button': 10, 'input[type="checkbox"]': 6 } },
  click: { selector: 'input[type="checkbox"]', index: 0 },
}

export const SUGGESTIONS: Suggestion[] = [
  { id: 's1', elementId: 'T1', kind: 'legalBasis', value: { act: 'Verordnung (EU) 2021/1060', article: '74' }, excerpt: 'Art. 74 CPR', origin: 'documentation' },
  { id: 's2', elementId: 'T1', kind: 'rolePrefix', value: 'ZGS', excerpt: 'ZGS: Antrag prüfen', origin: 'name' },
  { id: 's3', elementId: 'T2', kind: 'rolePrefix', value: 'VB', excerpt: 'VB: Zahlung anweisen', origin: 'name' },
]

export const ENRICHMENT_CASE: DialogCase<Record<string, unknown>> = {
  name: 'Anreicherung: Vorschläge je Element, einer abgewählt',
  props: () => ({ open: true, suggestions: SUGGESTIONS, names: { T1: 'Antrag prüfen' } }),
  expect: { texts: ['Antrag prüfen', 'T2', '3 Vorschläge übernehmen'], roles: [['dialog', 'Altbestand anreichern']], counts: { '.fa-enrich__item': 3 } },
  click: { selector: '.fa-enrich__item input' },
  after: { texts: ['2 Vorschläge übernehmen'] },
}

export const XML_CASE: DialogCase<Record<string, unknown>> = {
  name: 'XML-Ansicht bearbeiten',
  props: () => ({ open: true, xml: '<a/>' }),
  expect: { roles: [['dialog', 'XML-Ansicht'], ['textbox', 'XML-Ansicht']] },
  type: { selector: 'textarea', value: '<b/>' },
}

export const SHORTCUT_CASE: DialogCase<Record<string, unknown>> = {
  name: 'Tastenkürzel-Hilfe',
  props: () => ({ open: true }),
  expect: { texts: ['Speichern'], roles: [['dialog', 'Tastenkürzel']], counts: { tr: 17, kbd: 36 } },
}

export const SEARCH_CASE: DialogCase<Record<string, unknown>> = {
  name: 'Elementsuche mit Treffern',
  props: () => ({ open: true, model: null }),
  expect: { roles: [['dialog', 'Element suchen'], ['searchbox', 'Element suchen']] },
  type: { selector: 'input', value: 'Antrag' },
}

export const ISSUES = [issue('BPMN-S010', 'Process_1', { name: 'Antrag' }), issue('BPMN-F001', 'Task_1', { name: 'Prüfen' })]

export const ISSUE_CASE: DialogCase<Record<string, unknown>> = {
  name: 'Hinweisliste nach Schwere gefiltert',
  props: () => ({ issues: ISSUES, error: 'Server nicht erreichbar' }),
  expect: { texts: ['Server nicht erreichbar', 'BPMN-S010'], roles: [['region', 'Hinweise']], counts: { '.fa-issue': 2, '.fa-chip': 4 } },
  click: { selector: '.fa-chip', index: 1 },
  after: { counts: { '.fa-issue': 1 } },
}

export const KEY_FILTER_CASE: DialogCase<Record<string, unknown>> = {
  name: 'Schlüsselfilter mit Treffern',
  props: () => ({ keys: { ka: { '10': ['T1'], '2': ['T2'] }, bk: { '2.3': ['T1'] } }, kind: 'ka', value: '', hits: 2 }),
  expect: { texts: ['2 Treffer'], roles: [['search', 'Schlüsselfilter']], counts: { 'datalist option': 2 } },
  type: { selector: 'input', value: '10' },
}

export const INFO: DiagramInfo = { title: 'Bewilligung', subtitle: 'Zuwendungsverfahren', status: 'entwurf', version: '1.0', funds: ['efre'] }

export const INFO_CASE: DialogCase<Record<string, unknown>> = {
  name: 'Diagramm-Infos mit Freigabe',
  props: () => ({ open: true, info: INFO, profiles: [{ id: 'p', version: '1', title: 'Profil' }], approvals: [{ version: '1.0', sha256: 'a'.repeat(64) }], fallbackTitle: 'Datei' }),
  expect: { texts: ['Bewilligung', 'a'.repeat(64)], roles: [['dialog', 'Diagramm-Infos']], counts: { '.fa-info-section': 6, '.fa-chip[aria-pressed="true"]': 1 } },
  click: { selector: '.fa-chip[aria-pressed="true"]' },
  after: { counts: { '.fa-chip[aria-pressed="true"]': 0 } },
}

/** Process model of the synthetic 1.1 fixture (for the element search). */
export async function fixtureModel(): Promise<ProcessModel> {
  const xml = readFileSync(join(__dirname, '../fixtures/schema-1.1.bpmn'), 'utf-8')
  return modelFromDefinitions((await loadDefinitions(xml)).definitions)
}
