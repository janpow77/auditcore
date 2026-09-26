/** View state of one editor: panels, side view, dialogs, key filter, modes. */

import type { Direction, KeyKind } from '../index'

export type SideView = 'properties' | 'issues' | 'walkthrough' | 'compare'
export type DialogId = 'info' | 'export' | 'enrich' | 'esi' | 'search' | 'shortcuts' | 'xml'

export interface UiState {
  leftOpen: boolean
  rightOpen: boolean
  side: SideView
  dialogs: Record<DialogId, boolean>
  filterOpen: boolean
  filterKind: KeyKind
  filterValue: string
  filterHits: number
  pageView: string
  direction: Direction
  message: string
  decorations: boolean
  minimap: boolean
}

export const DIALOG_IDS: DialogId[] = ['info', 'export', 'enrich', 'esi', 'search', 'shortcuts', 'xml']

export function initialUiState(): UiState {
  return {
    leftOpen: true,
    rightOpen: true,
    side: 'properties',
    dialogs: { info: false, export: false, enrich: false, esi: false, search: false, shortcuts: false, xml: false },
    filterOpen: false,
    filterKind: 'ka',
    filterValue: '',
    filterHits: 0,
    pageView: 'aus',
    direction: 'waagerecht',
    message: '',
    decorations: true,
    minimap: false,
  }
}

/** Patch that opens or closes one dialog. */
export function dialogPatch(state: UiState, id: DialogId, open: boolean): Partial<UiState> {
  return { dialogs: { ...state.dialogs, [id]: open } }
}

/** Opens a side view, or returns to the properties when it is already shown. */
export function toggleSidePatch(state: UiState, view: SideView): Partial<UiState> {
  return { side: state.side === view && state.rightOpen ? 'properties' : view, rightOpen: true }
}
