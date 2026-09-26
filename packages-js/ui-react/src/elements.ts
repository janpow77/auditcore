/**
 * @deprecated Hüllen um die Vue-Web-Components aus `@flowaudit/ui` (Stichprobe,
 * Benford, Screening, Risiko-Merkmale, Kanban, Geo-Karte). Sie brauchen Vue
 * und `@flowaudit/ui` als Peer-Abhängigkeit und bleiben nur, bis es native
 * React-Fassungen gibt. Tabelle, Synopse, VVT und DSFA sind seit 1.0.0 nativ
 * im Haupteinstieg `@flowaudit/ui-react` (ohne Vue).
 */
export { createElementComponent, eventPayload, type BaseElementProps, type ElementComponentOptions, type EventHandlers } from './legacy/createElementComponent'
export {
  FlowauditBenford,
  FlowauditRiskFlags,
  FlowauditSampling,
  FlowauditScreeningReview,
  type FlowauditBenfordProps,
  type FlowauditRiskFlagsProps,
  type FlowauditSamplingProps,
  type FlowauditScreeningError,
  type FlowauditScreeningReviewProps,
} from './legacy/wrappers'
export { FlowauditGeoMap, type FlowauditGeoMapProps } from './legacy/geo'
export { FlowauditKanbanBoard, FlowauditKanbanBoards, type FlowauditKanbanBoardProps, type FlowauditKanbanBoardsProps } from './legacy/kanban'
export { defineFlowauditElements } from '@flowaudit/ui/elements'
