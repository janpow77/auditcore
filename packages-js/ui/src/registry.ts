import type { ElementDefinition } from './elements/define'
import { kanbanBoardElement, kanbanBoardListElement } from './kanban/element'
import { synopsisElement } from './synopsis/element'
import { tableElement } from './table/element'

/**
 * Alle Web Components von @flowaudit/ui. Neue Komponenten tragen hier ihre
 * `ElementDefinition` ein (siehe docs/ui/beitragen.md).
 */
export const ELEMENTS: readonly ElementDefinition[] = [tableElement, kanbanBoardElement, kanbanBoardListElement, synopsisElement]
