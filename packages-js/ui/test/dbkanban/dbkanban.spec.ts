import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import FaDbKanban from '../../src/dbkanban/FaDbKanban.vue'
import { defineFlowauditElements } from '../../src/elements'
import { recordPort, recordTable } from '../../../ui-core/test/dbkanban/fixtures'

afterEach(() => {
  document.body.innerHTML = ''
})

function transfer(): DataTransfer {
  const data = new Map<string, string>()
  return { setData: (type: string, value: string) => data.set(type, value), getData: (type: string) => data.get(type) ?? '', effectAllowed: 'all' } as unknown as DataTransfer
}

async function mounted(props: Record<string, unknown> = {}) {
  const port = recordPort()
  const wrapper = mount(FaDbKanban, { props: { port, ...props }, attachTo: document.body })
  await flushPromises()
  return { port, wrapper }
}

const cardsIn = (root: { findAll: (s: string) => { attributes: (n: string) => string | undefined }[] }, column: string) =>
  root.findAll(`[data-column="${column}"] .fa-db-kanban-card`).map((card) => card.attributes('data-card-id'))

describe('FaDbKanban', () => {
  it('verschiebt eine Karte per Ziehen und Ablegen und setzt den Zellwert', async () => {
    const { port, wrapper } = await mounted()
    const dataTransfer = transfer()
    await wrapper.find('[data-card-id="r1"]').trigger('dragstart', { dataTransfer })
    expect(wrapper.find('[data-card-id="r1"]').classes()).toContain('fa-db-kanban-card--dragging')
    await wrapper.find('[data-column="erledigt"]').trigger('dragover', { dataTransfer })
    expect(wrapper.find('[data-column="erledigt"]').classes()).toContain('fa-db-kanban-column--over')
    await wrapper.find('[data-column="erledigt"]').trigger('drop', { dataTransfer })
    await flushPromises()
    expect(port.updateCell).toHaveBeenCalledWith('r1', 'status', 'erledigt')
    expect(wrapper.emitted('record-move')?.[0]).toEqual([{ rowId: 'r1', propertyId: 'status', value: 'erledigt' }])
    expect(cardsIn(wrapper, 'erledigt')).toEqual(['r1', 'r2'])
    expect(wrapper.find('[role="status"]').text()).toBe('„Vorhaben A“ nach „erledigt“ verschoben.')
  })

  it('verschiebt mit Strg+Pfeil und behält den Fokus auf der Karte', async () => {
    const { port, wrapper } = await mounted()
    await wrapper.find('[data-card-id="r4"]').trigger('keydown', { key: 'ArrowRight', ctrlKey: true })
    await flushPromises()
    expect(port.updateCell).toHaveBeenCalledWith('r4', 'status', 'erledigt')
    expect(document.activeElement?.getAttribute('data-card-id')).toBe('r4')
    await wrapper.find('[data-card-id="r4"]').trigger('keydown', { key: 'ArrowRight' })
    await wrapper.find('[data-card-id="r3"]').trigger('keydown', { key: 'ArrowLeft', ctrlKey: true })
    await flushPromises()
    expect(port.updateCell).toHaveBeenCalledOnce()
    expect(wrapper.find('[data-card-id="r4"]').attributes('aria-label')).toBe('Vorhaben D – erledigt')
  })

  it('wechselt die Gruppierung über die Auswahl und v-model:group-by', async () => {
    const { wrapper } = await mounted()
    await wrapper.find('select').setValue('fonds')
    expect(wrapper.emitted('update:groupBy')?.[0]).toEqual(['fonds'])
    expect(wrapper.findAll('.fa-db-kanban-column__name').map((n) => n.text())).toEqual(['Ohne Wert', 'EFRE', 'ESF+', 'JTF'])
    await wrapper.setProps({ groupBy: 'status' })
    expect(wrapper.findAll('.fa-db-kanban-column__name').map((n) => n.text())[1]).toBe('offen')
  })

  it('legt Einträge in einer Spalte an und durchsucht Karten', async () => {
    const { port, wrapper } = await mounted()
    await wrapper.find('[aria-label="Eintrag in „Ohne Wert“ hinzufügen"]').trigger('click')
    await flushPromises()
    expect(port.addRow).toHaveBeenCalledWith({ status: null })
    expect(wrapper.emitted('record-add')?.[0]?.[0]).toMatchObject({ id: 'neu-1' })
    expect(cardsIn(wrapper, '')).toEqual(['r3', 'r5', 'neu-1'])
    await wrapper.find('input[type="search"]').setValue('vorhaben b')
    expect(wrapper.findAll('.fa-db-kanban-card').map((c) => c.attributes('data-card-id'))).toEqual(['r2'])
  })

  it('arbeitet ohne Port auf einer übergebenen Tabelle und meldet die neue Tabelle', async () => {
    const wrapper = mount(FaDbKanban, { props: { table: recordTable }, attachTo: document.body })
    await flushPromises()
    await wrapper.find('[data-card-id="r1"]').trigger('keydown', { key: 'ArrowLeft', ctrlKey: true })
    await flushPromises()
    const changed = wrapper.emitted('table-change')?.[0]?.[0] as typeof recordTable
    expect(changed.rows.find((row) => row.id === 'r1')?.cells.status).toBeNull()
    expect(recordTable.rows[0]?.cells.status).toBe('offen')
  })

  it('zeigt Speicherfehler an und nimmt die Verschiebung zurück', async () => {
    const port = recordPort({ updateCell: vi.fn(async () => Promise.reject(new TypeError('Failed to fetch'))) })
    const wrapper = mount(FaDbKanban, { props: { port }, attachTo: document.body })
    await flushPromises()
    await wrapper.find('[data-card-id="r1"]').trigger('keydown', { key: 'ArrowRight', ctrlKey: true })
    await flushPromises()
    expect(wrapper.find('[role="alert"]').text()).toBe('Keine Verbindung zur Datenquelle (Failed to fetch).')
    expect(cardsIn(wrapper, 'offen')).toEqual(['r1', 'r6'])
    expect(wrapper.emitted('error')).toHaveLength(1)
  })

  it('läuft als Web Component <flowaudit-db-kanban>', async () => {
    defineFlowauditElements({ only: ['flowaudit-db-kanban'] })
    const element = document.createElement('flowaudit-db-kanban') as HTMLElement & { table?: unknown }
    document.body.append(element)
    element.table = recordTable
    const changed = vi.fn()
    element.addEventListener('table-change', changed)
    await vi.waitFor(() => expect(element.querySelectorAll('.fa-db-kanban-card')).toHaveLength(6))
    element.querySelector<HTMLElement>('[data-card-id="r2"]')?.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft', ctrlKey: true, bubbles: true }))
    await vi.waitFor(() => expect(changed).toHaveBeenCalledOnce())
  })
})
