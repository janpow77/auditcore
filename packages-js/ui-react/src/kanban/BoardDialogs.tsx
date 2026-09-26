import type { Board, Card, Column, SharePermission } from '@auditcore/kanban-core'
import type { FlowauditKanbanBoardProps } from './FlowauditKanbanBoard'
import { KanbanCardDetail } from './KanbanCardDetail'
import { KanbanSettingsDialog } from './KanbanSettingsDialog'
import { KanbanShareDialog } from './KanbanShareDialog'
import type { BoardBinding } from './useKanbanBoard'

export interface BoardDialogsProps {
  props: FlowauditKanbanBoardProps
  binding: BoardBinding
  board: Board
  selected: Card | null
  dialog: 'settings' | 'share' | null
  setDialog: (dialog: 'settings' | 'share' | null) => void
  onCloseCard: () => void
}

/** Detailansicht, Einstellungen und Teilen des Boards (wie am Ende von `KanbanBoard.vue`). */
export function BoardDialogs({ props, binding, board, selected, dialog, setDialog, onCloseCard }: BoardDialogsProps) {
  const { actions } = binding.controller
  const { can } = binding.view
  const port = binding.port
  const search = port?.searchUsers ? (query: string) => port.searchUsers?.(query) ?? Promise.resolve([]) : null
  const removeCard = async (card: Card): Promise<void> => {
    if (await actions.remove(card.id)) onCloseCard()
  }
  const saveColumns = async (columns: Column[]): Promise<void> => {
    if (await actions.configure(columns)) setDialog(null)
  }
  return (
    <>
      <KanbanCardDetail
        card={selected}
        columns={board.columns}
        readOnly={!can.edit}
        canDelete={can.delete}
        locale={props.locale}
        renderExtra={props.renderCardExtra}
        onClose={onCloseCard}
        onUpdate={(fields) => selected && void actions.editCard(selected.id, fields)}
        onDelete={(card) => void removeCard(card)}
        onNavigate={(link) => selected && props.onNavigate?.(link, selected)}
        onAttachment={(attachment) => selected && props.onAttachment?.(attachment, selected)}
      />
      <KanbanSettingsDialog open={dialog === 'settings'} columns={board.columns} locale={props.locale} onClose={() => setDialog(null)} onSave={(columns) => void saveColumns(columns)} />
      <KanbanShareDialog
        open={dialog === 'share'}
        shares={board.shares}
        search={search}
        users={props.users}
        locale={props.locale}
        onClose={() => setDialog(null)}
        onShare={(userId: string, permission: SharePermission) => void actions.share(userId, permission)}
        onRevoke={(userId) => void actions.revoke(userId)}
      />
    </>
  )
}
