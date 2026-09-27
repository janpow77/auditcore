import { describe, expect, it } from 'vitest'
import {
  createExtrapolationController,
  detailWarnings,
  extrapolationDesignChoices,
  extrapolationMessages,
  groupRows,
  hasExtrapolationDetails,
  periodRows,
  recalculationView,
  subsampleEditorView,
  subsampleResultRows,
  systemAssessmentChoices,
  translator,
  type EvaluationRequest,
  type ExtrapolationForm,
  type StratumInput,
  type UnitInput,
} from '../../src'
import { evaluationResult, extrapolationCatalogue, fakeExtrapolationPort, groupsFixture, groupsResult, multistageFixture, periodsFixture, periodsResult } from './fake-port'

const t = translator(extrapolationMessages, 'de')

function controller(strata: readonly StratumInput[], units: readonly UnitInput[], port = fakeExtrapolationPort()) {
  const created = createExtrapolationController({ port: () => port, strata: () => strata, units: () => units, format: (value) => String(value) })
  return { created, port }
}

describe('Aufbau der Stichprobe (Leitfaden Kap. 6/7)', () => {
  it('übernimmt Zeiträume und Teilstichprobe und baut dieselbe Anfrage wie das Backend-Beispiel', async () => {
    const { created, port } = controller(periodsFixture.strata, periodsFixture.units)
    await created.load()
    expect(created.store.get().form.design).toBe('periods')
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    created.setSystemAssessment('3')
    await created.evaluate()
    const sent = port.calls.evaluate[0]
    if (!sent) throw new Error('keine Anfrage')
    expect(sent.periods).toEqual(periodsFixture.periods)
    expect(sent.system_assessment).toBe(3)
    expect(sent.units.map((unit) => unit.period)).toEqual(periodsFixture.units.map((unit) => unit.period))
    const [first] = sent.units
    const [expected] = periodsFixture.units
    expect(first?.subsample?.strata).toEqual(expected?.subsample?.strata)
    const shape = (unit: { id: string; stratum: string; book_value: number }) => [unit.id, unit.stratum, unit.book_value]
    expect(first?.subsample?.units.map(shape)).toEqual(expected?.subsample?.units.map(shape))
    expect(first).not.toHaveProperty('random_error')
    expect(created.store.get().result?.design).toBe('periods')
  })

  it('lehnt Zeiträume für den konservativen Ansatz ab und prüft Schichtnamen je Zeitraum', async () => {
    const { created } = controller(periodsFixture.strata, periodsFixture.units)
    await created.load()
    created.selectMethod('mus.conservative')
    created.setConfidence(0.9)
    await created.evaluate()
    expect(created.store.get().formError).toBe('periods')
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    created.updateStratum(1, { part: '1. Halbjahr' })
    await created.evaluate()
    expect(created.store.get().issues['strata.1.name']).toBe('duplicate')
  })

  it('legt Teilstichproben an, bearbeitet und entfernt sie', async () => {
    const { created } = controller(periodsFixture.strata, periodsFixture.units)
    await created.load()
    created.toggleSubsample(1)
    expect(created.store.get().subsampleUnit).toBe(1)
    created.addSubItem()
    created.updateSubItem(0, { id: 'R-9', bookValue: '100' })
    created.updateSubsample({ estimator: 'mean_per_unit' })
    const rows = created.store.get().form.units[1]?.subsample
    expect(rows?.items).toHaveLength(2)
    expect(rows?.estimator).toBe('mean_per_unit')
    created.removeSubItem(1)
    expect(created.store.get().form.units[1]?.subsample?.items).toHaveLength(1)
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    await created.evaluate()
    expect(created.store.get().issues['units.1.subsample.populationSize']).toBe('required')
    created.toggleSubsample(1)
    expect(created.store.get().form.units[1]?.subsample).toBeNull()
    expect(created.store.get().subsampleUnit).toBeNull()
  })

  it('schickt Gruppen und verlangt einen Programmnamen je Schicht', async () => {
    const { created, port } = controller(groupsFixture.strata, groupsFixture.units)
    await created.load()
    expect(created.store.get().form.design).toBe('groups')
    created.selectMethod('srs.mean_per_unit')
    created.setConfidence(0.8)
    await created.evaluate()
    expect(port.calls.evaluate[0]?.strata.map((stratum) => stratum.group)).toEqual(['Programm 1', 'Programm 2'])
    created.updateStratum(0, { part: ' ' })
    await created.evaluate()
    expect(created.store.get().issues['strata.0.part']).toBe('required')
  })
})

describe('Anzeige der Ergänzungen', () => {
  it('Zeiträume, Teilstichprobe und Neuberechnung', () => {
    expect(periodRows(periodsResult)).toHaveLength(2)
    expect(subsampleResultRows(periodsResult, t)).toHaveLength(1)
    const view = recalculationView(periodsResult, t, 'de')
    expect(view?.metrics.map((metric) => metric.id)).toEqual(['recalc-level', 'recalc-z', 'recalc-required'])
    expect(view?.verdict).toBe(t('recalcNotSupported'))
    expect(hasExtrapolationDetails(periodsResult)).toBe(true)
    expect(hasExtrapolationDetails({ ...evaluationResult, confidence_recalculation: undefined })).toBe(false)
  })

  it('Programme der Gruppe und Auswahllisten', () => {
    expect(groupRows(groupsResult, extrapolationCatalogue).map((row) => row.name)).toEqual(['Programm 1', 'Programm 2'])
    expect(detailWarnings(groupsResult).length).toBeGreaterThan(0)
    expect(extrapolationDesignChoices(extrapolationCatalogue, t).map((choice) => choice.id)).toEqual(['single', 'periods', 'groups'])
    expect(systemAssessmentChoices(extrapolationCatalogue, 'de')).toHaveLength(4)
  })
})

function expectMultistageForm(form: ExtrapolationForm): void {
  expect(form.design).toBe('periods')
  expect(form.strata.map((row) => row.group)).toEqual(['Programm 1', 'Programm 2', 'Programm 1', 'Programm 2'])
  const first = form.units[0]?.subsample
  if (!first) throw new Error('keine Teilstichprobe')
  expect(first.strata).toHaveLength(2)
  expect(first.items[1]?.subsample?.items).toHaveLength(4)
}

function expectMultistageRequest(sent: EvaluationRequest | undefined): void {
  const expected = multistageFixture.units[0]?.subsample
  const sub = sent?.units[0]?.subsample
  if (!sent || !sub || !expected) throw new Error('keine Anfrage')
  expect(sent.strata.map((stratum) => stratum.group)).toEqual(multistageFixture.strata.map((stratum) => stratum.group))
  expect(sub.strata).toEqual(expected.strata)
  const nested = sub.units[1]?.subsample
  expect(nested?.strata).toEqual(expected.units[1]?.subsample?.strata)
  expect(nested?.units).toHaveLength(4)
}

describe('Mehrstufige Teilstichproben und Programme über Zeiträume', () => {
  it('übernimmt Teilschichten, dritte Stufe und Programme und baut dieselbe Anfrage', async () => {
    const { created, port } = controller(multistageFixture.strata, multistageFixture.units)
    await created.load()
    expectMultistageForm(created.store.get().form)
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    await created.evaluate()
    expectMultistageRequest(port.calls.evaluate[0])
    expect(created.store.get().result?.groups).toHaveLength(2)
  })

  it('bearbeitet Teilschichten und die Teilstichprobe einer Teileinheit', async () => {
    const { created } = controller(multistageFixture.strata, multistageFixture.units)
    await created.load()
    created.editSubsample(0)
    created.editNestedSubsample(1)
    expect(subsampleEditorView(created.store.get(), t)?.nested).toBe(true)
    created.addSubItem()
    expect(created.store.get().form.units[0]?.subsample?.items[1]?.subsample?.items).toHaveLength(5)
    created.editNestedSubsample(null)
    created.addSubStratum()
    created.updateSubStratum(2, { name: 'Neu', bookValue: '1' })
    created.selectMethod('mus.standard')
    created.setConfidence(0.9)
    await created.evaluate()
    const issues = created.store.get().issues
    expect(issues['units.0.subsample.strata']).toBe('range')
    expect(issues['units.0.subsample.items.1.subsample.items.4.id']).toBe('required')
    created.toggleNestedSubsample(1)
    expect(created.store.get().form.units[0]?.subsample?.items[1]?.subsample).toBeNull()
    created.updateStratum(0, { group: '' })
    await created.evaluate()
    expect(created.store.get().issues['strata.0.group']).toBe('required')
  })
})
