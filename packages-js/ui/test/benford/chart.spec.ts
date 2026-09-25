import { describe, expect, it } from 'vitest'
import { axisMaximum, chartGeometry, DEFAULT_BOX } from '../../src/benford/chart'
import { buildAnalyseRequest, levelTone, needsShortValues } from '../../src/benford/model'
import type { BenfordAnalysis, BenfordCatalogue } from '../../src/benford/types'
import analysisJson from '../fixtures/benford-analysis.json'
import profilesJson from '../fixtures/benford-profiles.json'

const analysis = analysisJson as unknown as BenfordAnalysis
const catalogue = profilesJson as unknown as BenfordCatalogue

describe('Benford-Diagramm', () => {
  it('wählt eine runde Achsenobergrenze', () => {
    const axis = axisMaximum(0.301)
    expect(axis.step).toBe(0.1)
    expect(axis.top).toBeCloseTo(0.4)
    expect(axisMaximum(0.04)).toMatchObject({ step: 0.01 })
  })

  it('zeichnet je Ziffer einen Balken im Plotbereich und markiert Überschreitungen', () => {
    const geometry = chartGeometry(analysis.conformity.rows)
    expect(geometry.bars).toHaveLength(9)
    const bottom = DEFAULT_BOX.height - DEFAULT_BOX.bottom
    for (const bar of geometry.bars) {
      expect(bar.y + bar.height).toBeCloseTo(bottom)
      expect(bar.x).toBeGreaterThanOrEqual(DEFAULT_BOX.left)
    }
    expect(geometry.bars.filter((bar) => bar.exceeds).map((bar) => bar.digit)).toEqual(analysis.conformity.exceeding_digits)
    expect(geometry.expectedPath.startsWith('M')).toBe(true)
    expect(geometry.xLabels).toHaveLength(9)
  })

  it('beschriftet bei 90 Gruppen nur jede zehnte Ziffer', () => {
    const rows = Array.from({ length: 90 }, (_, index) => ({
      digit: index + 10, observed_count: 1, observed_share: 0.01, expected_share: Math.log10(1 + 1 / (index + 10)), deviation: 0, z: 0, exceeds: false,
    }))
    expect(chartGeometry(rows).xLabels.map((label) => label.digit)).toEqual([10, 20, 30, 40, 50, 60, 70, 80, 90])
  })
})

describe('Benford-Anfrage', () => {
  const base = { catalogue, test: 'first' as const, profile: 'nigrini.2012', shortValues: null, values: [1, 2] }

  it('verlangt Test, Profil und für zweistellige Tests die Regel für kurze Werte', () => {
    expect(buildAnalyseRequest(base)).toEqual({ ok: true, request: { test: 'first', profile: 'nigrini.2012', values: [1, 2] } })
    expect(buildAnalyseRequest({ ...base, test: 'second' })).toEqual({ ok: false, error: 'shortValues' })
    expect(buildAnalyseRequest({ ...base, test: 'second', shortValues: 'pad' })).toMatchObject({ ok: true, request: { short_values: 'pad' } })
    expect(buildAnalyseRequest({ ...base, profile: null })).toEqual({ ok: false, error: 'profile' })
    expect(buildAnalyseRequest({ ...base, values: [] })).toEqual({ ok: false, error: 'noValues' })
    expect(needsShortValues(catalogue, 'first_two')).toBe(true)
    expect([0, 1, 2, 3, 9].map(levelTone)).toEqual(['success', 'accent', 'warning', 'danger', 'danger'])
  })
})
