// Zustandsautomat von <flowaudit-risk-flags> (Vue und React): Filter,
// Datensatzauswahl und nachgeladene Profilbeschreibung; alles Übrige sind
// reine Selektoren über der Auswertung.

import type { TableColumn, TableRow } from '@flowaudit/common'
import type { Translate } from '../i18n'
import { createStore } from '../store'
import type { RiskMessageKey } from './messages'
import type { RiskPort } from './port'
import { statusHintKey, statusKey } from './labels'
import {
  DEFAULT_FILTER,
  distribution,
  filterRecords,
  flagState,
  recordEntries,
  recordLabel,
  recordRules,
  totals,
  triggeredDataset,
  type FlagEntry,
  type RiskDistributionRow,
  type RiskFilter,
  type Totals,
} from './state'
import type { DatasetFinding, Evaluation, ProfileDetail, ProfileReference, RecordView, RuleView } from './types'

export type RiskTranslate = Translate<RiskMessageKey>

/** Eingaben der Gesamtansicht (Props). */
export interface RiskInputs {
  evaluation?: Evaluation | null
  profile?: ProfileDetail | null
  port?: RiskPort | null
}

export interface RiskData {
  filter: RiskFilter
  selectedIndex: number | null
  /** Übergebene oder über den Port nachgeladene Profilbeschreibung. */
  profile: ProfileDetail | null
  profileError: string
}

/** Alles, was die Gesamtansicht aus Stand und Auswertung anzeigt (reine Funktion). */
export interface RiskSelection {
  rules: RuleView[]
  codes: string[]
  rows: RiskDistributionRow[]
  totals: Totals
  dataset: DatasetFinding[]
  records: RecordView[]
  tableColumns: TableColumn[]
  tableRows: TableRow[]
  selected: RecordView | null
  entries: FlagEntry[]
}

export const EMPTY_EVALUATION: Evaluation = {
  library: '', profile: { id: '', version: '', fingerprint: '', status: '' }, records: [], dataset: [], skipped: {}, summary: [],
}

export function riskTableColumns(rules: readonly RuleView[], recordText: string): TableColumn[] {
  return [
    { key: 'record', label: recordText, sortable: true },
    ...rules.map((rule) => ({ key: rule.code, label: rule.code, sortable: true, align: 'center' as const })),
  ]
}

export function riskTableRows(evaluation: Evaluation, records: readonly RecordView[], rules: readonly RuleView[]): TableRow[] {
  return records.map((record) => {
    const row: Record<string, unknown> = { id: record.index, record: recordLabel(record) }
    for (const rule of rules) row[rule.code] = flagState(record, rule.code, evaluation.skipped)
    return row
  })
}

export function selectRisk(state: Pick<RiskData, 'filter' | 'selectedIndex'>, given: Evaluation | null | undefined, recordText: string): RiskSelection {
  const evaluation = given ?? EMPTY_EVALUATION
  const rules = recordRules(evaluation)
  const records = filterRecords(evaluation, state.filter)
  const selected = evaluation.records.find((record) => record.index === state.selectedIndex) ?? null
  return {
    rules,
    codes: rules.map((rule) => rule.code),
    rows: distribution(evaluation),
    totals: totals(evaluation),
    dataset: triggeredDataset(evaluation),
    records,
    tableColumns: riskTableColumns(rules, recordText),
    tableRows: riskTableRows(evaluation, records, rules),
    selected,
    entries: selected ? recordEntries(selected, rules) : [],
  }
}

/** Sichtbarer Profilstatus („freigegeben“ …) oder der Rohwert. */
export function profileStatusText(profile: ProfileReference | null | undefined, t: RiskTranslate): string {
  const key = profile ? statusKey(profile.status) : null
  return key ? t(key) : (profile?.status ?? '')
}

/** Warnhinweis für nicht freigegebene Profile, sonst leer. */
export function profileHintText(profile: ProfileReference | null | undefined, t: RiskTranslate): string {
  const key = profile ? statusHintKey(profile.status) : null
  return key ? t(key) : ''
}

function errorText(failure: unknown): string {
  return failure instanceof Error ? failure.message : String(failure)
}

export function createRiskController() {
  const store = createStore<RiskData>({ filter: { ...DEFAULT_FILTER }, selectedIndex: null, profile: null, profileError: '' })

  /**
   * Profilbeschreibung: die übergebene, sonst über den Port nachgeladen
   * (Profil und Version der Auswertung, nie ein Standardprofil). Ein Ergebnis
   * zählt nur, wenn die aktuelle Auswertung noch denselben Fingerabdruck hat.
   */
  async function loadProfile(inputs: RiskInputs, latest: () => RiskInputs): Promise<void> {
    const reference = inputs.evaluation?.profile
    store.set({ profileError: '', profile: inputs.profile ?? null })
    if (inputs.profile || !inputs.port || !reference?.id) return
    try {
      const loaded = await inputs.port.profile(reference.id, reference.version)
      if (latest().evaluation?.profile.fingerprint === reference.fingerprint) store.set({ profile: loaded })
    } catch (failure) {
      store.set({ profileError: errorText(failure) })
    }
  }

  return {
    store,
    loadProfile,
    setFilter: (filter: RiskFilter) => store.set({ filter }),
    /** Klick auf einen Code der Verteilung: nach diesem Merkmal filtern (Treffer oder unbestimmt). */
    selectCode: (code: string) => store.set((state) => ({ filter: { ...state.filter, code, state: 'affected' } })),
    /** Datensatz wählen; erneuter Klick hebt die Auswahl auf. Liefert die neue Auswahl. */
    toggleRecord(index: number): number | null {
      const next = store.get().selectedIndex === index ? null : index
      store.set({ selectedIndex: next })
      return next
    },
    select: (index: number | null) => store.set({ selectedIndex: index }),
    /** Neue Auswertung: Auswahl aufheben. */
    resetSelection: () => store.set({ selectedIndex: null }),
  }
}

export type RiskController = ReturnType<typeof createRiskController>
