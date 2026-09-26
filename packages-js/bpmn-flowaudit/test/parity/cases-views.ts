/**
 * Shared parity cases of the editor side views (issue list, key filter): Vue
 * (`@auditcore/bpmn-vue`) and React (`@auditcore/bpmn-react`) are rendered
 * with the same inputs and checked against the same expectations and against
 * each other (DOM). Synthetic data only.
 */
import { issue } from '../../src'
import type { DialogCase } from './cases-dialogs'

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
