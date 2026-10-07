/**
 * Resizable, collapsible side panels (properties on the right, collection
 * on the left): bounds, stored width and open state, width from a pointer
 * drag or a key. Framework-free; Vue and React only wire the events.
 */

import { browserStorage, readJson, writePreference, type PreferenceStorage } from './preferences'

export interface PanelBounds {
  min: number
  max: number
  initial: number
}

export interface PanelState {
  width: number
  open: boolean
}

/** Which side of the handle the panel lies on. */
export type PanelEdge = 'left' | 'right'

export const PROPERTIES_PANEL: PanelBounds = { min: 300, max: 760, initial: 420 }
export const COLLECTION_PANEL: PanelBounds = { min: 220, max: 560, initial: 300 }
/** Width of the rail shown instead of a collapsed panel. */
export const PANEL_RAIL = 28
const KEY_STEP = 24

export const panelKey = (id: string): string => `auditcore.bpmn.panel.${id}`

export function clampWidth(width: number, bounds: PanelBounds): number {
  if (!Number.isFinite(width)) return bounds.initial
  return Math.round(Math.min(bounds.max, Math.max(bounds.min, width)))
}

export function readPanel(id: string, bounds: PanelBounds, storage: PreferenceStorage | null = browserStorage()): PanelState {
  const stored = readJson(panelKey(id), storage)
  const width = typeof stored?.width === 'number' ? stored.width : bounds.initial
  return { width: clampWidth(width, bounds), open: stored?.open !== false }
}

export function writePanel(id: string, state: PanelState, storage: PreferenceStorage | null = browserStorage()): void {
  writePreference(panelKey(id), JSON.stringify({ width: Math.round(state.width), open: state.open }), storage)
}

/** Width while dragging the handle from `startX` to `x`. */
export function dragWidth(startWidth: number, startX: number, x: number, edge: PanelEdge, bounds: PanelBounds): number {
  const delta = edge === 'right' ? startX - x : x - startX
  return clampWidth(startWidth + delta, bounds)
}

/** Width after a key on the handle (arrows, Home/End); `null` for other keys. */
export function keyWidth(width: number, key: string, edge: PanelEdge, bounds: PanelBounds): number | null {
  const grow = edge === 'right' ? 'ArrowLeft' : 'ArrowRight'
  const shrink = edge === 'right' ? 'ArrowRight' : 'ArrowLeft'
  if (key === grow) return clampWidth(width + KEY_STEP, bounds)
  if (key === shrink) return clampWidth(width - KEY_STEP, bounds)
  if (key === 'Home') return bounds.min
  if (key === 'End') return bounds.max
  return null
}
