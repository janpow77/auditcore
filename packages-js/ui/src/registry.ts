import type { ElementDefinition } from './elements/define'
import { benfordElement } from './benford/element'
import { samplingElement } from './sampling/element'
import { tableElement } from './table/element'

/**
 * Alle Web Components von @flowaudit/ui. Neue Komponenten tragen hier ihre
 * `ElementDefinition` ein (siehe docs/ui/beitragen.md).
 */
export const ELEMENTS: readonly ElementDefinition[] = [tableElement, samplingElement, benfordElement]
