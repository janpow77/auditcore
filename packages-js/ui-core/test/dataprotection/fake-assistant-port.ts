import { vi } from 'vitest'
import type { AssistantPort, WorkspaceOverview } from '../../src/dataprotection/assistantTypes'
import fixture from '../fixtures/dataprotection-assistant.json'

/** Antworten des echten Python-Backends (demo/dataprotection_assistant_demo.py). */
export const activityId = fixture.activity_id
export const fresh = fixture.fresh as unknown as WorkspaceOverview
export const suggested = fixture.suggested as unknown as WorkspaceOverview
export const free = fixture.free as unknown as WorkspaceOverview
export const table = fixture.table as unknown as WorkspaceOverview
export const providers = fixture.providers as unknown as WorkspaceOverview
export const consultation = fixture.consultation as unknown as WorkspaceOverview

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export function fakeAssistantPort(start: WorkspaceOverview = fresh, overrides: Partial<AssistantPort> = {}) {
  const port = {
    workspace: vi.fn(async () => clone(start)),
    answer: vi.fn(async () => clone(suggested)),
    confirm: vi.fn(async () => clone(fresh)),
    navigate: vi.fn(async () => clone(free)),
    checklist: vi.fn(async () => clone(start)),
    ...overrides,
  }
  return port satisfies AssistantPort
}
