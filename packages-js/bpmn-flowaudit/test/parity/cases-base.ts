/**
 * Shared parity cases of the base components (icon, dialog): Vue
 * (`@flowaudit/bpmn-vue`) and React (`@flowaudit/bpmn-react`) are rendered
 * with the same inputs and checked against the same expectations and against
 * each other (DOM). Synthetic data only.
 */
import type { ParityCase } from './expectation'

export interface IconCaseProps {
  name: string
  size?: number
  label?: string
}

export const ICON_CASES: ReadonlyArray<ParityCase<IconCaseProps>> = [
  { name: 'Symbol dekorativ', props: () => ({ name: 'close' }), expect: { counts: { 'svg[aria-hidden="true"]': 1, '[role="img"]': 0 } } },
  { name: 'Symbol mit Beschriftung und Größe', props: () => ({ name: 'search', size: 24, label: 'Suchen' }), expect: { roles: [['img', 'Suchen']], counts: { 'svg[width="24"]': 1 } } },
]

export interface DialogBaseProps {
  open: boolean
  title: string
  subtitle?: string
  width?: string
}

export const DIALOG_BASE_CASES: ReadonlyArray<ParityCase<DialogBaseProps>> = [
  {
    name: 'Dialog offen mit Untertitel',
    props: () => ({ open: true, title: 'Prüfpfad', subtitle: 'Synthetisches Verfahren', width: '480px' }),
    expect: { texts: ['Synthetisches Verfahren'], roles: [['dialog', 'Prüfpfad'], ['button', 'Schließen']] },
  },
]
