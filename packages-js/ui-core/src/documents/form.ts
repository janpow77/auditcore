/**
 * Formular „Neuer Vergleich“ als reine Daten: Vorgaben wie im REST-Vertrag
 * (`POST /comparisons`, docs/ui/synopsis-rest.md), Prüfung vor dem Hochladen
 * und Umsetzung in die Formularfelder des Servers. Der Server prüft erneut.
 */
import type { CompareFields } from '../synopsis/port'
import { ROW_STATUSES, type ComparisonProfile, type RowStatus } from '../synopsis/types'
import type { ComparisonsMessageKey } from './messages'

export type ComparisonKind = 'standard' | 'article_law'
export type ComparisonMode = 'auto' | 'checklist' | 'text'
export const COMPARISON_KINDS: readonly ComparisonKind[] = ['standard', 'article_law']
export const COMPARISON_MODES: readonly ComparisonMode[] = ['auto', 'checklist', 'text']
export const ACCEPTED_EXTENSIONS: readonly string[] = ['.docx', '.docm', '.pdf']
/** Vorgabe des Servers (`ServiceSettings.max_upload_bytes`). */
export const DEFAULT_MAX_UPLOAD_BYTES = 20 * 1024 * 1024
export const MIN_THRESHOLD = 70
export const MAX_THRESHOLD = 100
export const MAX_TITLE = 255

/** Datei aus einem Eingabefeld (im Browser `File`). */
export interface UploadFile extends Blob {
  readonly name: string
}

export interface CompareForm {
  oldFile: UploadFile | null
  newFile: UploadFile | null
  title: string
  kind: ComparisonKind
  mode: ComparisonMode
  threshold: number
  includeAnswers: boolean
  includeNotes: boolean
  includeEditorial: boolean
  highlightWords: boolean
  sections: readonly RowStatus[]
  /** Leer: Standardprofil des Servers. */
  profile: string
}

export const DEFAULT_FORM: CompareForm = {
  oldFile: null,
  newFile: null,
  title: '',
  kind: 'standard',
  mode: 'auto',
  threshold: 85,
  includeAnswers: true,
  includeNotes: true,
  includeEditorial: false,
  highlightWords: true,
  sections: ['changed', 'removed', 'added', 'moved'],
  profile: '',
}

/** Ein Befund der Formularprüfung: Textschlüssel und Platzhalter. */
export interface FormProblem {
  key: Extract<ComparisonsMessageKey, `problem_${string}`>
  field: 'oldFile' | 'newFile' | 'threshold' | 'sections' | 'title'
  params?: Readonly<Record<string, string>>
}

/** Größenangabe wie „20 MiB“ oder „512 KiB“. */
export function formatBytes(bytes: number, lang = 'de'): string {
  const format = (value: number): string => new Intl.NumberFormat(lang, { maximumFractionDigits: 1 }).format(value)
  if (bytes >= 1024 * 1024) return `${format(bytes / (1024 * 1024))} MiB`
  if (bytes >= 1024) return `${format(bytes / 1024)} KiB`
  return `${format(bytes)} B`
}

export function hasAcceptedExtension(name: string): boolean {
  const lower = name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((extension) => lower.endsWith(extension))
}

function fileProblems(file: UploadFile | null, field: 'oldFile' | 'newFile', maxBytes: number, lang: string): FormProblem[] {
  if (!file) return [{ key: field === 'oldFile' ? 'problem_oldMissing' : 'problem_newMissing', field }]
  if (!hasAcceptedExtension(file.name)) return [{ key: 'problem_type', field, params: { name: file.name } }]
  if (file.size > maxBytes) return [{ key: 'problem_size', field, params: { name: file.name, size: formatBytes(maxBytes, lang) } }]
  return []
}

function optionProblems(form: CompareForm): FormProblem[] {
  const problems: FormProblem[] = []
  const threshold = form.threshold
  if (!Number.isInteger(threshold) || threshold < MIN_THRESHOLD || threshold > MAX_THRESHOLD) {
    problems.push({ key: 'problem_threshold', field: 'threshold' })
  }
  if (form.sections.length === 0) problems.push({ key: 'problem_sections', field: 'sections' })
  if (form.title.trim().length > MAX_TITLE) problems.push({ key: 'problem_title', field: 'title' })
  return problems
}

/** Alle Befunde in Formularreihenfolge; leer heißt: absendbar. */
export function formProblems(form: CompareForm, maxBytes = DEFAULT_MAX_UPLOAD_BYTES, lang = 'de'): FormProblem[] {
  return [
    ...fileProblems(form.oldFile, 'oldFile', maxBytes, lang),
    ...fileProblems(form.newFile, 'newFile', maxBytes, lang),
    ...optionProblems(form),
  ]
}

/** PDF-Dateien vergleicht der Server immer als Fließtext. */
export function involvesPdf(form: CompareForm): boolean {
  return [form.oldFile, form.newFile].some((file) => file?.name.toLowerCase().endsWith('.pdf'))
}

/** Formularfelder für `POST /comparisons`; Gesetzessynopse ohne die Optionen des Standardvergleichs. */
export function toCompareFields(form: CompareForm): CompareFields {
  const sections = ROW_STATUSES.filter((status) => form.sections.includes(status))
  const common: CompareFields = {
    comparison_type: form.kind,
    highlight_words: form.highlightWords,
    output_sections: sections,
    ...(form.title.trim() ? { title: form.title.trim() } : {}),
    ...(form.profile ? { profile: form.profile } : {}),
  }
  if (form.kind === 'article_law') return common
  return {
    ...common,
    mode: form.mode,
    threshold: form.threshold,
    include_answers: form.includeAnswers,
    include_notes: form.includeNotes,
    include_editorial: form.includeEditorial,
  }
}

/** Abschnitt ein- oder ausschalten; Reihenfolge wie `ROW_STATUSES`. */
export function toggleSection(sections: readonly RowStatus[], status: RowStatus, enabled: boolean): RowStatus[] {
  const next = new Set(sections)
  if (enabled) next.add(status)
  else next.delete(status)
  return ROW_STATUSES.filter((entry) => next.has(entry))
}

/** Standardprofil des Servers (`default: true`), sonst das erste. */
export function defaultProfile(profiles: readonly ComparisonProfile[]): ComparisonProfile | null {
  return profiles.find((profile) => profile.default) ?? profiles[0] ?? null
}
