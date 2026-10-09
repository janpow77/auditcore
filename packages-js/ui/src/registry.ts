import type { ElementDefinition } from './elements/define'
import { benfordElement } from './benford/element'
import { extrapolationElement } from './extrapolation/element'
import { reportExportElement } from './reporting/element'
import { identifierCheckElement } from './identifiers/element'
import { assistantElement, dsfaElement, vvtElement } from './dataprotection/element'
import { comparisonsElement } from './documents/element'
import { extractionElement } from './extraction/element'
import { geoMapElement } from './geo/element'
import { samplingElement } from './sampling/element'
import { kanbanBoardElement, kanbanBoardListElement } from './kanban/element'
import { dbKanbanElement } from './dbkanban/element'
import { riskFlagsElement } from './risk/element'
import { screeningReviewElement } from './screening/element'
import { synopsisElement } from './synopsis/element'
import { tableElement } from './table/element'
import { batchChecksElement } from './batchchecks/element'
import { sampleSizePlannerElement } from './samplesize/element'
import { attributeSamplingElement } from './attributes/element'
import { reportTemplatesElement } from './reporttemplates/element'
import { runnerConsoleElement } from './runner/element'
import { accountWorkspaceElement } from './account/element'

/**
 * Alle Web Components von @auditcore/ui. Neue Komponenten tragen hier ihre
 * `ElementDefinition` ein (siehe docs/ui/beitragen.md).
 */
export const ELEMENTS: readonly ElementDefinition[] = [tableElement, samplingElement, benfordElement, extrapolationElement, kanbanBoardElement, kanbanBoardListElement, dbKanbanElement, screeningReviewElement, riskFlagsElement, synopsisElement, comparisonsElement, extractionElement, vvtElement, dsfaElement, assistantElement, geoMapElement, identifierCheckElement, reportExportElement, sampleSizePlannerElement, batchChecksElement, reportTemplatesElement, attributeSamplingElement, runnerConsoleElement, accountWorkspaceElement]
