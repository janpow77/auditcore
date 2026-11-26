// Zustand von <flowaudit-pdf-redaction>: Datentyp, Startwerte und reine Prüfungen.
// Öffentlich über controller.ts (ausgewählte Namen), intern für Controller und Vorgaben.

import { IDLE, type RequestState, type Store } from '../store'
import { redactionTerms, REDACTION_GROUP_PAGE } from './model'
import type { RedactionArea, RedactionBox, RedactionCatalogue, RedactionCriteria, RedactionLimits, RedactionPlan, RedactionPort, RedactionResult } from './types'

export type RedactionBusy = 'load' | 'plan' | 'apply'
export type RedactionValidation = 'needFile' | 'tooLarge' | 'needCriteria' | 'tooManyTerms' | 'termTooLong' | null
export type RedactionOption = 'caseSensitive' | 'wholeWord' | 'sanitize'

export interface RedactionCallbacks {
  planned?: (plan: RedactionPlan) => void
  completed?: (result: RedactionResult) => void
  failed?: (message: string) => void
}

/** Erzeugen und Freigeben von Objekt-URLs (Seitenbild, Download); in Tests ersetzbar. */
export interface RedactionUrls {
  create: (blob: Blob) => string
  revoke: (url: string) => void
}

/** Laufendes Aufziehen, Verschieben oder Vergrößern mit dem Zeiger. */
export type RedactionGesture =
  | { kind: 'draw'; start: readonly [number, number]; box: RedactionBox }
  | { kind: 'move'; id: string; from: readonly [number, number]; origin: RedactionBox }
  | { kind: 'resize'; id: string }

export interface RedactionData extends RequestState<string> {
  catalogue: RedactionCatalogue | null
  file: Blob | null
  filename: string
  /** Die Datei stellt die Anwendung bereit (`provideFile`); kein Dateifeld. */
  fileFixed: boolean
  /**
   * Ein Plan zu alten Kriterien ist verworfen (Hinweis im Formular): `presets` durch
   * eine Vorgabe der Anwendung, `edited` durch eine Änderung während der Suche.
   */
  criteriaNotice: 'presets' | 'edited' | null
  patterns: readonly string[]
  terms: string
  caseSensitive: boolean
  wholeWord: boolean
  sanitize: boolean
  validation: RedactionValidation
  plan: RedactionPlan | null
  selected: ReadonlySet<string>
  areas: readonly RedactionArea[]
  page: number
  /** Objekt-URL des Seitenbilds der aktuellen Seite (`null` solange es lädt). */
  preview: string | null
  previewError: string | null
  gesture: RedactionGesture | null
  areaLimitHit: boolean
  filter: string
  expanded: ReadonlySet<string>
  groupLimit: number
  result: RedactionResult | null
  resultUrl: string | null
}

/** Startwerte der Anwendung für Begriffe und Muster (danach frei änderbar). */
export interface RedactionPresets {
  terms?: readonly string[]
  patterns?: readonly string[]
}

export interface RedactionSource {
  port: () => RedactionPort | null | undefined
  callbacks?: () => RedactionCallbacks
  urls?: RedactionUrls
}

export const INITIAL_REDACTION: RedactionData = {
  ...IDLE,
  catalogue: null,
  file: null,
  filename: '',
  fileFixed: false,
  criteriaNotice: null,
  patterns: [],
  terms: '',
  caseSensitive: false,
  wholeWord: true,
  sanitize: true,
  validation: null,
  plan: null,
  selected: new Set(),
  areas: [],
  page: 1,
  preview: null,
  previewError: null,
  gesture: null,
  areaLimitHit: false,
  filter: '',
  expanded: new Set(),
  groupLimit: REDACTION_GROUP_PAGE,
  result: null,
  resultUrl: null,
}

/** Zurück auf die Prüfansicht eines neuen Plans (ohne Datei und Kriterien). */
export const REVIEW_RESET: Partial<RedactionData> = {
  areas: [], page: 1, preview: null, previewError: null, gesture: null, areaLimitHit: false,
  filter: '', expanded: new Set(), groupLimit: REDACTION_GROUP_PAGE, result: null, resultUrl: null, criteriaNotice: null,
}

export function redactionCriteria(state: RedactionData): RedactionCriteria {
  return { patterns: [...state.patterns], terms: redactionTerms(state.terms), case_sensitive: state.caseSensitive, whole_word: state.wholeWord }
}

/** Prüfung vor dem Senden (reine Funktion). */
export function redactionValidation(state: RedactionData): RedactionValidation {
  if (!state.file) return 'needFile'
  const limits = state.catalogue?.limits
  if (limits && state.file.size > limits.max_upload_bytes) return 'tooLarge'
  const terms = redactionTerms(state.terms)
  if (!state.patterns.length && !terms.length) return 'needCriteria'
  return limits ? termValidation(terms, limits) : null
}

function termValidation(terms: readonly string[], limits: RedactionLimits): RedactionValidation {
  if (terms.length > limits.max_terms) return 'tooManyTerms'
  if (terms.some((term) => term.length > limits.max_term_length)) return 'termTooLong'
  return null
}

export function toggled(set: ReadonlySet<string>, ids: Iterable<string>, on: boolean): ReadonlySet<string> {
  const next = new Set(set)
  for (const id of ids) {
    if (on) next.add(id)
    else next.delete(id)
  }
  return next
}

export type RedactionStore = Store<RedactionData>

/** Während des Schwärzens bleibt die Auswahl fest, damit das Ergebnis zur Anzeige passt. */
export const locked = (store: RedactionStore): boolean => store.get().busy === 'apply'
