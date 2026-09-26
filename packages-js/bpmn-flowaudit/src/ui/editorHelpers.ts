/**
 * Small editor-level rules shared by the Vue and React editors: read-only
 * lock of approved diagrams, file import, the save payload, the key index
 * of the filter bar and the toolbar's active states.
 */

import { excerptFromModel, rolesFor, type DiagramInfo, type PaletteColor, type ProfileData, type RolePaletteProvider } from '../index'
import type { EditorSession } from './session'
import type { ToolbarAction } from './toolbarActions'
import type { UiState } from './uiState'

/** Read-only: explicitly, or an approved diagram while `lockApproved` is on. */
export const isLocked = (readonly: boolean, lockApproved: boolean, info: DiagramInfo | null): boolean => readonly || (lockApproved && info?.status === 'freigegeben')

/** XML of an imported file and the name derived from it. */
export async function readImportFile(file: File): Promise<{ xml: string; name: string }> {
  return { xml: await file.text(), name: file.name.replace(/\.(bpmn|xml)$/i, '') }
}

/** Save payload (XML and diagram info); marks the editor saved. */
export async function savePayload(session: EditorSession): Promise<{ xml: string; info: DiagramInfo | null }> {
  const payload = { xml: await session.editor.exportXml(), info: session.editor.store.get().info }
  session.editor.markSaved()
  return payload
}

/** Key index of the diagram for the filter bar (empty while closed). */
export function filterKeys(session: EditorSession, open: boolean) {
  return open && session.editor.store.get().ready ? excerptFromModel(session.editor.model()).keys : {}
}

export function activeActions(ui: UiState): Partial<Record<ToolbarAction, boolean>> {
  return { 'left-panel': ui.leftOpen, 'right-panel': ui.rightOpen, walkthrough: ui.side === 'walkthrough', compare: ui.side === 'compare', 'key-filter': ui.filterOpen, decorations: ui.decorations, minimap: ui.minimap }
}

/** Assigns the chosen role (or adds a lane with it) at the element of the role popover. */
export function choosePopoverRole(session: EditorSession, profile: ProfileData | null, code: string): void {
  const popover = session.canvas.get().popover
  const provider = session.editor.instance()?.get<RolePaletteProvider>('flowauditRolePalette', false)
  const role = rolesFor(profile).find((entry) => entry.code === code)
  if (popover && provider && role) {
    if (popover.mode === 'add-lane') provider.addLaneWithRole(popover.element, role)
    else provider.assignRole(popover.element, role)
  }
  session.closePopover()
}

/** Colours the element of the colour popover (`null` removes the colour). */
export function choosePopoverColor(session: EditorSession, color: PaletteColor | null): void {
  const popover = session.canvas.get().popover
  if (popover) session.editor.services().modeling.setColor([popover.element], { fill: color?.fill ?? null, stroke: color?.stroke ?? null })
  session.closePopover()
}
