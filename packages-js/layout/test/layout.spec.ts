import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import FaExportActions from '../src/FaExportActions.vue'
import FaLoginLayout from '../src/FaLoginLayout.vue'
import FaAppLayout from '../src/FaAppLayout.vue'
import FaThemeSwitch from '../src/FaThemeSwitch.vue'
import { defineFlowauditLayoutElements } from '../src/elements'

describe('@auditcore/layout', () => {
  it('renders a fish login scene with an accessible form slot', () => {
    const wrapper = mount(FaLoginLayout, { slots: { default: '<form aria-label="Anmelden"></form>' } })
    expect(wrapper.find('h1').text()).toBe('Willkommen zurück')
    expect(wrapper.find('form[aria-label="Anmelden"]').exists()).toBe(true)
    expect(wrapper.find('.fa-login-fish').exists()).toBe(true)
    expect(wrapper.find('.fa-login-art').attributes('aria-hidden')).toBe('true')
  })

  it('puts the account portrait at the far end of the app header', () => {
    const wrapper = mount(FaAppLayout, { props: { accountName: 'Ada', accountImage: '/ada.jpg' } })
    expect(wrapper.find('.fa-app-brand').exists()).toBe(true)
    expect(wrapper.find('.fa-app-account__image').attributes('src')).toBe('/ada.jpg')
    expect(wrapper.find('.fa-app-header').element.lastElementChild?.classList.contains('fa-app-account')).toBe(true)
  })

  it('emits save and both image/document export formats', async () => {
    const wrapper = mount(FaExportActions)
    const buttons = wrapper.findAll('button')
    await buttons[0]?.trigger('click')
    await buttons[1]?.trigger('click')
    await buttons[2]?.trigger('click')
    expect(wrapper.emitted('save')).toHaveLength(1)
    expect(wrapper.emitted('export')?.map(([format]) => format)).toEqual(['pdf', 'jpg'])
  })

  it('adapts the shared theme to an existing dark class and persists the choice', async () => {
    localStorage.removeItem('layout-theme-test')
    const wrapper = mount(FaThemeSwitch, { props: { target: 'class', storageKey: 'layout-theme-test' } })
    await wrapper.trigger('click')
    expect(localStorage.getItem('layout-theme-test')).toBe(document.documentElement.classList.contains('dark') ? 'dark' : 'light')
    wrapper.unmount()
  })

  it('registers the layout custom elements for non-Vue host applications', () => {
    const registered = defineFlowauditLayoutElements(['flowaudit-export-actions'])
    expect(registered.map((entry) => entry.tag)).toEqual(['flowaudit-export-actions'])
    expect(customElements.get('flowaudit-export-actions')).toBeDefined()
  })
})
