import { vi } from 'vitest'
import type {
  AssessmentView,
  DataProtectionPort,
  DataProtectionProfile,
  OverviewRow,
  Proposal,
  RegisterState,
  VersionView,
} from '../../src/dataprotection/types'
import fixture from '../fixtures/dataprotection-contract.json'

export const profile = fixture.profile as unknown as DataProtectionProfile
export const register = fixture.register as unknown as RegisterState
export const rows = fixture.overview.items as unknown as OverviewRow[]
export const released = fixture.released_assessment as unknown as AssessmentView
export const draftAssessment = fixture.draft_assessment as unknown as AssessmentView
export const proposal = fixture.proposal as unknown as Proposal

export function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

/** Port mit den Antworten des echten Python-Backends (Fixture aus demo/dataprotection_demo.py). */
export function fakePort(overrides: Partial<DataProtectionPort> = {}) {
  const draft = register.draft as VersionView
  const port = {
    profile: vi.fn(async () => profile),
    register: vi.fn(async () => clone(register)),
    checkRegister: vi.fn(async () => ({ issues: [] })),
    saveDraft: vi.fn(async (content) => ({ ...clone(draft), content, revision: draft.revision + 1 })),
    releaseRegister: vi.fn(async () => ({ ...clone(draft), status: 'freigegeben' as const })),
    exportRegister: vi.fn(async () => ({ blob: new Blob(['x']), filename: 'v.csv', mediaType: 'text/csv' })),
    overview: vi.fn(async () => ({ items: clone(rows) })),
    startAssessment: vi.fn(async () => clone(draftAssessment)),
    assessment: vi.fn(async (id: string) => clone(id === released.id ? released : draftAssessment)),
    calculate: vi.fn(async () => clone(proposal)),
    updateAssessment: vi.fn(async (_id, revision, survey) => ({ ...clone(draftAssessment), ...survey, proposal: clone(proposal), revision: revision + 1 })),
    decide: vi.fn(async (_id, revision, decision) => ({ ...clone(draftAssessment), decision: decision.decision, revision: revision + 1 })),
    requestDpo: vi.fn(async () => clone(draftAssessment)),
    releaseAssessment: vi.fn(async () => clone(released)),
    reassess: vi.fn(async () => clone(draftAssessment)),
    exportAssessment: vi.fn(async () => ({ blob: new Blob(['x']), filename: 'dsfa.html', mediaType: 'text/html' })),
    ...overrides,
  } satisfies DataProtectionPort
  return port
}
