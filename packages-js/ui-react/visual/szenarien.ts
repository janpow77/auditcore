/**
 * Szenarien der Bildparität: dieselben Fälle wie die DOM-Parität
 * (ui-core/test/parity/cases-base.ts), gerendert von Vue und React.
 */
import { buttonCases, textFieldCases } from '../../ui-core/test/parity/cases-base'

export interface Szenario {
  id: string
  art: 'schaltflaeche' | 'eingabefeld'
  index: number
}

export const szenarien: Szenario[] = [
  ...buttonCases.map((_, index) => ({ id: `schaltflaeche-${index}`, art: 'schaltflaeche' as const, index })),
  ...textFieldCases.map((_, index) => ({ id: `eingabefeld-${index}`, art: 'eingabefeld' as const, index })),
]
