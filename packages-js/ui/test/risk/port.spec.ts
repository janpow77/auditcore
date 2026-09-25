import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { RestError, RiskFlags, createRiskRestPort, type Evaluation, type ProfileDetail, type RiskPort } from '../../src'
import profileJson from './fixtures/profile-year-bound.json'
import yearBoundJson from './fixtures/evaluation-year-bound.json'

const evaluation = yearBoundJson as unknown as Evaluation
const profile = profileJson as unknown as ProfileDetail

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

describe('createRiskRestPort', () => {
  it('ruft die Pfade des REST-Vertrags auf', async () => {
    const fetch = vi.fn(async (input: string, _init?: RequestInit) => {
      if (input.endsWith('/profiles')) return json({ profiles: [{ id: 'a', version: '1' }] })
      if (input.endsWith('/check-columns')) return json({ complete: true, rules: [] })
      if (input.endsWith('/evaluate')) return json(evaluation)
      return json(profile)
    })
    const port = createRiskRestPort({ baseUrl: '/api/risk/', fetch })
    expect(await port.profiles()).toEqual([{ id: 'a', version: '1' }])
    await port.profile('riskanalysis.year_bound', '2026.09.5')
    await port.checkColumns('riskanalysis.year_bound', '2026.09.5', ['bruttobetrag'])
    await port.evaluate({ profile: { id: 'riskanalysis.year_bound', version: '2026.09.5' }, records: [] })
    const calls = fetch.mock.calls.map(([url]) => url)
    expect(calls).toEqual([
      '/api/risk/profiles',
      '/api/risk/profiles/riskanalysis.year_bound/2026.09.5',
      '/api/risk/profiles/riskanalysis.year_bound/2026.09.5/check-columns',
      '/api/risk/evaluate',
    ])
    const init = fetch.mock.calls[2]?.[1]
    expect(JSON.parse(String(init?.body))).toEqual({ columns: ['bruttobetrag'] })
  })

  it('reicht Fehler des Servers als RestError weiter', async () => {
    const fetch = vi.fn(async () => json({ error: { code: 'profile_not_found', message: 'Profil unbekannt' } }, 404))
    const port = createRiskRestPort({ baseUrl: '/risk', fetch })
    await expect(port.profile('x', '1')).rejects.toEqual(new RestError('Profil unbekannt', 404, 'profile_not_found'))
  })
})

describe('RiskFlags mit Port', () => {
  it('lädt die Profilbeschreibung der Auswertung nach', async () => {
    const port = { profile: vi.fn(async () => profile) } as unknown as RiskPort
    const wrapper = mount(RiskFlags, { props: { evaluation, port } })
    await flushPromises()
    expect(port.profile).toHaveBeenCalledWith('riskanalysis.year_bound', '2026.09.5')
    expect(wrapper.text()).toContain('Profil und Eingabefelder')
  })

  it('zeigt einen Ladefehler an', async () => {
    const port = { profile: vi.fn(async () => { throw new Error('Netzwerkfehler') }) } as unknown as RiskPort
    const wrapper = mount(RiskFlags, { props: { evaluation, port } })
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toBe('Netzwerkfehler')
  })
})
