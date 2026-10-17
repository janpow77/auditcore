import type { DownloadFile } from '@auditcore/common'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { SamplingCalculator } from '../src/index'
import { FOUNDATION_SHEETS } from './sheets'

const delivered: DownloadFile[] = []

const mounted: VueWrapper[] = []

function mountCalculator(props: Record<string, unknown> = {}): VueWrapper {
  const wrapper = mount(SamplingCalculator, {
    attachTo: document.body,
    props: { sheets: FOUNDATION_SHEETS, localDraft: false, saveFile: (file: DownloadFile) => void delivered.push(file), ...props },
  })
  mounted.push(wrapper)
  return wrapper
}

/** Wartet auf Rechnen, Prüfsumme und den nachgeladenen Excel-Austausch. */
async function settle(): Promise<void> {
  for (let round = 0; round < 4; round += 1) {
    await flushPromises()
    await vi.dynamicImportSettled()
    if (!vi.isFakeTimers()) await new Promise((resolve) => setTimeout(resolve, 0))
  }
  await nextTick()
}

async function menu(wrapper: VueWrapper, action: string): Promise<void> {
  await wrapper.get('.fa-st__menu-wrap > button').trigger('click')
  await wrapper.get(`[data-action="${action}"]`).trigger('click')
  await settle()
}

async function withSample(props: Record<string, unknown> = {}): Promise<VueWrapper> {
  const wrapper = mountCalculator(props)
  await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
  await menu(wrapper, 'sample')
  return wrapper
}

const field = (wrapper: VueWrapper, cell: string) => wrapper.get(`[data-cell="${cell}"]`)
const inputOf = (wrapper: VueWrapper, cell: string) => field(wrapper, cell).get<HTMLInputElement>('input, select')

beforeEach(() => {
  delivered.length = 0
  localStorage.clear()
  sessionStorage.clear()
})
afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
})

describe('Lokaler Entwurf', () => {
  it('ist abschaltbar: ohne Entwurf wird nichts im Browser abgelegt', async () => {
    vi.useFakeTimers()
    try {
      const wrapper = await withSample({ localDraft: false })
      await inputOf(wrapper, 'C20').setValue('0,24')
      vi.advanceTimersByTime(2000)
      await settle()
      expect(localStorage.length).toBe(0)
      expect(wrapper.find('[data-action="clearDraft"]').exists()).toBe(false)
      expect(wrapper.text()).not.toContain('lokalen Entwurf')
    } finally {
      vi.useRealTimers()
    }
  })

  it('wird nach Änderungen abgelegt, beim nächsten Start geprüft übernommen und lässt sich löschen', async () => {
    const first = await withSample({ localDraft: true, draftKey: 'test' })
    await inputOf(first, 'C20').setValue('0,24')
    first.unmount()
    mounted.length = 0
    await settle()
    expect(localStorage.getItem('auditcore-sampling-templates:test')).toContain('flowaudit-stichprobe')
    const second = mountCalculator({ localDraft: true, draftKey: 'test' })
    await settle()
    await settle()
    expect(inputOf(second, 'C20').element.value).toBe('0,24')
    expect(second.get('[data-notice="info"]').text()).toContain('Lokaler Entwurf wiederhergestellt')
    expect(second.get('[data-status]').text()).toContain('geändert')
    await menu(second, 'clearDraft')
    expect(localStorage.getItem('auditcore-sampling-templates:test')).toBeNull()
    expect(second.get('[data-flash]').text()).toBe('Lokaler Entwurf gelöscht.')
  })
  it('Stufe „nur diese Sitzung“: sessionStorage statt localStorage; „Neu“ löscht den Zwischenstand', async () => {
    const first = await withSample({ draft: 'session', draftKey: 'sitzung' })
    await inputOf(first, 'C20').setValue('0,24')
    expect(first.get('[data-draft-note]').text()).toContain('für diese Sitzung')
    first.unmount()
    mounted.length = 0
    await settle()
    expect(sessionStorage.getItem('auditcore-sampling-templates:sitzung')).toContain('flowaudit-stichprobe')
    expect(localStorage.length).toBe(0)
    const second = mountCalculator({ draft: 'session', draftKey: 'sitzung' })
    await settle()
    await settle()
    expect(inputOf(second, 'C20').element.value).toBe('0,24')
    await menu(second, 'new')
    ;(document.querySelector('[data-action="discard"]') as HTMLButtonElement).click()
    await settle()
    expect(sessionStorage.getItem('auditcore-sampling-templates:sitzung')).toBeNull()
  })

  it('Stufenwechsel: „auf diesem Gerät behalten“ zieht den Zwischenstand um, „aus“ leert beide Ablagen; die Anwendung bietet den Umschalter im Slot an', async () => {
    const wrapper = mount(SamplingCalculator, {
      attachTo: document.body,
      props: { sheets: FOUNDATION_SHEETS, draft: 'session', draftKey: 'wechsel', saveFile: () => undefined },
      slots: { draft: '<template #draft="{ mode, stored }"><span data-slot-draft>{{ mode }}/{{ stored }}</span></template>' },
    })
    mounted.push(wrapper)
    await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
    await inputOf(wrapper, 'C20').setValue('0,24')
    await new Promise((resolve) => setTimeout(resolve, 700))
    await settle()
    expect(sessionStorage.getItem('auditcore-sampling-templates:wechsel')).not.toBeNull()
    expect(wrapper.get('[data-slot-draft]').text()).toBe('session/true')
    expect(wrapper.emitted('draft')).toEqual([[{ mode: 'session', stored: true }]])
    await wrapper.setProps({ draft: 'device' })
    await settle()
    expect(localStorage.getItem('auditcore-sampling-templates:wechsel')).toContain('flowaudit-stichprobe')
    expect(sessionStorage.getItem('auditcore-sampling-templates:wechsel')).toBeNull()
    await wrapper.setProps({ draft: 'off' })
    await settle()
    expect(localStorage.length + sessionStorage.length).toBe(0)
    expect(wrapper.find('[data-draft-note]').exists()).toBe(false)
  })
})
