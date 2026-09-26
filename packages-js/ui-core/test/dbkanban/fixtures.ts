import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { vi } from 'vitest'
import { createMemoryRecordPort, type RecordPort, type RecordTable } from '@auditcore/kanban-core'
import { dbKanbanMessages, type DbKanbanTranslate } from '../../src/dbkanban/messages'
import { translate } from '../../src/i18n'

/**
 * Tabelle der gemeinsamen Paritätsfixture `group.json` (erzeugt von
 * auditcore_kanban/tools/build_parity_fixtures.py, Form der audit_designer-Datenbank).
 */
// Pfad ohne `new URL`: unter happy-dom ist `URL` die Browserfassung.
const path = resolve(dirname(fileURLToPath(import.meta.url)), '../../../../packages/auditcore_kanban/tests/fixtures/parity/group.json')
const cases = JSON.parse(readFileSync(path, 'utf8')) as Array<{ input: { table: RecordTable } }>
export const recordTable: RecordTable = (cases[0] as { input: { table: RecordTable } }).input.table
export const t: DbKanbanTranslate = (key, params) => translate(dbKanbanMessages, 'de', key, params)

/** Speicherport mit beobachtbaren Aufrufen; einzelne Methoden lassen sich ersetzen. */
export function recordPort(overrides: Partial<RecordPort> = {}, table: RecordTable = recordTable) {
  let id = 0
  const memory = createMemoryRecordPort(table, { newId: () => `neu-${++id}`, clock: () => '2026-09-26T10:00:00Z' })
  const port = {
    load: vi.fn(() => memory.load()),
    updateCell: vi.fn(memory.updateCell),
    addRow: vi.fn(memory.addRow as NonNullable<RecordPort['addRow']>),
  }
  return Object.assign(port, overrides)
}
