/**
 * Shared parity cases of the panel components: the Vue version
 * (`@auditcore/bpmn-vue`) and the React version (`@auditcore/bpmn-react`)
 * render with the same inputs and are checked against the same
 * expectations and against each other (DOM). Synthetic data only.
 */
import type { LegalBasis, Marker } from '../../src'
import { LISTS, type FieldDescriptor, type Option } from '../../src/ui'
import type { Expectation, ParityCase } from './expectation'

export type { Expectation, ParityCase }

const FIELDS: FieldDescriptor[] = [
  { key: 'label', label: 'field.label', kind: 'text' },
  { key: 'keyControl', label: 'field.keyControl', kind: 'checkbox' },
  { key: 'controls', label: 'field.controls', kind: 'tokens', wide: true },
  { key: 'frequency', label: 'field.frequency', kind: 'select' },
  { key: 'description', label: 'field.description', kind: 'textarea', placeholder: 'Beschreibung' },
  { key: 'deadline', label: 'field.deadline', kind: 'date' },
]

const options = (): Option[] => [{ value: 'monatlich', label: 'monatlich' }]

export interface FieldFormCase {
  value: Record<string, unknown>
  fields: FieldDescriptor[]
  optionsFor: (field: FieldDescriptor) => Option[]
  disabled?: boolean
}

export const FIELD_FORM_CASES: ParityCase<FieldFormCase>[] = [
  { name: 'alle Feldarten', props: () => ({ value: { label: 'Sichtprüfung', keyControl: true, controls: ['K1', 'K2'], frequency: 'monatlich', description: 'Vier-Augen-Prinzip' }, fields: FIELDS, optionsFor: options }), expect: { counts: { select: 1, textarea: 1, 'input[type="checkbox"]': 1 } } },
  { name: 'unbekannter Auswahlwert, gesperrt', props: () => ({ value: { frequency: 'alle 7 Jahre' }, fields: FIELDS, optionsFor: () => [], disabled: true }), expect: { texts: ['alle 7 Jahre'], counts: { 'input:disabled': 4 } } },
]

export interface ListEditorCase {
  descriptor: (typeof LISTS)[keyof typeof LISTS]
  items: Record<string, unknown>[]
  optionsFor: (field: FieldDescriptor) => Option[]
  disabled?: boolean
}

export const LIST_EDITOR_CASES: ParityCase<ListEditorCase>[] = [
  { name: 'Kontrollen mit Schlüsselkontrolle', props: () => ({ descriptor: LISTS.controls, items: [{ id: 'K1', label: 'Sichtprüfung', keyControl: true }, { id: 'K2' }], optionsFor: options }), expect: { texts: ['K1 · Sichtprüfung', 'Schlüsselkontrolle'], counts: { '.fa-card': 2 } } },
  { name: 'leere Liste', props: () => ({ descriptor: LISTS.findings, items: [], optionsFor: options }), expect: { texts: ['Keine Einträge.'], roles: [['button', /Hinzufügen/]] } },
]

export interface LegalCase {
  items: LegalBasis[]
  disabled?: boolean
}

export const LEGAL_CASES: ParityCase<LegalCase>[] = [
  { name: 'strukturiert', props: () => ({ items: [{ act: 'Verordnung (EU) 2021/1060', article: '74', paragraph: '1' }] }), expect: { texts: ['Art. 74'], counts: { '.fa-card': 1 } } },
  { name: 'Altbestand', props: () => ({ items: [{ text: 'Art. 74 VO (EU) 2021/1060; interne Weisung' }] }), expect: { texts: ['Altbestand'] } },
  { name: 'leer, gesperrt', props: () => ({ items: [], disabled: true }), expect: { counts: { 'input:disabled': 1 } } },
]

export interface MarkerCase {
  markers: Marker[]
  disabled?: boolean
}

export const MARKER_CASES: ParityCase<MarkerCase>[] = [
  { name: 'ohne Kennzeichen', props: () => ({ markers: [] }), expect: { counts: { '.fa-chip[aria-pressed="true"]': 0 } } },
  { name: 'mit Text', props: () => ({ markers: [{ type: 'feststellung', text: 'F-01' }, { type: 'pruefpunkt' }] }), expect: { counts: { '.fa-chip[aria-pressed="true"]': 2, 'input.fa-input': 2 } } },
]
