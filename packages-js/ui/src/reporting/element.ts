import type { ElementDefinition } from '../elements/define'
import ReportExportPanel from './ReportExportPanel.vue'

/**
 * `<flowaudit-report-export>`: Eigenschaften `port` (ReportingPort), `tables`,
 * `filename`, `locale`; Ereignisse `preview-completed`, `export-completed`, `error`.
 */
export const reportExportElement: ElementDefinition = { tag: 'flowaudit-report-export', component: ReportExportPanel }
