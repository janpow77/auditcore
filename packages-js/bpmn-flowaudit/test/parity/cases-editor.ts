/**
 * Shared parity cases of the whole editor: the Vue `FlowauditEditor`
 * (@flowaudit/bpmn-vue) and the React `FlowauditEditor` (@flowaudit/bpmn-react)
 * load the same synthetic fixture, run the same steps (DOM events and the
 * `select` method) and are compared part by part (normalised DOM, form
 * state) and by their XML output.
 */
import type { Expectation } from './expectation'

export type EditorStep =
  | { kind: 'select'; id: string }
  | { kind: 'key'; target: string; key: string; ctrl?: boolean }
  | { kind: 'click'; target: string }
  | { kind: 'change'; target: string; value: string }

export interface EditorParityCase {
  name: string
  fixture: string
  props?: { readonly?: boolean; lockApproved?: boolean; locale?: 'de' | 'en'; name?: string }
  steps: EditorStep[]
  /** Parts compared between both versions (selectors inside the editor root). */
  parts: string[]
  expect: Expectation
}

const TASK = 'Task_Bewilligen'
const ROOT = '.fa-editor'

export const EDITOR_CASES: EditorParityCase[] = [
  {
    name: 'nach dem Import',
    fixture: 'schema-1.1.bpmn',
    steps: [],
    parts: ['.fa-toolbar', '.fa-palette', '.fa-statusbar', '.fa-side'],
    expect: { roles: [['toolbar', 'Werkzeugleiste'], ['button', 'Speichern']], counts: { '.fa-palette__item': 34 } },
  },
  {
    name: 'Aufgabe ausgewählt: Eigenschaften',
    fixture: 'schema-1.1.bpmn',
    steps: [{ kind: 'select', id: TASK }],
    parts: ['.fa-side'],
    expect: { roles: [['tab', 'Allgemein']], counts: { '.fa-props [role="tab"]': 10 } },
  },
  {
    name: 'Tabwechsel per Pfeiltaste und Ende',
    fixture: 'schema-1.1.bpmn',
    steps: [{ kind: 'select', id: TASK }, { kind: 'key', target: '#fa-tab-general', key: 'ArrowDown' }, { kind: 'key', target: '.fa-props [aria-selected="true"]', key: 'End' }],
    parts: ['.fa-side'],
    expect: { counts: { '.fa-props [aria-selected="true"]#fa-tab-color': 1 } },
  },
  {
    name: 'Tastenkürzelhilfe mit „?“',
    fixture: 'schema-1.1.bpmn',
    steps: [{ kind: 'key', target: ROOT, key: '?' }],
    parts: ['[role="dialog"]'],
    expect: { texts: ['Rückgängig'], roles: [['dialog', 'Tastenkürzel']] },
  },
  {
    name: 'Elementsuche mit Strg+F und Treffer',
    fixture: 'schema-1.1.bpmn',
    steps: [{ kind: 'key', target: ROOT, key: 'f', ctrl: true }, { kind: 'change', target: '[role="dialog"] input', value: 'bewillig' }],
    parts: ['[role="dialog"]'],
    expect: { counts: { '[role="dialog"] [role="option"]': 1 } },
  },
  {
    name: 'Hinweisliste über die Statusleiste',
    fixture: 'schema-1.1.bpmn',
    steps: [{ kind: 'click', target: '.fa-statusbar button' }],
    parts: ['.fa-side', '.fa-statusbar'],
    expect: { texts: ['BPMN-'] },
  },
  {
    name: 'Diagramm-Infos über die Werkzeugleiste',
    fixture: 'schema-1.1.bpmn',
    steps: [{ kind: 'click', target: '[aria-label="Diagramm-Infos"]' }],
    parts: ['[role="dialog"]'],
    expect: { roles: [['dialog', 'Diagramm-Infos']] },
  },
  {
    name: 'Exportdialog',
    fixture: 'schema-1.1.bpmn',
    steps: [{ kind: 'click', target: '[aria-label^="Exportieren"]' }],
    parts: ['[role="dialog"]'],
    expect: { texts: ['PDF', 'BPMN'] },
  },
  {
    name: 'Prüfmenü geöffnet',
    fixture: 'schema-1.1.bpmn',
    steps: [{ kind: 'click', target: '.fa-toolbar-menu > button[aria-label="Prüfen"]' }],
    parts: ['.fa-toolbar'],
    expect: { roles: [['menu', '']] },
  },
  {
    name: 'schreibgeschützt',
    fixture: 'schema-1.1.bpmn',
    props: { readonly: true },
    steps: [{ kind: 'select', id: TASK }],
    parts: ['.fa-toolbar', '.fa-side'],
    expect: { texts: ['schreibgeschützt'] },
  },
  {
    name: 'englische Oberfläche',
    fixture: 'enrichment.bpmn',
    props: { locale: 'en' },
    steps: [],
    parts: ['.fa-toolbar', '.fa-palette', '.fa-statusbar'],
    expect: { roles: [['button', 'Save']] },
  },
]
