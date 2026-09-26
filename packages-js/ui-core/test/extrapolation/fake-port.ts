/**
 * Port mit den Antworten des echten Python-Backends (Fixtures von
 * auditcore_extrapolation.web, erzeugt mit tools/ui_fixtures.py, synthetische
 * Daten). `calls` hält die Anfragen fest; `failing` lässt eine Methode scheitern.
 */
import type { EvaluationRequest, EvaluationResult, ExtrapolationCatalogue, ExtrapolationPort, ResidualRequest, ResidualResult, StratumInput, UnitInput } from '../../src'
import evaluation from '../fixtures/extrapolation-evaluation.json'
import profiles from '../fixtures/extrapolation-profiles.json'
import request from '../fixtures/extrapolation-request.json'
import residual from '../fixtures/extrapolation-residual.json'

export const extrapolationCatalogue = profiles as unknown as ExtrapolationCatalogue
export const evaluationResult = evaluation as unknown as EvaluationResult
export const residualResult = residual as unknown as ResidualResult
export const fixtureRequest = request as unknown as EvaluationRequest
export const fixtureStrata: readonly StratumInput[] = fixtureRequest.strata
export const fixtureUnits: readonly UnitInput[] = fixtureRequest.units

export interface ExtrapolationFake extends ExtrapolationPort {
  calls: { evaluate: EvaluationRequest[]; residual: ResidualRequest[]; export: [EvaluationRequest, string][] }
}

export function fakeExtrapolationPort(failing?: keyof ExtrapolationPort, message = 'Konfidenzniveau 85.00% ist in Tabelle 3 des Leitfadens nicht enthalten'): ExtrapolationFake {
  const calls: ExtrapolationFake['calls'] = { evaluate: [], residual: [], export: [] }
  const fail = (name: keyof ExtrapolationPort): void => {
    if (failing === name) throw new Error(message)
  }
  return {
    calls,
    profiles: async () => (fail('profiles'), extrapolationCatalogue),
    evaluate: async (body) => (fail('evaluate'), calls.evaluate.push(body), evaluationResult),
    residual: async (body) => (fail('residual'), calls.residual.push(body), residualResult),
    exportEvaluation: async (body, format) => (calls.export.push([body, format]), { blob: new Blob(['x']), filename: `hochrechnung.${format}`, mediaType: 'text/csv' }),
  }
}
