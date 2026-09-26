/**
 * Logic of the property tabs: markers (toggle with colour), marker colour,
 * comments, actor/role of pools and lanes, FlowStat input.
 */

import { FLOWSTAT_FIELDS, label, MARKER_COLOR_PRECEDENCE, MARKER_COLORS, roleOf, type Actor, type Comment, type FlowstatField, type Marker, type ProcessModel, type ProfileData } from '../index'
import type { Translate } from './i18n/translator'

type Fill = { fill: string; stroke: string }

/** New marker list and the colour to set when a colouring marker is turned on. */
export function toggleMarker(markers: Marker[], type: string): { markers: Marker[]; color: Fill | null } {
  if (markers.some((marker) => marker.type === type)) return { markers: markers.filter((marker) => marker.type !== type), color: null }
  return { markers: [...markers, { type }], color: MARKER_COLORS[type] ?? null }
}

export function setMarkerText(markers: Marker[], type: string, text: string): Marker[] {
  return markers.map((marker) => (marker.type === type ? { ...marker, text: text.trim() || undefined } : marker))
}

/** Colour implied by the markers (precedence order) or `null`. */
export function colorFromMarkers(markers: Marker[]): Fill | null {
  const types = new Set(markers.map((marker) => marker.type))
  const winner = MARKER_COLOR_PRECEDENCE.find((type) => types.has(type))
  return winner ? MARKER_COLORS[winner] ?? null : null
}

export function newComment(elementId: string, text: string, author: string): Comment {
  return { id: `C${Date.now().toString(36)}`, elementId, text: text.trim(), author, timestamp: new Date().toISOString(), resolved: false }
}

export const toggleResolved = (comments: Comment[], id: string): Comment[] => comments.map((comment) => (comment.id === id ? { ...comment, resolved: !comment.resolved } : comment))
export const commentsOf = (comments: Comment[], elementId: string): Comment[] => comments.filter((comment) => comment.elementId === elementId)

export const isContainerType = (type: string): boolean => type === 'bpmn:Participant' || type === 'bpmn:Lane'

/** Actor after a change; `undefined` when neither role nor display name remain. */
export function actorAfter(actor: Actor, patch: Partial<Actor>): Actor | undefined {
  const next = { ...actor, ...patch }
  return next.role || next.displayName ? next : undefined
}

/** Role inherited from lane or pool for a flow node (display values) or `null`. */
export function inheritedRole(model: ProcessModel, elementId: string, profile: ProfileData | null, locale: 'de' | 'en', t: Translate): { name: string; role: string } | null {
  const found = model.byId.get(elementId)?.actor
  if (!found) return null
  const role = roleOf(profile, found.role)
  return { name: found.sourceName ?? '', role: role ? label(role.label, locale) : t('role.none') }
}

export const FLOWSTAT_KEYS = Object.keys(FLOWSTAT_FIELDS) as FlowstatField[]

/** Parsed FlowStat input (`null` clears the value). */
export function flowstatValue(field: FlowstatField, raw: string): number | string | null {
  if (raw.trim() === '') return null
  return FLOWSTAT_FIELDS[field].numeric ? Number(raw) : raw
}
