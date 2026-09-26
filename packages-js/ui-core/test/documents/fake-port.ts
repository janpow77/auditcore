import { vi } from 'vitest'
import type { ComparisonsPort } from '../../src/documents/controller'
import { comparisonsMessages, type ComparisonsTranslate } from '../../src/documents/messages'
import { translate } from '../../src/i18n'
import type { Comparison, ComparisonProfile, ComparisonSummary } from '../../src/synopsis/types'
import fixture from '../fixtures/documents-comparisons.json'

/** Antworten des echten Dienstes (`demo/documents_demo.py --fixture`, synthetische Dokumente). */
export const profiles = fixture.profiles.items as ComparisonProfile[]
export const summaries = fixture.list.items as ComparisonSummary[]
export const created = fixture.created as unknown as Comparison
export const imported: Comparison = { ...created, id: fixture.imported.id, title: fixture.imported.title }
export const errors = fixture.errors
export const t: ComparisonsTranslate = (key, params) => translate(comparisonsMessages, 'de', key, params)

export function file(name: string, size = 10): File {
  return new File([new Uint8Array(size)], name)
}

/** Port mit den Antworten des echten Python-Backends; einzelne Methoden lassen sich ersetzen. */
export function fakePort(overrides: Partial<ComparisonsPort> = {}) {
  const port = {
    profiles: vi.fn(async () => profiles),
    list: vi.fn(async () => summaries),
    create: vi.fn(async () => created),
    importResult: vi.fn(async () => imported),
    remove: vi.fn(async () => undefined),
    load: vi.fn(async () => created),
    updateRows: vi.fn(async () => created),
    exportUrl: vi.fn((id: string, format: string) => `/api/synopsis/comparisons/${id}/export?format=${format}`),
  }
  return Object.assign(port, overrides)
}
