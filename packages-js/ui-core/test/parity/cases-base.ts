/** Gemeinsame Paritätsfälle der Basiskomponenten (Vue ↔ React). */
import type { ParityCase } from './cases'

export interface ButtonCaseProps {
  label?: string
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md'
  icon?: 'plus' | 'close' | 'lock'
  iconOnly?: boolean
  disabled?: boolean
  loading?: boolean
  pressed?: boolean
}

export const buttonCases: ReadonlyArray<ParityCase<ButtonCaseProps>> = [
  { name: 'Standard', props: () => ({ label: 'Speichern' }), expect: { roles: [['button', 'Speichern']] } },
  { name: 'primär, klein, mit Symbol', props: () => ({ label: 'Neu', variant: 'primary', size: 'sm', icon: 'plus' }), expect: { counts: { svg: 1 } } },
  { name: 'nur Symbol', props: () => ({ label: 'Schließen', icon: 'close', iconOnly: true }), expect: { roles: [['button', 'Schließen']], counts: { '.fa-button__label': 0 } } },
  { name: 'lädt und gedrückt', props: () => ({ label: 'Freigeben', loading: true, pressed: true }), expect: { counts: { '[aria-busy="true"][disabled]': 1 } } },
]

export interface TextFieldCaseProps {
  label: string
  modelValue?: string
  hint?: string
  error?: string
  hideLabel?: boolean
  required?: boolean
  type?: 'text' | 'search'
}

export const textFieldCases: ReadonlyArray<ParityCase<TextFieldCaseProps>> = [
  { name: 'mit Hinweis', props: () => ({ label: 'Aktenzeichen', modelValue: 'AZ-1', hint: 'Format AZ-n' }), expect: { roles: [['textbox', 'Aktenzeichen']], texts: ['Format AZ-n'] } },
  { name: 'mit Fehler', props: () => ({ label: 'Betrag', error: 'Pflichtfeld', required: true }), expect: { roles: [['alert', '']], counts: { '[aria-invalid="true"]': 1 } } },
  { name: 'Suche ohne sichtbare Beschriftung', props: () => ({ label: 'Suchen', type: 'search', hideLabel: true }), expect: { roles: [['searchbox', 'Suchen']] } },
]

export interface DialogCaseProps {
  open: boolean
  title: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
  placement?: 'center' | 'side'
  locale?: 'de' | 'en'
}

export const dialogCases: ReadonlyArray<ParityCase<DialogCaseProps>> = [
  { name: 'zentriert mit Beschreibung', props: () => ({ open: true, title: 'Fassung freigeben', description: 'Vier-Augen-Prinzip' }), expect: { roles: [['dialog', 'Fassung freigeben'], ['button', 'Schließen']] } },
  { name: 'seitlich, englisch', props: () => ({ open: true, title: 'Details', placement: 'side', size: 'lg', locale: 'en' }), expect: { roles: [['button', 'Close']] } },
]
