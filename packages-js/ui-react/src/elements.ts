/**
 * @deprecated Hüllen um die Vue-Web-Components aus `@flowaudit/ui` (Kanban).
 * Sie brauchen Vue und `@flowaudit/ui` als Peer-Abhängigkeit und bleiben nur,
 * bis es native React-Fassungen gibt. Tabelle, Synopse, VVT, DSFA, Geo-Karte,
 * Risiko-Merkmale, Screening, Stichprobe und Benford sind seit 1.0.0 nativ
 * im Haupteinstieg `@flowaudit/ui-react` (ohne Vue).
 */
export { createElementComponent, eventPayload, type BaseElementProps, type ElementComponentOptions, type EventHandlers } from './legacy/createElementComponent'
export { FlowauditKanbanBoard, FlowauditKanbanBoards, type FlowauditKanbanBoardProps, type FlowauditKanbanBoardsProps } from './legacy/kanban'
export { defineFlowauditElements } from '@flowaudit/ui/elements'
