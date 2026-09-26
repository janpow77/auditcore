/**
 * Ports mit den Antworten der echten Python-Backends (Fixtures von
 * auditcore_sampling.web und auditcore_statistics.web, synthetische Belege).
 * `calls` hält die Anfragen fest; `failing` lässt eine Methode scheitern.
 */
import type { BenfordAnalysis, BenfordCatalogue, BenfordPort, PopulationItem, SamplingCatalogue, SamplingPort, SelectionResult, SizeResult } from '../../src'
import analysis from '../fixtures/benford-analysis.json'
import benfordProfiles from '../fixtures/benford-profiles.json'
import samplingProfiles from '../fixtures/sampling-profiles.json'
import selection from '../fixtures/sampling-selection.json'
import size from '../fixtures/sampling-size.json'

export const samplingCatalogue = samplingProfiles as unknown as SamplingCatalogue
export const sizeResult = size as unknown as SizeResult
export const selectionResult = selection as unknown as SelectionResult
export const benfordCatalogue = benfordProfiles as unknown as BenfordCatalogue
export const benfordAnalysis = analysis as unknown as BenfordAnalysis

/** 30 synthetische Belege in zwei Losen (wie in den Vue-Tests). */
export const populationItems: readonly PopulationItem[] = Array.from({ length: 30 }, (_, i) => ({
  id: `B-${i + 1}`,
  value: ((i * 37) % 900) + 10,
  stratum: i % 3 ? 'Los 1' : 'Los 2',
}))

export type SamplingFake = SamplingPort & { calls: Record<'size' | 'selection' | 'export', unknown[]> }

export function fakeSamplingPort(failing?: keyof SamplingPort, message = 'Konfidenzniveau 0.93 ist nicht definiert'): SamplingFake {
  const calls: SamplingFake['calls'] = { size: [], selection: [], export: [] }
  const fail = (name: keyof SamplingPort): void => {
    if (failing === name) throw new Error(message)
  }
  return {
    calls,
    profiles: async () => (fail('profiles'), samplingCatalogue),
    size: async (request) => (fail('size'), calls.size.push(request), sizeResult),
    allocation: async () => {
      throw new Error('nicht benutzt')
    },
    selection: async (request) => (fail('selection'), calls.selection.push(request), selectionResult),
    exportSelection: async (request, format) => (calls.export.push([request, format]), { blob: new Blob(['x']), filename: 'stichprobe.csv', mediaType: 'text/csv' }),
  }
}

export type BenfordFake = BenfordPort & { calls: unknown[] }

export function fakeBenfordPort(failing?: keyof BenfordPort, message = 'Dienst nicht erreichbar'): BenfordFake {
  const calls: unknown[] = []
  return {
    calls,
    profiles: async () => {
      if (failing === 'profiles') throw new Error(message)
      return benfordCatalogue
    },
    analyse: async (request) => {
      if (failing === 'analyse') throw new Error(message)
      calls.push(request)
      return benfordAnalysis
    },
  }
}
