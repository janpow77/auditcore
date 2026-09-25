import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'
import { FaBadge, FaButton, FaDialog, FaIcon, FaTextField, ICONS, isIconName } from '../src'
import { wrapTarget } from '../src/composables/useFocusTrap'

afterEach(() => {
  document.body.innerHTML = ''
})

describe('Basiskomponenten', () => {
  it('FaIcon ist ohne Beschriftung dekorativ, mit Beschriftung ein Bild', () => {
    expect(mount(FaIcon, { props: { name: 'plus' } }).attributes('aria-hidden')).toBe('true')
    const labelled = mount(FaIcon, { props: { name: 'plus', label: 'Hinzufügen' } })
    expect(labelled.attributes('role')).toBe('img')
    expect(labelled.findAll('path')).toHaveLength(ICONS.plus.length)
    expect(isIconName('plus')).toBe(true)
    expect(isIconName('unbekannt')).toBe(false)
  })

  it('FaButton mit nur Symbol hat eine zugängliche Beschriftung und meldet Klicks', async () => {
    const wrapper = mount(FaButton, { props: { icon: 'close', iconOnly: true, label: 'Schließen' } })
    expect(wrapper.attributes('aria-label')).toBe('Schließen')
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
    await wrapper.setProps({ loading: true })
    expect(wrapper.attributes('disabled')).toBeDefined()
    expect(wrapper.attributes('aria-busy')).toBe('true')
  })

  it('FaBadge zeigt Ton und Text', () => {
    const wrapper = mount(FaBadge, { props: { tone: 'danger', label: 'überfällig' } })
    expect(wrapper.classes()).toContain('fa-badge--danger')
    expect(wrapper.text()).toBe('überfällig')
  })

  it('FaTextField verknüpft Label, Eingabe und Fehlermeldung', async () => {
    const wrapper = mount(FaTextField, { props: { label: 'Titel', error: 'Pflichtfeld', modelValue: '' } })
    const input = wrapper.get('input')
    expect(wrapper.get('label').attributes('for')).toBe(input.attributes('id'))
    expect(input.attributes('aria-invalid')).toBe('true')
    expect(wrapper.get('[role="alert"]').text()).toBe('Pflichtfeld')
    await input.setValue('Neu')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['Neu'])
  })

  it('FaDialog ist modal beschriftet, fokussiert und schließt mit Escape', async () => {
    const wrapper = mount(FaDialog, {
      props: { open: true, title: 'Einstellungen', description: 'Spalten anpassen' },
      slots: { default: '<input id="erstes" />' },
      attachTo: document.body,
    })
    await nextTick()
    await nextTick()
    const dialog = document.querySelector('[role="dialog"]') as HTMLElement
    expect(dialog.getAttribute('aria-modal')).toBe('true')
    expect(document.getElementById(dialog.getAttribute('aria-labelledby') ?? '')?.textContent).toBe('Einstellungen')
    expect(document.activeElement?.tagName).toBe('BUTTON')
    dialog.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    expect(wrapper.emitted('update:open')?.[0]).toEqual([false])
    wrapper.unmount()
  })

  it('Fokusfalle springt am Rand zum anderen Ende', () => {
    const a = document.createElement('button')
    const b = document.createElement('button')
    expect(wrapTarget([a, b], b, false)).toBe(a)
    expect(wrapTarget([a, b], a, true)).toBe(b)
    expect(wrapTarget([a, b], a, false)).toBeNull()
    expect(wrapTarget([], a, false)).toBeNull()
  })
})
