import { forwardRef, useImperativeHandle, useRef, useState, type KeyboardEvent, type Ref } from 'react'
import {
  deliverExport,
  focusRow,
  navigationDirection,
  type ClientExportFormat,
  type Comparison,
  type ComparisonResult,
  type ExportPayload,
  type Locale,
  type RowUpdate,
  type SynopsisLayout,
  type SynopsisPort,
} from '@auditcore/ui-core'
import { useElementId } from '../store'
import { SynopsisCommands } from './SynopsisCommands'
import { SynopsisHeader } from './SynopsisHeader'
import { SynopsisRow } from './SynopsisRow'
import { SynopsisToolbar } from './SynopsisToolbar'
import { useSynopsis, type UseSynopsis } from './useSynopsis'

export interface FlowauditSynopsisProps {
  /** Gespeicherter Vergleich (`GET /comparisons/{id}`). */
  comparison?: Comparison | null
  /** Alternativ nur das Ergebnisobjekt (`ComparisonResult.to_dict()`). */
  result?: ComparisonResult | null
  /** Mit `port`: Vergleich selbst laden. */
  comparisonId?: string
  port?: SynopsisPort | null
  title?: string
  oldLabel?: string
  newLabel?: string
  /** Auswahl und Grund je Zeile bearbeiten (Vorschau vor der Ausgabe). */
  editable?: boolean
  locale?: Locale
  /** Gesteuerte Ansicht; ohne Angabe verwaltet die Komponente sie selbst (Start: `defaultLayout`). */
  layout?: SynopsisLayout
  defaultLayout?: SynopsisLayout
  onLayoutChange?: (layout: SynopsisLayout) => void
  onRowUpdate?: (update: RowUpdate) => void
  onExport?: (payload: ExportPayload) => void
  onNavigate?: (rowId: string) => void
  className?: string
}

/** Methoden über `ref` (wie `defineExpose` der Vue-Fassung). */
export interface FlowauditSynopsisHandle {
  next: () => string | null
  previous: () => string | null
  exportAs: (format: ClientExportFormat) => ExportPayload | null
}

function useLayout(props: FlowauditSynopsisProps): [SynopsisLayout, (layout: SynopsisLayout) => void] {
  const [own, setOwn] = useState<SynopsisLayout>(props.defaultLayout ?? 'side-by-side')
  const layout = props.layout ?? own
  return [layout, (next) => {
    setOwn(next)
    props.onLayoutChange?.(next)
  }]
}

function useNavigation(synopsis: UseSynopsis, root: Ref<HTMLElement | null>, onNavigate?: (id: string) => void) {
  return (direction: 1 | -1): string | null => {
    const next = synopsis.controller.go(synopsis.selection, direction)
    if (next === null) return null
    focusRow((root as { current: HTMLElement | null }).current, next)
    onNavigate?.(next)
    return next
  }
}

function Rows({ synopsis, props, layout }: { synopsis: UseSynopsis; props: FlowauditSynopsisProps; layout: SynopsisLayout }) {
  const { selection, controller, t } = synopsis
  const view = selection.view
  if (!view) return null
  const update = async (id: string, patch: Omit<RowUpdate, 'row_id'>): Promise<void> => {
    props.onRowUpdate?.(await controller.updateRow(synopsis.inputs, id, patch))
  }
  return (
    <div className="fa-synopsis__rows">
      {selection.rows.length === 0 ? <p className="fa-synopsis__state">{t('noMatches')}</p> : null}
      {selection.rows.map((row) => (
        <SynopsisRow
          key={row.id}
          row={row}
          layout={layout}
          oldLabel={view.oldLabel}
          newLabel={view.newLabel}
          reasonLabel={view.reasonLabel}
          editable={!!props.editable}
          active={selection.activeId === row.id}
          t={t}
          onUpdate={(patch) => void update(row.id, patch)}
          onActivate={() => row.isChange && controller.activate(row.id)}
        />
      ))}
    </div>
  )
}

function States({ synopsis }: { synopsis: UseSynopsis }) {
  const { state, selection, t } = synopsis
  return (
    <>
      {state.loading ? <p className="fa-synopsis__state" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-synopsis__state fa-synopsis__state--error" role="alert">{state.error}</p> : null}
      {!selection.view && !state.loading && !state.error ? <p className="fa-synopsis__state">{t('empty')}</p> : null}
    </>
  )
}

/**
 * Synopse / Versionsvergleich als native React-Komponente (Vertrag wie
 * `<flowaudit-synopsis>`): Seiten- oder Inline-Ansicht, Wortdifferenz, Filter,
 * Navigation mit N/J und P/K, Exporte, optional Auswahl und Grund je Zeile.
 */
export const FlowauditSynopsis = forwardRef<FlowauditSynopsisHandle, FlowauditSynopsisProps>(function FlowauditSynopsis(props, ref) {
  const root = useRef<HTMLElement | null>(null)
  const headingId = useElementId('fa-synopsis')
  const synopsis = useSynopsis(props)
  const { selection, controller, state, t } = synopsis
  const [layout, setLayout] = useLayout(props)
  const go = useNavigation(synopsis, root, props.onNavigate)
  const run = (format: ClientExportFormat): void => {
    const payload = synopsis.exportAs(format)
    if (!payload) return
    props.onExport?.(payload)
    deliverExport(payload)
  }
  useImperativeHandle(ref, () => ({ next: () => go(1), previous: () => go(-1), exportAs: synopsis.exportAs }))
  const onKeyDown = (event: KeyboardEvent<HTMLElement>): void => {
    const direction = navigationDirection(event.nativeEvent)
    if (direction === null) return
    go(direction)
    event.preventDefault()
  }
  const view = selection.view
  return (
    <section ref={root} className={props.className ? `fa-synopsis ${props.className}` : 'fa-synopsis'} aria-labelledby={view ? headingId : undefined} aria-busy={state.loading || undefined} onKeyDown={onKeyDown}>
      <States synopsis={synopsis} />
      {view ? (
        <>
          <SynopsisHeader view={view} selectedText={selection.selectedText} editable={!!props.editable} headingId={headingId} t={t} />
          <SynopsisToolbar
            layout={layout}
            query={state.filter.query}
            onlySelected={state.filter.onlySelected}
            highlight={selection.highlight}
            statuses={state.filter.statuses}
            editable={!!props.editable}
            position={selection.position}
            canPrev={selection.canPrev}
            canNext={selection.canNext}
            serverExports={selection.serverExports}
            t={t}
            onLayout={setLayout}
            onQuery={controller.setQuery}
            onOnlySelected={controller.setOnlySelected}
            onHighlight={controller.setHighlight}
            onToggleStatus={controller.toggleStatus}
            onAllChanges={controller.setAllChanges}
            onNavigate={go}
            onExport={run}
          />
          <Rows synopsis={synopsis} props={props} layout={layout} />
          <SynopsisCommands view={view} t={t} />
        </>
      ) : null}
    </section>
  )
})
