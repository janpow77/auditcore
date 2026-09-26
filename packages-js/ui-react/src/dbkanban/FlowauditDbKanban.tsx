import { useRef } from 'react'
import { TextField } from '../base/TextField'
import { LocaleProvider } from '../i18n'
import { useElementId } from '../store'
import { DbKanbanColumn } from './DbKanbanColumn'
import { useDbKanban, type DbKanbanInputs, type UseDbKanban } from './useDbKanban'

export type FlowauditDbKanbanProps = DbKanbanInputs

function Toolbar({ view, id, editable }: { view: UseDbKanban; id: string; editable: boolean }) {
  const { t, state, controller } = view
  return (
    <header className="fa-db-kanban__toolbar">
      <h2 id={`${id}-title`} className="fa-db-kanban__title">{t('title')}</h2>
      {view.view.groupOptions.length ? (
        <div className="fa-db-kanban__group">
          <label htmlFor={`${id}-group`}>{t('groupByLabel')}</label>
          <select id={`${id}-group`} value={state.groupBy} onChange={(event) => controller.setGroupBy(event.target.value)}>
            {view.view.groupOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </div>
      ) : null}
      {state.table ? <TextField className="fa-db-kanban__search" value={state.query} type="search" label={t('searchLabel')} onChange={controller.setQuery} /> : null}
      {editable ? null : <span className="fa-db-kanban__readonly">{t('readOnly')}</span>}
    </header>
  )
}

function Messages({ view }: { view: UseDbKanban }) {
  const { t, state } = view
  return (
    <>
      {!view.source ? <p className="fa-db-kanban__state fa-db-kanban__state--error" role="alert">{t('noPort')}</p>
        : state.error ? <p className="fa-db-kanban__state fa-db-kanban__state--error" role="alert">{state.error.message}</p> : null}
      {view.view.notice ? <p className="fa-db-kanban__state">{view.view.notice}</p> : null}
      {view.view.noMatches ? <p className="fa-db-kanban__state">{t('noMatches')}</p> : null}
    </>
  )
}

/**
 * Datenbankansicht als Kanban, native React-Komponente (Vertrag wie
 * `<flowaudit-db-kanban>`): Datensätze nach einer Auswahl-Eigenschaft gruppiert,
 * Ablegen oder Strg+Pfeil setzt den Zellwert, Eintrag je Spalte anlegen.
 */
export function FlowauditDbKanban(props: FlowauditDbKanbanProps) {
  const view = useDbKanban(props)
  const { t, state, controller } = view
  const editable = props.editable ?? true
  const id = useElementId('fa-db-kanban')
  const root = useRef<HTMLElement | null>(null)
  const step = async (rowId: string, direction: 1 | -1): Promise<void> => {
    if (!(await controller.moveBy(rowId, direction))) return
    // Nach dem Neuzeichnen steht die Karte in der Nachbarspalte; Fokus mitnehmen.
    setTimeout(() => root.current?.querySelector<HTMLElement>(`[data-card-id="${CSS.escape(rowId)}"]`)?.focus(), 0)
  }
  return (
    <LocaleProvider locale={view.locale}>
      <section ref={root} className="fa-db-kanban" aria-labelledby={`${id}-title`} aria-busy={state.busy !== null || undefined}>
        <Toolbar view={view} id={id} editable={editable} />
        <p id={`${id}-hint`} className="fa-sr-only">{t('moveHint')}</p>
        <p className="fa-sr-only" role="status" aria-live="polite">{view.view.busyText || state.notice}</p>
        <Messages view={view} />
        {view.view.columns.length ? (
          <div className="fa-db-kanban__columns">
            {view.view.columns.map((column) => (
              <DbKanbanColumn
                key={column.value} column={column} t={t} editable={editable} canAdd={Boolean(view.source?.addRow)}
                dragging={state.dragging} over={state.dropTarget === column.value} hintId={`${id}-hint`}
                onCardDrag={controller.startDrag} onCardStep={(rowId, direction) => void step(rowId, direction)}
                onCardDrop={(rowId, value) => void controller.move(rowId, value)} onColumnOver={controller.setDropTarget}
                onCardAdd={(value) => void controller.addCard(value)}
              />
            ))}
          </div>
        ) : null}
      </section>
    </LocaleProvider>
  )
}
