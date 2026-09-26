import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it, vi } from 'vitest'
import {
  createMemoryRecordPort,
  dropValue,
  groupableProperties,
  groupOf,
  groupRecords,
  matchesRecord,
  neighbourGroup,
  withCell,
  withRow,
  type RecordTable,
} from '../src'

interface GroupCase {
  name: string
  input: { table: RecordTable; group_by: string }
  expected: [string, string[]][]
}

const DIR = process.env.KANBAN_PARITY_DIR ?? fileURLToPath(new URL('../../../packages/auditcore_kanban/tests/fixtures/parity/', import.meta.url))
const cases = JSON.parse(readFileSync(`${DIR.replace(/\/?$/, '/')}group.json`, 'utf8')) as GroupCase[]
const table = (cases[0] as GroupCase).input.table

describe('Datenbankansicht – Parität mit group_by_value (Python)', () => {
  for (const entry of cases) {
    it(entry.name, () => {
      const groups = groupRecords(entry.input.table, entry.input.group_by)
      expect(groups.map((group) => [group.value, group.rows.map((row) => row.id)])).toEqual(entry.expected)
    })
  }
})

describe('Datenbankansicht – reine Funktionen', () => {
  it('gruppiert nur nach Auswahl-Eigenschaften', () => {
    expect(groupableProperties(table).map((property) => property.id)).toEqual(['status', 'fonds'])
    expect(groupRecords(table, 'titel')).toEqual([])
    expect(groupRecords(table, '')).toEqual([])
  })

  it('setzt beim Ablegen in „ohne Wert“ null und findet Nachbarspalten', () => {
    expect(dropValue('')).toBeNull()
    expect(dropValue('offen')).toBe('offen')
    const groups = groupRecords(table, 'status')
    expect(neighbourGroup(groups, 'offen', 1)).toBe('in Prüfung')
    expect(neighbourGroup(groups, 'offen', -1)).toBe('')
    expect(neighbourGroup(groups, '', -1)).toBeNull()
    expect(neighbourGroup(groups, 'fehlt', 1)).toBeNull()
    expect(groupOf(table, table.rows[3]!, 'fonds')).toBe('')
    expect(groupOf(table, table.rows[0]!, 'status')).toBe('offen')
  })

  it('ändert Tabellen unveränderlich und sucht in Zellen', () => {
    const changed = withCell(table, 'r1', 'status', 'erledigt')
    expect(changed.rows[0]?.cells.status).toBe('erledigt')
    expect(table.rows[0]?.cells.status).toBe('offen')
    expect(withRow(changed, { id: 'r1', cells: {} }).rows[0]?.cells).toEqual({})
    expect(withRow(changed, { id: 'neu', cells: {} }).rows).toHaveLength(table.rows.length + 1)
    expect(matchesRecord(table.rows[0]!, 'vorhaben a')).toBe(true)
    expect(matchesRecord(table.rows[0]!, '1200')).toBe(true)
    expect(matchesRecord(table.rows[5]!, 'efre')).toBe(true)
    expect(matchesRecord(table.rows[0]!, '  ')).toBe(true)
    expect(matchesRecord(table.rows[0]!, 'fehlt')).toBe(false)
  })

  it('Speicherport liefert Kopien, meldet Änderungen und legt Datensätze an', async () => {
    const onChange = vi.fn()
    const port = createMemoryRecordPort(table, { onChange, newId: () => 'r9', clock: () => '2026-09-26T10:00:00Z' })
    const loaded = await port.load()
    expect(loaded).toEqual(table)
    expect(loaded).not.toBe(table)
    expect((await port.updateCell('r3', 'status', 'offen'))?.cells.status).toBe('offen')
    expect(onChange).toHaveBeenLastCalledWith(expect.objectContaining({ rows: expect.arrayContaining([expect.objectContaining({ id: 'r3' })]) }))
    await expect(port.updateCell('fehlt', 'status', 'offen')).rejects.toThrow("Datensatz 'fehlt' nicht gefunden")
    const added = await port.addRow?.({ status: 'erledigt' })
    expect(added).toEqual({ id: 'r9', cells: { status: 'erledigt' }, created_at: '2026-09-26T10:00:00Z' })
    expect(port.snapshot().rows).toHaveLength(table.rows.length + 1)
    expect(table.rows).toHaveLength(6)
  })
})
