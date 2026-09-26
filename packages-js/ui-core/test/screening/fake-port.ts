import { vi } from 'vitest'
import type { HitView, LogView, RunView, ScreeningPort, SettingsView, SourcesView } from '../../src'
import fixture from '../fixtures/screening-contract.json'

// Antworten des echten Python-Dienstes (auditcore_registry_sources.web), nur synthetische Personen.
export const run = fixture.run as unknown as RunView
export const pepRun = fixture.pep_run as unknown as RunView
export const settings = fixture.settings as unknown as SettingsView
export const sources = fixture.sources as unknown as SourcesView
export const log = fixture.log as unknown as LogView
export const firstSubject = run.subjects[0]!
export const secondHit = firstSubject.hits[1]!

/** Port mit den Fixture-Antworten; `decide`/`secondReview` liefern den zweiten Treffer als verworfen. */
export function fakePort(overrides: Partial<ScreeningPort> = {}) {
  const decided: HitView = { ...secondHit, review: { ...secondHit.review, status: 'dismissed', status_label: 'verworfen' } }
  return {
    settings: vi.fn(async () => settings),
    sources: vi.fn(async () => sources),
    runs: vi.fn(async () => ({ contract: run.contract, runs: [run] })),
    createRun: vi.fn(async () => run),
    run: vi.fn(async () => run),
    log: vi.fn(async () => log),
    decide: vi.fn(async () => decided),
    secondReview: vi.fn(async () => decided),
    ...overrides,
  } satisfies ScreeningPort
}
