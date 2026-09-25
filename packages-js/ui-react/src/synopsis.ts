import type { Comparison, ComparisonResult, Locale, SynopsisLayout, SynopsisPort } from '@flowaudit/ui'
import { createElementComponent } from './createElementComponent'

export interface FlowauditSynopsisProps {
  comparison?: Comparison | null
  result?: ComparisonResult | null
  comparisonId?: string
  port?: SynopsisPort | null
  title?: string
  oldLabel?: string
  newLabel?: string
  editable?: boolean
  layout?: SynopsisLayout
  locale?: Locale
}

/** `<flowaudit-synopsis>` als React-Komponente (Synopse / Versionsvergleich). */
export const FlowauditSynopsis = createElementComponent<
  FlowauditSynopsisProps,
  { onRowUpdate: string; onExport: string; onNavigate: string; onLayoutChange: string }
>('flowaudit-synopsis', {
  properties: ['comparison', 'result', 'comparisonId', 'port', 'title', 'oldLabel', 'newLabel', 'editable', 'layout', 'locale'],
  events: { onRowUpdate: 'row-update', onExport: 'export', onNavigate: 'navigate', onLayoutChange: 'update:layout' },
})
