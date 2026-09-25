import { describe, expect, it } from 'vitest'
import {
  DEFAULT_FILTER,
  distribution,
  evaluationRules,
  filterRecords,
  flagState,
  formatValue,
  parameterLabel,
  recordEntries,
  recordLabel,
  recordRules,
  requirementKey,
  severityTone,
  statusHintKey,
  totals,
  triggeredDataset,
  whenMissingKey,
  type Evaluation,
} from '../../src'
import flowstatJson from './fixtures/evaluation-flowstat.json'
import yearBoundJson from './fixtures/evaluation-year-bound.json'

// Echte Antworten von auditcore_risk.web (POST /evaluate), synthetische Belege.
const yearBound = yearBoundJson as unknown as Evaluation
const flowstat = flowstatJson as unknown as Evaluation
const NETTO_FEHLT = 'Nettobetrag fehlt in der Quelle'

function record(evaluation: Evaluation, key: string) {
  const found = evaluation.records.find((item) => item.key === key)
  if (!found) throw new Error(`Datensatz ${key} fehlt`)
  return found
}

describe('Zustand je Datensatz und Regel', () => {
  it('unterscheidet Treffer, kein Merkmal, unbestimmt, übersprungen', () => {
    const b2 = record(yearBound, 'B-002')
    expect(flagState(b2, 'RF02', yearBound.skipped)).toBe('undetermined')
    expect(flagState(b2, 'RF01', yearBound.skipped)).toBe('clear')
    expect(flagState(record(yearBound, 'B-001'), 'RF08', yearBound.skipped)).toBe('hit')
    const fs1 = record(flowstat, 'FS-1')
    expect(flagState(fs1, 'BL_RF03_MISSING_PAYMENT_DATE', flowstat.skipped)).toBe('skipped')
    expect(flagState(fs1, 'UNBEKANNT', flowstat.skipped)).toBe('absent')
  })

  it('leitet Regeln ohne `rules` aus den Datensätzen ab und trennt Datensatzregeln', () => {
    expect(recordRules(yearBound).map((rule) => rule.code)).toEqual(
      ['RF01', 'RF02', 'RF08', 'RF09', 'RF10', 'RF11', 'RF12', 'RF13', 'RF14', 'RF15'])
    expect(recordRules(flowstat).map((rule) => rule.code)).not.toContain('BL_RF10_VENDOR_CONCENTRATION')
    const bare = { ...yearBound, rules: undefined }
    expect(evaluationRules(bare).map((rule) => rule.code)).toContain('RF02')
  })
})

describe('Verteilung', () => {
  it('zählt Treffer, unbestimmte Datensätze mit Begründung und Volumen', () => {
    const rows = distribution(yearBound)
    const rf02 = rows.find((row) => row.code === 'RF02')
    expect(rf02).toMatchObject({ hit: 2, undetermined: 3, total: 12, skipped: null, volume: 146900 })
    expect(rf02?.reasons).toEqual({ [NETTO_FEHLT]: 3 })
    expect((rf02?.hit ?? 0) + (rf02?.clear ?? 0) + (rf02?.undetermined ?? 0)).toBe(12)
    const rf08 = rows.find((row) => row.code === 'RF08')
    expect(rf08?.undetermined).toBe(2)
  })

  it('weist übersprungene Regeln und Datensatzbefunde aus', () => {
    const skipped = distribution(flowstat).find((row) => row.code === 'BL_RF03_MISSING_PAYMENT_DATE')
    expect(skipped?.skipped).toMatch(/^Spalten fehlen/)
    expect(skipped?.hit).toBe(0)
    expect(totals(flowstat).skippedRules).toBe(5)
    expect(triggeredDataset(flowstat).map((finding) => finding.code)).toEqual(['BL_RF10_VENDOR_CONCENTRATION'])
    expect(totals(yearBound)).toEqual({ records: 12, withHits: 8, withUndetermined: 3, skippedRules: 0 })
  })
})

describe('Filter', () => {
  it('zeigt standardmäßig Datensätze mit Treffer oder unbestimmtem Merkmal', () => {
    const keys = filterRecords(yearBound, DEFAULT_FILTER).map(recordLabel)
    expect(keys).not.toContain('B-005')
    expect(keys).toContain('B-002')
  })

  it('filtert nach Code, Zustand und Suchtext', () => {
    const undetermined = filterRecords(yearBound, { code: 'RF08', state: 'undetermined', query: '' })
    expect(undetermined.map(recordLabel)).toEqual(['B-002', 'B-012'])
    expect(filterRecords(yearBound, { code: 'RF13', state: 'hit', query: '' }).map(recordLabel)).toEqual(['B-009'])
    expect(filterRecords(yearBound, { code: null, state: 'clear', query: '' }).map(recordLabel)).toEqual(['B-005', 'B-007'])
    expect(filterRecords(yearBound, { code: null, state: 'all', query: 'b-01' }).map(recordLabel)).toEqual(['B-010', 'B-011', 'B-012'])
    expect(filterRecords(yearBound, { code: null, state: 'all', query: 'glattes vielfaches' }).length).toBe(2)
  })
})

describe('Detaileinträge', () => {
  it('liefert Treffer und unbestimmte Merkmale in Profilreihenfolge mit Eingabewerten', () => {
    const entries = recordEntries(record(yearBound, 'B-012'), recordRules(yearBound))
    expect(entries.map((entry) => [entry.code, entry.state])).toEqual([
      ['RF02', 'undetermined'], ['RF08', 'undetermined'], ['RF11', 'hit']])
    const rf08 = entries[1]
    expect(rf08?.reason).toBe(NETTO_FEHLT)
    expect(rf08?.inputs.nettobetrag).toBeNull()
    expect(rf08?.parameters).toEqual({ amount_gt: 25000 })
    const hit = recordEntries(record(yearBound, 'B-001'), recordRules(yearBound))[0]
    expect(hit?.inputs).toEqual({ bruttobetrag: 40000 })
    expect(hit?.origin.repository).toBe('janpow77/riskanalysis')
  })

  it('nutzt den Index als Beschriftung ohne Schlüssel', () => {
    expect(recordLabel({ ...record(yearBound, 'B-001'), key: null })).toBe('#1')
  })
})

describe('Formate und Beschriftungen', () => {
  it('formatiert Werte deutsch und leer ausdrücklich', () => {
    expect(formatValue(40000.5, 'de', 'leer')).toBe('40.000,5')
    expect(formatValue(null, 'de', 'leer')).toBe('leer')
    expect(formatValue([1000, 5000], 'de', 'leer')).toBe('1.000; 5.000')
    expect(formatValue(true, 'de', 'leer')).toBe('ja')
    expect(formatValue({ a: 1 }, 'de', 'leer')).toBe('{"a":1}')
    expect(formatValue('0=ni', 'de', 'leer')).toBe('0=ni')
  })

  it('beschriftet Parameter, Schwere, Status, Pflicht und fehlende Spalten', () => {
    expect(parameterLabel('amount_gt', 'de')).toBe('Betrag größer als')
    expect(parameterLabel('unbekannt', 'de')).toBe('unbekannt')
    expect(severityTone('HIGH')).toBe('danger')
    expect(severityTone(null)).toBe('neutral')
    expect(statusHintKey('APPROVED')).toBeNull()
    expect(statusHintKey('CANDIDATE_HUMAN_DECISION_REQUIRED')).toBe('statusHintCandidate')
    expect(requirementKey('value_required')).toBe('valueRequired')
    expect(whenMissingKey('undetermined')).toBe('missingUndetermined')
  })
})
