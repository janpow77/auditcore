// View-Logik des Verzeichnisses von Verarbeitungstätigkeiten, ohne Vue und ohne DOM.
// Die Vollständigkeitsprüfung selbst rechnet die Bibliothek (Hinweise `Issue`);
// hier werden die Hinweise nur Tätigkeiten und Feldern zugeordnet.

import type { BadgeTone } from '../base/types'
import type { Activity, RegisterColumn, FieldValue, Issue, Person, RegisterContent, RegisterState, VersionView } from './types'

export const NO_DEPARTMENT = ''

export interface ActivityGroup {
  department: string
  items: { index: number; activity: Activity }[]
}

export interface Completeness {
  blocking: number
  hints: number
}

/** Tätigkeit ohne Kennung (die vergibt der Server beim Speichern). */
export function emptyActivity(columns: readonly RegisterColumn[], department: string): Activity {
  const activity: Activity = {}
  for (const column of columns) activity[column.key] = column.kind === 'text' ? '' : null
  activity.referat = department
  return activity
}

export function emptyContent(): RegisterContent {
  return { deckblatt: { verantwortlicher: { name: '' }, dsb: { name: '' } }, referate: [], taetigkeiten: [] }
}

/** Tiefe Kopie (JSON-Daten), damit Eingaben den gelesenen Stand nie verändern. */
export function cloneContent(content: RegisterContent): RegisterContent {
  return JSON.parse(JSON.stringify(content)) as RegisterContent
}

/** Referate wie in der Quelle: konfigurierte zuerst, dann unbekannte; leere entfallen. */
export function groupByDepartment(content: RegisterContent, query = ''): ActivityGroup[] {
  const needle = query.trim().toLocaleLowerCase('de')
  const rows = content.taetigkeiten
    .map((activity, index) => ({ index, activity }))
    .filter(({ activity }) => !needle || activityText(activity).includes(needle))
  const named = (activity: Activity): string => (typeof activity.referat === 'string' ? activity.referat.trim() : '')
  const known = content.referate.filter((department) => rows.some(({ activity }) => named(activity) === department))
  const unknown = [...new Set(rows.map(({ activity }) => named(activity)))]
    .filter((department) => !known.includes(department))
    .sort((a, b) => a.localeCompare(b, 'de'))
  return [...known, ...unknown].map((department) => ({
    department,
    items: rows.filter(({ activity }) => named(activity) === department),
  }))
}

function activityText(activity: Activity): string {
  return Object.values(activity)
    .filter((value): value is string => typeof value === 'string')
    .join(' ')
    .toLocaleLowerCase('de')
}

function split(subject: string): [string, string] {
  const at = subject.lastIndexOf(':')
  return at < 0 ? [subject, ''] : [subject.slice(0, at), subject.slice(at + 1)]
}

/** Schlüssel einer Tätigkeit für die Zuordnung der Hinweise (Kennung, sonst Name wie in der Bibliothek). */
export function activityKey(activity: Activity): string {
  return String(activity.id || activity.name || '')
}

export function issuesFor(issues: readonly Issue[], activity: Activity): Issue[] {
  const key = activityKey(activity)
  return issues.filter((issue) => split(issue.subject)[0] === key)
}

export function fieldIssues(issues: readonly Issue[], activity: Activity, field: string): Issue[] {
  const key = activityKey(activity)
  return issues.filter((issue) => {
    const [subject, name] = split(issue.subject)
    return subject === key && name === field
  })
}

/** Hinweise zum Deckblatt (Verantwortlicher, DSB). */
export function coverIssues(issues: readonly Issue[]): Issue[] {
  return issues.filter((issue) => split(issue.subject)[0] === 'deckblatt')
}

export function completeness(issues: readonly Issue[]): Completeness {
  const blocking = issues.filter((issue) => issue.blocking).length
  return { blocking, hints: issues.length - blocking }
}

export function completenessTone(value: Completeness): BadgeTone {
  if (value.blocking > 0) return 'danger'
  return value.hints > 0 ? 'warning' : 'success'
}

export function statusTone(status: string): BadgeTone {
  if (status === 'freigegeben') return 'success'
  if (status === 'entwurf' || status === 'dsb_beteiligung') return 'warning'
  return 'neutral'
}

/** Angezeigte Fassung: offener Entwurf vor Freigabe (dort wird gearbeitet). */
export function currentVersion(state: RegisterState | null, prefer: 'draft' | 'released' = 'draft'): VersionView | null {
  if (!state) return null
  return prefer === 'released' ? state.released ?? state.draft : state.draft ?? state.released
}

export function withField(content: RegisterContent, index: number, key: string, value: FieldValue): RegisterContent {
  const next = cloneContent(content)
  const activity = next.taetigkeiten[index]
  if (activity) activity[key] = value
  return next
}

export function withActivity(content: RegisterContent, activity: Activity): RegisterContent {
  const next = cloneContent(content)
  next.taetigkeiten.push(activity)
  return next
}

export function withoutActivity(content: RegisterContent, index: number): RegisterContent {
  const next = cloneContent(content)
  next.taetigkeiten.splice(index, 1)
  return next
}

export function withPerson(content: RegisterContent, part: 'verantwortlicher' | 'dsb', person: Person): RegisterContent {
  const next = cloneContent(content)
  next.deckblatt[part] = { ...next.deckblatt[part], ...person }
  return next
}

export function withDepartments(content: RegisterContent, departments: readonly string[]): RegisterContent {
  const next = cloneContent(content)
  next.referate = [...new Set(departments.map((d) => d.trim()).filter(Boolean))]
  return next
}

/** Anzeigewert eines Feldes; Wahrheitswerte und Leerwerte über die Texte der Komponente. */
export function displayValue(value: FieldValue | undefined, texts: { yes: string; no: string; empty: string }): string {
  if (value === true) return texts.yes
  if (value === false) return texts.no
  if (value === null || value === undefined || value === '') return texts.empty
  return String(value)
}

/** Eingabe eines Zahlfeldes: leer → null, sonst nichtnegative ganze Zahl; ungültig → undefined. */
export function parseCount(text: string): number | null | undefined {
  const trimmed = text.trim()
  if (!trimmed) return null
  if (!/^\d+$/.test(trimmed)) return undefined
  return Number(trimmed)
}

/** Vier-Augen-Prinzip vorab anzeigen: wer den Entwurf bearbeitet hat, kann ihn nicht freigeben. */
export function editedBy(version: VersionView | null, actor: string): boolean {
  return !!actor && !!version && version.editors.includes(actor)
}
