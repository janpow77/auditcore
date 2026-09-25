import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { FaTable, ariaSort, compareValues, nextSort, sortRows, type TableColumn } from '../src'

const rows = [
  { id: 'a', name: 'Übergang', betrag: 10 },
  { id: 'b', name: 'Antrag', betrag: null },
  { id: 'c', name: 'Zahlung', betrag: 2 },
]
const columns: TableColumn[] = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'betrag', label: 'Betrag', sortable: true, align: 'end', format: (v) => (v === null ? '–' : `${String(v)} €`) },
]

describe('Tabellensortierung', () => {
  it('sortiert sprachsensitiv, stabil und leere Werte zuletzt', () => {
    expect(sortRows(rows, { key: 'name', direction: 'asc' }).map((r) => r.id)).toEqual(['b', 'a', 'c'])
    expect(sortRows(rows, { key: 'betrag', direction: 'asc' }).map((r) => r.id)).toEqual(['c', 'a', 'b'])
    expect(sortRows(rows, { key: 'betrag', direction: 'desc' }).map((r) => r.id)).toEqual(['a', 'c', 'b'])
    expect(sortRows(rows, null).map((r) => r.id)).toEqual(['a', 'b', 'c'])
    expect(compareValues('Datei 2', 'Datei 10')).toBeLessThan(0)
  })

  it('wechselt aufsteigend → absteigend → unsortiert', () => {
    const first = nextSort(null, 'name')
    expect(first).toEqual({ key: 'name', direction: 'asc' })
    const second = nextSort(first, 'name')
    expect(ariaSort(second, 'name')).toBe('descending')
    expect(nextSort(second, 'name')).toBeNull()
    expect(nextSort(second, 'betrag')).toEqual({ key: 'betrag', direction: 'asc' })
  })
})

describe('FaTable', () => {
  it('rendert formatierte Zellen, sortiert per Klick und setzt aria-sort', async () => {
    const wrapper = mount(FaTable, { props: { columns, rows, caption: 'Belege' } })
    expect(wrapper.get('caption').text()).toBe('Belege')
    expect(wrapper.findAll('tbody tr')[1]?.text()).toContain('–')
    await wrapper.findAll('th button')[1]?.trigger('click')
    expect(wrapper.findAll('th')[1]?.attributes('aria-sort')).toBe('ascending')
    expect(wrapper.emitted('sort-change')?.[0]).toEqual([{ key: 'betrag', direction: 'asc' }])
    expect(wrapper.findAll('tbody tr')[0]?.text()).toContain('Zahlung')
  })

  it('zeigt einen Leertext und meldet Zeilenklicks per Tastatur', async () => {
    expect(mount(FaTable, { props: { columns, rows: [] } }).text()).toContain('Keine Einträge')
    const wrapper = mount(FaTable, { props: { columns, rows, clickable: true, locale: 'en' } })
    await wrapper.findAll('tbody tr')[0]?.trigger('keydown', { key: 'Enter' })
    expect(wrapper.emitted('row-click')?.[0]).toEqual([rows[0]])
    expect(wrapper.get('th button').attributes('aria-label')).toBe('Sort by Name')
  })
})
