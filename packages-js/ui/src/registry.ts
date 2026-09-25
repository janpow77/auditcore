import type { ElementDefinition } from './elements/define'
import { tableElement } from './table/element'

/**
 * Alle Web Components von @flowaudit/ui. Neue Komponenten tragen hier ihre
 * `ElementDefinition` ein (siehe docs/ui/beitragen.md).
 */
export const ELEMENTS: readonly ElementDefinition[] = [tableElement]
