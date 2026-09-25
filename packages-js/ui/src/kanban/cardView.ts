/** Reine Darstellungshilfen für Karten und Boardliste (ohne DOM, einzeln getestet). */
import type { Priority } from '@flowaudit/kanban-core'
import type { BadgeTone } from '../base/types'

/** Badge-Farben je Präfix (WorkspaceTaskCard: VP, SYS/SP, JKB, PRJ), sonst grau. */
export const BADGE_COLORS: Readonly<Record<string, { background: string; color: string }>> = {
  VP: { background: '#2563eb', color: '#ffffff' },
  SYS: { background: '#7c3aed', color: '#ffffff' },
  SP: { background: '#7c3aed', color: '#ffffff' },
  JKB: { background: '#b45309', color: '#ffffff' },
  PRJ: { background: '#0e7490', color: '#ffffff' },
}
const DEFAULT_BADGE = { background: '#4b5563', color: '#ffffff' }

export function badgePrefix(badge: string): string {
  return badge.replace(/[-_]?\d+$/, '').toUpperCase()
}

export function badgeStyle(badge: string): { background: string; color: string } {
  return BADGE_COLORS[badgePrefix(badge)] ?? DEFAULT_BADGE
}

export const PRIORITY_TONES: Readonly<Record<Priority, BadgeTone>> = { hoch: 'danger', mittel: 'warning', niedrig: 'success' }

export function preview(text: string, length = 80): string {
  const chars = [...text]
  return chars.length > length ? `${chars.slice(0, length).join('')}…` : text
}

export type AgeKey = 'ageNew' | 'ageHours' | 'ageDays' | 'ageWeeks' | 'ageMonths'

/** Alter einer Karte in Stufen wie WorkspaceTaskCard (neu, Stunden, Tage, Wochen, Monate). */
export function cardAge(createdAt: string, now: number): { key: AgeKey; count: number } | null {
  const created = Date.parse(createdAt)
  if (Number.isNaN(created)) return null
  const hours = Math.floor((now - created) / 3_600_000)
  const days = Math.floor(hours / 24)
  if (hours < 1) return { key: 'ageNew', count: 0 }
  if (hours < 24) return { key: 'ageHours', count: hours }
  if (days < 7) return { key: 'ageDays', count: days }
  if (days < 35) return { key: 'ageWeeks', count: Math.floor(days / 7) }
  return { key: 'ageMonths', count: Math.floor(days / 30) }
}

export type RelativeKey = 'justNow' | 'minutesAgo' | 'hoursAgo' | 'daysAgo' | 'weeksAgo'

/** Relative Zeit für die Boardliste (WorkspaceSidebar.relativeTime). */
export function relativeTime(value: string, now: number): { key: RelativeKey; count: number } | null {
  const then = Date.parse(value)
  if (Number.isNaN(then)) return null
  const minutes = Math.floor((now - then) / 60_000)
  if (minutes < 1) return { key: 'justNow', count: 0 }
  if (minutes < 60) return { key: 'minutesAgo', count: minutes }
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return { key: 'hoursAgo', count: hours }
  const days = Math.floor(hours / 24)
  return days < 7 ? { key: 'daysAgo', count: days } : { key: 'weeksAgo', count: Math.floor(days / 7) }
}

/** Lesbare Schriftfarbe auf einer Kartenfarbe (Luminanzschwelle wie im Original). */
export function textOn(hex: string): 'light' | 'dark' {
  const match = /^#?([0-9a-f]{6})$/i.exec(hex.trim())
  if (!match?.[1]) return 'dark'
  const value = Number.parseInt(match[1], 16)
  const luminance = (0.299 * ((value >> 16) & 255) + 0.587 * ((value >> 8) & 255) + 0.114 * (value & 255)) / 255
  return luminance < 0.5 ? 'light' : 'dark'
}

/** Initialen aus einem Namen: erster und letzter Namensteil. */
export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean)
  const first = parts[0] ?? ''
  const last = parts[parts.length - 1] ?? ''
  if (parts.length >= 2) return `${first.charAt(0)}${last.charAt(0)}`.toUpperCase()
  return first.slice(0, 2).toUpperCase()
}

/** Kartenfarben zur Auswahl (TaskDetail colorPresets). */
export const CARD_COLORS: readonly { value: string; label: string }[] = [
  { value: '#ef4444', label: 'Rot' },
  { value: '#f97316', label: 'Orange' },
  { value: '#eab308', label: 'Gelb' },
  { value: '#22c55e', label: 'Grün' },
  { value: '#06b6d4', label: 'Cyan' },
  { value: '#3b82f6', label: 'Blau' },
  { value: '#8b5cf6', label: 'Violett' },
  { value: '#ec4899', label: 'Pink' },
  { value: '#6b7280', label: 'Grau' },
  { value: '#1e293b', label: 'Dunkel' },
]

/** Spaltenfarben (BoardSettingsDialog PRESET_COLORS). */
export const COLUMN_COLORS: readonly string[] = ['#7c3aed', '#f59e0b', '#10b981', '#ef4444', '#3b82f6', '#ec4899', '#6b7280', '#06b6d4']
