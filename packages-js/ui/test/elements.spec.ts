import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'
import { ELEMENTS, defineFlowauditElements } from '../src/elements'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Web Components', () => {
  it('alle Elemente folgen dem Namensschema flowaudit-<name> und sind eindeutig', () => {
    const tags = ELEMENTS.map((entry) => entry.tag)
    expect(new Set(tags).size).toBe(tags.length)
    for (const tag of tags) expect(tag).toMatch(/^flowaudit-[a-z][a-z0-9-]*$/)
  })

  it('registriert flowaudit-table im Light DOM, nimmt Eigenschaften an und sendet Ereignisse', async () => {
    defineFlowauditElements({ only: ['flowaudit-table'] })
    defineFlowauditElements()
    expect(customElements.get('flowaudit-table')).toBeDefined()
    const element = document.createElement('flowaudit-table') as HTMLElement & Record<string, unknown>
    element.columns = [{ key: 'name', label: 'Name' }]
    element.rows = [{ id: 1, name: 'Vorhaben A' }]
    element.clickable = true
    document.body.append(element)
    await nextTick()
    expect(element.shadowRoot).toBeNull()
    expect(element.querySelector('td')?.textContent).toBe('Vorhaben A')
    const received: unknown[] = []
    element.addEventListener('row-click', (event) => received.push((event as CustomEvent).detail))
    element.querySelector('tbody tr')?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(received).toEqual([[{ id: 1, name: 'Vorhaben A' }]])
  })
})
