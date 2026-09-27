import type { ElementDefinition } from '../elements/define'
import ReportTemplates from './ReportTemplates.vue'

/**
 * `<flowaudit-report-templates>`: Eigenschaften `port`, `data`, `filename`, `locale`;
 * Ereignisse `template-select`, `preview-completed`, `report-rendered`, `error`.
 */
export const reportTemplatesElement: ElementDefinition = { tag: 'flowaudit-report-templates', component: ReportTemplates }
