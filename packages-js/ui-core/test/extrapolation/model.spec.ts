import { describe, expect, it } from 'vitest'
import {
  buildEvaluationRequest,
  buildResidualRequest,
  emptyStratum,
  emptyUnit,
  readExtrapolationAmount,
  residualFormFrom,
  stratumRows,
  unitRows,
  type ExtrapolationForm,
} from '../../src'
import { evaluationResult, extrapolationCatalogue, fixtureStrata, fixtureUnits } from './fake-port'

const format = (value: number): string => String(value).replace('.', ',')

function form(patch: Partial<ExtrapolationForm> = {}): ExtrapolationForm {
  return {
    methodId: 'mus.standard', confidence: 0.9, profileId: 'kom_2017_tables', sampleSize: '', materiality: '2',
    strata: stratumRows(fixtureStrata, format), units: unitRows(fixtureUnits, format), ...patch,
  }
}

describe('Formularlogik der Hochrechnung', () => {
  it('liest deutsche und englische Zahlen, leere Fehlerfelder sind 0', () => {
    expect(readExtrapolationAmount('1.234,5')).toBe(1234.5)
    expect(readExtrapolationAmount('')).toBe(0)
    expect(readExtrapolationAmount('', { required: true })).toBe('required')
    expect(readExtrapolationAmount('abc')).toBe('invalid')
    expect(readExtrapolationAmount('-1')).toBe('range')
    expect(readExtrapolationAmount('3', { max: 2 })).toBe('range')
    expect(readExtrapolationAmount('2,5', { integer: true })).toBe('invalid')
  })

  it('baut die Anfrage aus den Zeilen (Wesentlichkeit in Prozent → Anteil)', () => {
    const checked = buildEvaluationRequest(extrapolationCatalogue, form())
    expect(checked.ok).toBe(true)
    if (!checked.ok) return
    expect(checked.request.method).toBe('mus.standard')
    expect(checked.request.materiality_rate).toBe(0.02)
    expect(checked.request.confidence_level).toBe(0.9)
    expect(checked.request.strata).toEqual([{ name: 'Programm', book_value: 1_000_000, systemic_error: 2000 }])
    expect(checked.request.units[3]).toMatchObject({ id: 'V-04', anomalous_error: 800, anomalous_reason: 'Einmaliger Übertragungsfehler', anomalous_corrected: true })
    expect(checked.request.units[4]).toMatchObject({ id: 'V-05', exhaustive: true, random_error: 4000 })
  })

  it('verlangt Methode, Konfidenzniveau und Profil nur für statistische Verfahren', () => {
    expect(buildEvaluationRequest(extrapolationCatalogue, form({ methodId: '' }))).toEqual({ ok: false, error: 'method', issues: {} })
    expect(buildEvaluationRequest(extrapolationCatalogue, form({ confidence: null }))).toMatchObject({ error: 'confidence' })
    const nonStatistical = buildEvaluationRequest(extrapolationCatalogue, form({ methodId: 'nonstatistical.pps', confidence: null }))
    expect(nonStatistical).toMatchObject({ ok: false, issues: { 'strata.0.populationSize': 'required' } })
  })

  it('meldet Feldbefunde mit Zeilenschlüssel', () => {
    const units = [{ ...emptyUnit('x', 'fremd'), id: '', bookValue: '0', anomalous: '5' }]
    const strata = [emptyStratum('a'), { ...emptyStratum('b'), name: 'B', bookValue: '10' }, { ...emptyStratum('c'), name: 'B', bookValue: '10' }]
    const checked = buildEvaluationRequest(extrapolationCatalogue, form({ strata, units, materiality: '3' }))
    expect(checked).toEqual({
      ok: false,
      error: null,
      issues: {
        'strata.0.name': 'required', 'strata.0.bookValue': 'required', 'strata.2.name': 'duplicate',
        'units.0.id': 'required', 'units.0.stratum': 'stratum', 'units.0.reason': 'reason', 'units.0.bookValue': 'range', materiality: 'range',
      },
    })
  })

  it('konservativer Ansatz verlangt n', () => {
    const checked = buildEvaluationRequest(extrapolationCatalogue, form({ methodId: 'mus.conservative' }))
    expect(checked).toMatchObject({ ok: false, issues: { sampleSize: 'required' } })
    const ok = buildEvaluationRequest(extrapolationCatalogue, form({ methodId: 'mus.conservative', sampleSize: '40' }))
    expect(ok.ok && ok.request.sample_size).toBe(40)
  })

  it('RER-Formular übernimmt A und D aus der Auswertung, D in Prozent', () => {
    const residual = residualFormFrom(evaluationResult, { auditPopulation: '', terRate: '', ongoing: '5', otherNegative: '', corrections: '' }, format)
    expect(residual).toEqual({ auditPopulation: '1000000', terRate: '1,6', ongoing: '5', otherNegative: '', corrections: '' })
    const checked = buildResidualRequest({ ...residual, corrections: '3.000' }, 0.02)
    expect(checked).toEqual({
      ok: true,
      request: { audit_population: 1_000_000, total_error_rate: 0.016, ongoing_assessment: 5, other_negative_amounts: 0, financial_corrections: 3000, materiality_rate: 0.02 },
    })
    expect(buildResidualRequest({ ...residual, terRate: '' }, 0.02)).toEqual({ ok: false, issues: { terRate: 'required' } })
  })
})
