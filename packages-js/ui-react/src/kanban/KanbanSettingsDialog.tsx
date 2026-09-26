import { createColumnEditor, selectColumnEditor, type Column } from '@auditcore/kanban-core'
import type { Locale } from '@auditcore/ui-core'
import { useLayoutEffect, useRef, useState } from 'react'
import { Button } from '../base/Button'
import { Dialog } from '../base/Dialog'
import { useStoreState } from '../store'
import { ColumnEditorRow } from './ColumnEditorRow'
import { useKanbanDialogText } from './text'

export interface KanbanSettingsDialogProps {
  open: boolean
  columns: readonly Column[]
  locale?: Locale
  onClose: () => void
  onSave: (columns: Column[]) => void
}

/** Spalten, Farben und WIP-Limits wie `KanbanSettingsDialog.vue` (Prüfung über die Kernlogik). */
export function KanbanSettingsDialog(props: KanbanSettingsDialogProps) {
  const { t } = useKanbanDialogText(props.locale)
  const [editor] = useState(() => createColumnEditor())
  const state = useStoreState(editor.store)
  const view = selectColumnEditor(state, editor.maxColumns)
  const columns = useRef(props.columns)
  columns.current = props.columns
  // Wie der Vue-watch auf `open`: beim Öffnen den Entwurf aus den Spalten neu belegen.
  useLayoutEffect(() => {
    if (props.open) editor.reset(columns.current)
  }, [props.open, editor])
  const save = (): void => {
    const columns = editor.validated()
    if (columns) props.onSave(columns)
  }
  const footer = (
    <>
      <Button icon="plus" disabled={!view.canAdd} onClick={() => editor.add(t('newColumn'))}>{t('addColumn')}</Button>
      <span style={{ flex: 1 }} />
      <Button onClick={props.onClose}>{t('cancel')}</Button>
      <Button variant="primary" disabled={!view.dirty} testId="kanban-settings-save" onClick={save}>{t('save')}</Button>
    </>
  )
  return (
    <Dialog open={props.open} title={t('settingsTitle')} description={t('settingsDescription')} size="lg" locale={props.locale} footer={footer} onClose={props.onClose}>
      <p className="fa-kanban-detail__label">{t('columns', { count: state.draft.length, max: editor.maxColumns })}</p>
      <ol className="fa-kanban-settings__list">
        {state.draft.map((column, index) => (
          <ColumnEditorRow
            key={column.id}
            column={column}
            first={index === 0}
            last={index === state.draft.length - 1}
            canRemove={view.canRemove}
            locale={props.locale}
            onUpdate={(patch) => editor.update(index, patch)}
            onRemove={() => editor.remove(index)}
            onMove={(step) => editor.move(index, step)}
          />
        ))}
      </ol>
      {view.removed.length ? <p className="fa-kanban-settings__hint">{t('removedHint')}</p> : null}
      {state.problem ? <p className="fa-field__note" role="alert" style={{ color: 'var(--fa-color-danger)' }}>{state.problem}</p> : null}
    </Dialog>
  )
}
