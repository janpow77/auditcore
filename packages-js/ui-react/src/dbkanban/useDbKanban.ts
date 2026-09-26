import { useEffect, useMemo, useRef, useState } from 'react'
import { createMemoryRecordPort, type RecordPort, type RecordRow, type RecordTable } from '@auditcore/kanban-core'
import {
  createDbKanbanController,
  dbKanbanMessages,
  dbKanbanView,
  type DbKanbanController,
  type DbKanbanData,
  type DbKanbanError,
  type DbKanbanTranslate,
  type DbKanbanView,
  type Locale,
  type RecordMove,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

export interface DbKanbanInputs {
  /** Datenquelle (Datenbank/REST der Anwendung) mit `load`, `updateCell` und optional `addRow`. */
  port?: RecordPort | null
  /** Ohne Port: Tabelle direkt; Änderungen kommen über `onTableChange` zurück. */
  table?: RecordTable | null
  /** Gesteuerte Gruppierung (Gegenstück zu `v-model:group-by`); leer: erste Auswahl-Eigenschaft. */
  groupBy?: string
  onGroupByChange?: (propertyId: string) => void
  /** `false`: nur Ansicht, kein Verschieben und Anlegen. */
  editable?: boolean
  locale?: Locale
  onRecordMove?: (move: RecordMove) => void
  onRecordAdd?: (row: RecordRow) => void
  onTableChange?: (table: RecordTable) => void
  onError?: (error: DbKanbanError) => void
}

export interface UseDbKanban {
  t: DbKanbanTranslate
  locale: Locale
  controller: DbKanbanController
  state: DbKanbanData
  view: DbKanbanView
  source: RecordPort | null
}

function useSource(props: DbKanbanInputs, latest: { current: { props: DbKanbanInputs } }): RecordPort | null {
  const { port, table } = props
  return useMemo(
    () => port ?? (table ? createMemoryRecordPort(table, { onChange: (next) => latest.current.props.onTableChange?.(next) }) : null),
    [port, table, latest],
  )
}

/** React-Anbindung der Datenbankansicht aus `@auditcore/ui-core` (dieselbe Logik wie `useDbKanban` in Vue). */
export function useDbKanban(props: DbKanbanInputs): UseDbKanban {
  const { t, locale } = useTranslation(dbKanbanMessages, props.locale)
  const latest = useRef({ props, t, locale, source: null as RecordPort | null })
  const source = useSource(props, latest)
  latest.current = { props, t, locale, source }
  const [controller] = useState(() =>
    createDbKanbanController({
      port: () => latest.current.source,
      t: () => latest.current.t,
      lang: () => latest.current.locale,
      editable: () => latest.current.props.editable ?? true,
      onMoved: (move) => latest.current.props.onRecordMove?.(move),
      onAdded: (row) => latest.current.props.onRecordAdd?.(row),
      onGroupBy: (propertyId) => latest.current.props.onGroupByChange?.(propertyId),
      onError: (error) => latest.current.props.onError?.(error),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    void controller.load(latest.current.props.groupBy)
  }, [controller, source])
  useEffect(() => {
    if (props.groupBy) controller.setGroupBy(props.groupBy)
  }, [controller, props.groupBy])
  const view = useMemo(() => dbKanbanView(state, t, locale), [state, t, locale])
  return { t, locale, controller, state, view, source }
}
