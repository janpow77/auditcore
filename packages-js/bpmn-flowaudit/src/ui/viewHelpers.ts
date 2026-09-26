/**
 * Logic of the side views and canvas overlays: issue filter, comparison and
 * its highlighting, walk-through steps, page grid, popover position,
 * palette sections and side tabs.
 */

import {
  checkTargetActual,
  compareVersions,
  computePageGrid,
  diffColors,
  HIGHLIGHT_CLASSES,
  loadDefinitions,
  modelFromDefinitions,
  PAGE_FORMATS,
  pageSize,
  type AuditStep,
  type Comparison,
  type Orientation,
  type ProcessModel,
  type Severity,
  type TargetActualCheck,
  type ValidationIssue,
  type ViewboxLike,
} from '../index'
import { AUDIT_STEP_LIST } from './descriptors'
import type { PaletteItem } from './paletteEntries'
import type { SideView } from './uiState'

export const ISSUE_ICONS: Record<Severity, string> = { fehler: 'error', warnung: 'warning', hinweis: 'hint' }
export const SEVERITIES: Severity[] = ['fehler', 'warnung', 'hinweis']
export const filterIssues = (issues: ValidationIssue[], filter: Severity | 'alle') => (filter === 'alle' ? issues : issues.filter((item) => item.severity === filter))
export const countSeverity = (issues: ValidationIssue[], severity: Severity) => issues.filter((item) => item.severity === severity).length

export const SIDE_VIEWS: { id: SideView; label: string; icon: string }[] = [
  { id: 'properties', label: 'props.label', icon: 'info' },
  { id: 'issues', label: 'issues.label', icon: 'validate' },
  { id: 'walkthrough', label: 'walk.title', icon: 'play' },
  { id: 'compare', label: 'compare.title', icon: 'compare' },
]

export type CompareMode = 'version' | 'targetActual'

export interface CompareResult {
  comparison: Comparison | null
  check: TargetActualCheck | null
}

export async function runComparison(mode: CompareMode, otherXml: string, current: ProcessModel): Promise<CompareResult> {
  const other = modelFromDefinitions((await loadDefinitions(otherXml)).definitions)
  return { comparison: mode === 'version' ? compareVersions(other, current) : null, check: mode === 'targetActual' ? checkTargetActual(other, current) : null }
}

/** Highlight classes of a comparison or target/actual check. */
export function compareClasses(result: CompareResult): Map<string, string> {
  const classes = new Map<string, string>()
  if (result.comparison) for (const [id, kind] of diffColors(result.comparison)[1]) classes.set(id, HIGHLIGHT_CLASSES.diff[kind])
  for (const [id, css] of checkClasses(result.check)) classes.set(id, css)
  return classes
}

function checkClasses(check: TargetActualCheck | null): [string, string][] {
  if (!check) return []
  const met = check.results.filter((item) => item.actualId).map((item): [string, string] => [item.actualId as string, item.met ? HIGHLIGHT_CLASSES.walkthrough.erfuellt : HIGHLIGHT_CLASSES.walkthrough.nicht_erfuellt])
  return [...met, ...check.additionalInActual.map((id): [string, string] => [id, HIGHLIGHT_CLASSES.diff.hinzugefuegt])]
}

export const WALK_FIELDS = AUDIT_STEP_LIST.fields.filter((field) => field.key !== 'id')

export const stepDraft = (tester?: string): AuditStep => ({ tester, date: new Date().toISOString().slice(0, 10), result: 'erfuellt' })
export const clampStep = (step: number, count: number): number => Math.max(0, Math.min(step, count - 1))

export function walkthroughClasses(steps: { elementId: string; status: keyof typeof HIGHLIGHT_CLASSES.walkthrough }[], currentId?: string): Map<string, string> {
  const classes = new Map<string, string>(steps.map((step) => [step.elementId, HIGHLIGHT_CLASSES.walkthrough[step.status]]))
  if (currentId) classes.set(currentId, HIGHLIGHT_CLASSES.walkthrough.current)
  return classes
}

export const progressPercent = (progress: { done: number; total: number }): string => `${progress.total ? (progress.done / progress.total) * 100 : 0}%`

export function pageGrid(view: string, viewbox: ViewboxLike, width: number, height: number, pageLabel: string) {
  if (view === 'aus') return { vertical: [], horizontal: [], pages: [] }
  const [format = 'a4', orientation = 'hoch'] = view.split('-')
  return computePageGrid(viewbox, pageSize(format, orientation as Orientation), width, height, pageLabel)
}

export const PAGE_OPTIONS = PAGE_FORMATS.flatMap((format) => (['hoch', 'quer'] as const).map((orientation) => ({ value: `${format.id}-${orientation}`, label: `${format.label} ${orientation}` })))

/** Position of a canvas popover, kept inside the canvas. */
export function popoverPosition(x: number, y: number, width: number, height: number): { left: string; top: string } {
  return { left: `${Math.max(4, Math.min(x + 8, width - 260))}px`, top: `${Math.max(4, Math.min(y + 8, height - 320))}px` }
}

export function paletteSections(items: PaletteItem[]) {
  const roles = items.filter((item) => item.group === 'flowaudit-roles')
  const tools = items.filter((item) => item.group === 'tools')
  const shapes = items.filter((item) => item.group !== 'tools' && item.group !== 'flowaudit-roles')
  return [
    { id: 'tools', title: 'palette.tools', items: tools },
    { id: 'shapes', title: 'palette.shapes', items: shapes },
    { id: 'roles', title: 'palette.roles', items: roles },
  ]
}
