import { describe, expect, it } from 'vitest'
import { createExtrapolationRestPort } from '../../src'
import { fixtureRequest } from './fake-port'

describe('createExtrapolationRestPort', () => {
  it('ruft die Endpunkte des Vertrags auf', async () => {
    const seen: [string, RequestInit | undefined][] = []
    const fetch = async (input: string, init?: RequestInit): Promise<Response> => {
      seen.push([input, init])
      const headers: Record<string, string> = input.endsWith('/export') ? { 'Content-Disposition': 'attachment; filename="h.csv"', 'Content-Type': 'text/csv' } : { 'Content-Type': 'application/json' }
      return new Response(input.endsWith('/export') ? 'x' : '{}', { status: 200, headers })
    }
    const port = createExtrapolationRestPort({ baseUrl: '/api/extrapolation/', fetch })
    await port.profiles()
    await port.evaluate(fixtureRequest)
    await port.residual({ audit_population: 1, total_error_rate: 0, ongoing_assessment: 0, other_negative_amounts: 0, financial_corrections: 0, materiality_rate: 0.02 })
    const file = await port.exportEvaluation(fixtureRequest, 'csv')
    expect(seen.map(([url]) => url)).toEqual(['/api/extrapolation/profiles', '/api/extrapolation/evaluate', '/api/extrapolation/residual', '/api/extrapolation/evaluate/export'])
    expect(JSON.parse(String(seen[3]?.[1]?.body))).toMatchObject({ format: 'csv', method: 'mus.standard' })
    expect(file.filename).toBe('h.csv')
  })
})
