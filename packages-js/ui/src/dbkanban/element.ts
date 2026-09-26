import type { ElementDefinition } from '../elements/define'
import FaDbKanban from './FaDbKanban.vue'

/**
 * `<flowaudit-db-kanban>`: `port` (RecordPort) oder `table` als JS-Eigenschaft;
 * Ereignisse `record-move`, `record-add`, `table-change`, `update:groupBy`, `error`.
 */
export const dbKanbanElement: ElementDefinition = { tag: 'flowaudit-db-kanban', component: FaDbKanban }
