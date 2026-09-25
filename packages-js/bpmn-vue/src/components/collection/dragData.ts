/** Drag-and-drop payloads of the collection tree. */

export const DIAGRAM_MIME = 'application/x-flowaudit-diagram'
export const FOLDER_MIME = 'application/x-flowaudit-folder'

export interface DropTarget {
  folderId: string | null
  /** Position among the diagrams of the folder (before this index). */
  position?: number
}

export function setDrag(event: DragEvent, kind: 'diagram' | 'folder', id: string): void {
  event.dataTransfer?.setData(kind === 'diagram' ? DIAGRAM_MIME : FOLDER_MIME, id)
  event.dataTransfer?.setData('text/plain', id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

export function readDrag(event: DragEvent): { kind: 'diagram' | 'folder'; id: string } | null {
  const diagram = event.dataTransfer?.getData(DIAGRAM_MIME)
  if (diagram) return { kind: 'diagram', id: diagram }
  const folder = event.dataTransfer?.getData(FOLDER_MIME)
  return folder ? { kind: 'folder', id: folder } : null
}
