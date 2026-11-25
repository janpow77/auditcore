// Prüfpunkte als Baum (Bereich → Prüfpunkt). Reine Ableitung aus dem
// Serverstand des Arbeitsbereichs; Status und Sperren berechnet der Server.
import type { ChecklistChange, ChecklistItemView, ChecklistStatus } from './assistantTypes'
import type { DataProtectionTranslate } from './messages'
import { prefixedLabel } from './requests'

export const CHECKLIST_STATUSES: readonly ChecklistStatus[] = [
  'offen',
  'in_bearbeitung',
  'zur_pruefung',
  'nachgewiesen',
  'klaerungsbedarf',
  'nicht_erfuellt',
  'nicht_anwendbar',
  'erneut_zu_pruefen',
]

/** Farbton eines Knotens; der Status steht daneben immer als Text (GUI-10). */
export type ChecklistTone = 'open' | 'progress' | 'attention' | 'settled'

// „settled“ entspricht SETTLED in auditcore_dataprotection.checklist.
const TONES: Record<ChecklistStatus, ChecklistTone> = {
  offen: 'open',
  in_bearbeitung: 'progress',
  zur_pruefung: 'progress',
  nachgewiesen: 'settled',
  nicht_anwendbar: 'settled',
  klaerungsbedarf: 'attention',
  nicht_erfuellt: 'attention',
  erneut_zu_pruefen: 'attention',
}

export interface ChecklistProgress {
  total: number
  settled: number
  attention: number
}

export interface ChecklistTreeNode {
  /** Stabile Kennung: `bereich:A` oder die Kennung des Prüfpunkts. */
  id: string
  kind: 'area' | 'item'
  /** Bereichskürzel bzw. Titel des Prüfpunkts. */
  label: string
  item: ChecklistItemView | null
  children: ChecklistTreeNode[]
  tone: ChecklistTone
  progress: ChecklistProgress
}

export function checklistTone(status: ChecklistStatus): ChecklistTone {
  return TONES[status] ?? 'open'
}

function itemNode(item: ChecklistItemView): ChecklistTreeNode {
  const tone = checklistTone(item.status)
  const progress = { total: 1, settled: tone === 'settled' ? 1 : 0, attention: tone === 'attention' ? 1 : 0 }
  return { id: item.id, kind: 'item', label: item.titel, item, children: [], tone, progress }
}

/** Summe über Knoten einer Ebene. */
export function checklistProgress(nodes: readonly ChecklistTreeNode[]): ChecklistProgress {
  const sum = { total: 0, settled: 0, attention: 0 }
  for (const node of nodes) {
    sum.total += node.progress.total
    sum.settled += node.progress.settled
    sum.attention += node.progress.attention
  }
  return sum
}

function areaTone(children: readonly ChecklistTreeNode[], progress: ChecklistProgress): ChecklistTone {
  if (progress.attention > 0) return 'attention'
  if (progress.total > 0 && progress.settled === progress.total) return 'settled'
  return children.some((child) => child.tone !== 'open') ? 'progress' : 'open'
}

/** Gruppiert nach `bereich` in der Reihenfolge des Katalogs. */
export function checklistTree(items: readonly ChecklistItemView[]): ChecklistTreeNode[] {
  const areas = new Map<string, ChecklistTreeNode[]>()
  for (const item of items) {
    const group = areas.get(item.bereich) ?? []
    group.push(itemNode(item))
    areas.set(item.bereich, group)
  }
  return Array.from(areas, ([area, children]) => {
    const progress = checklistProgress(children)
    return { id: `bereich:${area}`, kind: 'area' as const, label: area, item: null, children, tone: areaTone(children, progress), progress }
  })
}

/** Kennungen aller Knoten mit Kindern (für „Alle aufklappen“ und den Startzustand). */
export function checklistBranchIds(nodes: readonly ChecklistTreeNode[]): string[] {
  return nodes.flatMap((node) => (node.children.length ? [node.id, ...checklistBranchIds(node.children)] : []))
}

/** Neuer Satz aufgeklappter Knoten nach dem Umschalten von `id`. */
export function toggleChecklistNode(expanded: ReadonlySet<string>, id: string): Set<string> {
  const next = new Set(expanded)
  if (!next.delete(id)) next.add(id)
  return next
}

/** Aufgeklappte und bereits bekannte Knoten; neue Bereiche starten offen. */
export interface ChecklistExpansion {
  expanded: ReadonlySet<string>
  known: ReadonlySet<string>
}

/**
 * Klappt Bereiche auf, die erst jetzt im Baum stehen (z. B. weil die Prüfpunkte
 * später kommen). Bereits bekannte Knoten behalten den Zustand des Nutzers;
 * ohne neue Bereiche kommt derselbe Zustand zurück.
 */
export function expandNewChecklistBranches(state: ChecklistExpansion, branchIds: readonly string[]): ChecklistExpansion {
  const added = branchIds.filter((id) => !state.known.has(id))
  if (!added.length) return state
  return { expanded: new Set([...state.expanded, ...added]), known: new Set([...state.known, ...added]) }
}

export interface ChecklistEdit {
  status: ChecklistStatus
  justification: string
  evidence: string
  owner: string
  due: string
}

/** Eingabestand der Detailansicht aus dem Serverstand. */
export function checklistEdit(item: ChecklistItemView): ChecklistEdit {
  return { status: item.status, justification: item.justification, evidence: item.evidence_ids.join(', '), owner: item.owner, due: item.due }
}

/** Schlüssel der bearbeitbaren Inhalte; gleich, solange der Serverstand des Prüfpunkts gleich bleibt. */
export function checklistEditKey(item: ChecklistItemView): string {
  return JSON.stringify([item.status, item.justification, item.owner, item.due, item.evidence_ids])
}

/** Änderung für den Server; Bearbeitung und Frist gehen nur mit, wenn sie geändert wurden. */
export function checklistChange(item: ChecklistItemView, edit: ChecklistEdit): ChecklistChange {
  const change: ChecklistChange = { status: edit.status, justification: edit.justification, evidence_ids: parseEvidenceIds(edit.evidence) }
  if (edit.owner.trim() !== item.owner) change.owner = edit.owner.trim()
  if (edit.due !== item.due) change.due = edit.due
  return change
}

/** Eingabe „a, b“ als Liste von Nachweiskennungen. */
export function parseEvidenceIds(value: string): string[] {
  return value.split(',').map((entry) => entry.trim()).filter(Boolean)
}

export interface ChecklistMetaRow {
  key: string
  label: string
  value: string
}

/** Angaben zum Prüfpunkt für die Detailansicht; leere Angaben entfallen. */
export function checklistMeta(t: DataProtectionTranslate, item: ChecklistItemView, when: (value: string, withTime: boolean) => string): ChecklistMetaRow[] {
  const kinds = item.nachweisarten.map((kind) => prefixedLabel(t, 'evidenceKind', kind)).join(', ')
  const rows: ChecklistMetaRow[] = [
    { key: 'role', label: t('checklistOwnerRole'), value: prefixedLabel(t, 'ownerRole', item.zustaendig) },
    { key: 'kinds', label: t('checklistEvidenceKinds'), value: kinds },
    { key: 'owner', label: t('checklistOwner'), value: item.owner },
    { key: 'due', label: t('checklistDue'), value: item.due && when(item.due, false) },
    { key: 'objection', label: t('checklistObjection'), value: item.objection },
    { key: 'updated', label: t('checklistUpdated'), value: [item.updated_by, item.updated_at && when(item.updated_at, true)].filter(Boolean).join(' · ') },
    { key: 'confirmed', label: t('checklistConfirmed'), value: item.confirmed_by },
  ]
  return rows.filter((row) => row.value)
}
