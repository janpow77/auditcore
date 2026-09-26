import type { ElementDefinition } from './elements/define'
import { benfordElement } from './benford/element'
import { dsfaElement, vvtElement } from './dataprotection/element'
import { comparisonsElement } from './documents/element'
import { geoMapElement } from './geo/element'
import { samplingElement } from './sampling/element'
import { kanbanBoardElement, kanbanBoardListElement } from './kanban/element'
import { dbKanbanElement } from './dbkanban/element'
import { riskFlagsElement } from './risk/element'
import { screeningReviewElement } from './screening/element'
import { synopsisElement } from './synopsis/element'
import { tableElement } from './table/element'

/**
 * Alle Web Components von @flowaudit/ui. Neue Komponenten tragen hier ihre
 * `ElementDefinition` ein (siehe docs/ui/beitragen.md).
 */
export const ELEMENTS: readonly ElementDefinition[] = [tableElement, samplingElement, benfordElement, kanbanBoardElement, kanbanBoardListElement, dbKanbanElement, screeningReviewElement, riskFlagsElement, synopsisElement, comparisonsElement, vvtElement, dsfaElement, geoMapElement]
