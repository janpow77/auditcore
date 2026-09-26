import { describe, expect, it } from 'vitest'
import {
  buildSelectionRequest,
  buildSizeRequest,
  fieldValue,
  hasPartialStrata,
  initialTexts,
  itemsFromImport,
  parseInput,
  populationSuggestions,
  strataOf,
} from '../../src/sampling/model'
import type { MethodProfile, SamplingCatalogue } from '../../src/sampling/types'
import profilesJson from '../fixtures/sampling-profiles.json'

const catalogue = profilesJson as unknown as SamplingCatalogue
const mus = catalogue.methods.find((m) => m.id === 'portal.mus_poisson') as MethodProfile
const srs = catalogue.methods.find((m) => m.id === 'portal.srs_normal') as MethodProfile
const spec = (profile: MethodProfile, key: string) => profile.parameters.find((p) => p.key === key)!

describe('Stichprobe: Eingaben', () => {
  it('liest deutsche und englische Schreibweisen', () => {
    expect(parseInput('475.478,94')).toBe(475478.94)
    expect(parseInput('50.000')).toBe(50000)
    expect(parseInput('0.5')).toBe(0.5)
    expect(parseInput('0,5')).toBe(0.5)
  })

  it('rechnet Prozentfelder in Anteile um und prüft Grenzen', () => {
    expect(fieldValue(spec(mus, 'expected_error_rate'), '0,5')).toEqual({ value: 0.005 })
    expect(fieldValue(spec(mus, 'expected_error_rate'), '100')).toEqual({ error: { code: 'range', min: 0, max: 100 } })
    expect(fieldValue(spec(mus, 'materiality'), '0')).toEqual({ error: { code: 'range', min: 0 } })
    expect(fieldValue(spec(srs, 'population_size'), '10,5')).toEqual({ error: { code: 'invalid' } })
    expect(fieldValue(spec(mus, 'materiality'), '')).toEqual({ error: { code: 'required' } })
  })

  it('bildet die Umfangsanfrage nur mit allen Pflichtfeldern', () => {
    const texts = { population_value: '475.478,94', materiality: '50.000', expected_error_rate: '0,5' }
    expect(buildSizeRequest(mus, texts, null)).toEqual({ ok: false, errors: { confidence_level: { code: 'required' } } })
    expect(buildSizeRequest(mus, texts, 0.95)).toEqual({
      ok: true,
      request: { method: 'portal.mus_poisson', population_value: 475478.94, materiality: 50000, expected_error_rate: 0.005, confidence_level: 0.95 },
    })
  })

  it('schlägt Werte vor und übernimmt Profilvorschläge sichtbar', () => {
    expect(populationSuggestions([{ value: 10.555 }, { value: -3 }, { value: null }, { value: 5 }])).toEqual({ population_value: 15.56, population_size: 4 })
    expect(initialTexts(srs, (value) => String(value))).toEqual({ expected_proportion: '50' })
  })
})

describe('Stichprobe: Auswahl', () => {
  const items = [{ id: 'a', value: 10, stratum: 'X' }, { id: 'b', value: 20, stratum: 'Y' }]
  const base = { profile: mus, items, sampleSize: '2', seed: '', variant: 'portal' as const, allocation: 'equal' as const }

  it('lässt den Seed leer, damit der Server ihn erzeugt', () => {
    const result = buildSelectionRequest(base)
    expect(result).toEqual({ ok: true, request: { method: 'mus', items, sample_size: 2, variant: 'portal', allocation: 'equal' } })
    expect(buildSelectionRequest({ ...base, seed: '42' })).toMatchObject({ ok: true, request: { seed: 42 } })
  })

  it('meldet fehlende Angaben', () => {
    expect(buildSelectionRequest({ ...base, items: [] })).toEqual({ ok: false, error: 'noItems' })
    expect(buildSelectionRequest({ ...base, sampleSize: '-1' })).toEqual({ ok: false, error: 'sampleSize' })
    expect(buildSelectionRequest({ ...base, seed: '12a' })).toEqual({ ok: false, error: 'seed' })
    expect(buildSelectionRequest({ ...base, seed: '99999999999999999999' })).toEqual({ ok: false, error: 'seed' })
    expect(buildSelectionRequest({ ...base, variant: null })).toEqual({ ok: false, error: 'variant' })
    expect(buildSelectionRequest({ ...base, allocation: null })).toEqual({ ok: false, error: 'allocation' })
    expect(buildSelectionRequest({ ...base, items: [...items, { id: 'c', value: 1 }] })).toEqual({ ok: false, error: 'partialStrata' })
    expect(buildSelectionRequest({ ...base, profile: srs, variant: null, items: [{ value: 1 }] })).toMatchObject({ ok: true, request: { method: 'srs' } })
  })

  it('zählt Schichten in Reihenfolge und übernimmt Dateispalten', () => {
    expect(strataOf([{ value: 1, stratum: 'B' }, { value: 1, stratum: 'A' }, { value: 2, stratum: 'B' }])).toEqual([
      { stratum: 'B', population: 2 },
      { stratum: 'A', population: 1 },
    ])
    expect(hasPartialStrata([{ value: 1, stratum: 'B' }, { value: 1 }])).toBe(true)
    expect(itemsFromImport({ values: [5, null], ids: ['R-1', ''], strata: ['L1', ''] })).toEqual([
      { id: 'R-1', value: 5, stratum: 'L1' },
      { id: '2', value: null },
    ])
  })
})
