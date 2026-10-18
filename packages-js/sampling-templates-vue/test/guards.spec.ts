/**
 * Auflagen der Gesamtabnahme an die Oberfläche: Der Rechner meldet ungesicherte
 * Änderungen nach außen (Routenwächter der Anwendung, V8), und der Bericht trägt
 * am Bildschirm wie im Druck Vorlage, Rechtsstand, Fassung des Rechenkerns und
 * die Prüfsumme der Eingaben (V4). Dazu die Prüfgrundlage in der Fußzeile (V9).
 */
import type { DownloadFile } from '@auditcore/common'
import { ENGINE_VERSION, workspaceChecksum } from '@auditcore/sampling-templates-core'
import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { SamplingCalculator } from '../src/index'

const mounted: VueWrapper[] = []
function mountCalculator(props: Record<string, unknown> = {}): VueWrapper {
  const wrapper = mount(SamplingCalculator, { attachTo: document.body, props: { saveFile: (_file: DownloadFile) => undefined, ...props } })
  mounted.push(wrapper)
  return wrapper
}

async function settle(): Promise<void> {
  for (let round = 0; round < 4; round += 1) {
    await flushPromises()
    await vi.dynamicImportSettled()
    await new Promise((resolve) => setTimeout(resolve, 0))
  }
  await nextTick()
}

async function menu(wrapper: VueWrapper, action: string): Promise<void> {
  await wrapper.get('.fa-st__menu-wrap > button').trigger('click')
  await wrapper.get(`[data-action="${action}"]`).trigger('click')
  await settle()
}

async function withSample(): Promise<VueWrapper> {
  const wrapper = mountCalculator()
  await wrapper.get('[data-sheet="03_MUS_1Z"]').trigger('click')
  await menu(wrapper, 'sample')
  return wrapper
}

type Exposed = { isDirty: () => boolean; dirty: boolean; state: Parameters<typeof workspaceChecksum>[0] }
const exposed = (wrapper: VueWrapper): Exposed => wrapper.vm as unknown as Exposed
const input = (wrapper: VueWrapper, cell: string) => wrapper.get(`[data-cell="${cell}"]`).get<HTMLInputElement>('input, select')

afterEach(() => {
  for (const wrapper of mounted.splice(0)) wrapper.unmount()
  document.body.innerHTML = ''
})

describe('Ungesicherte Änderungen für den Routenwächter der Anwendung', () => {
  it('Ereignis `dirty` und Methode `isDirty()` folgen dem Arbeitsstand: Eingabe, Speichern, erneute Eingabe', async () => {
    const wrapper = await withSample()
    const events = (): unknown[] => (wrapper.emitted('dirty') ?? []).map(([value]) => value)
    // Der Anfangsstand wird gemeldet, damit die Anwendung ohne eigene Annahme beginnt.
    expect(events()).toEqual([false])
    expect(exposed(wrapper).isDirty()).toBe(false)
    await input(wrapper, 'C20').setValue('0,24')
    expect(events()).toEqual([false, true])
    expect([exposed(wrapper).isDirty(), exposed(wrapper).dirty]).toEqual([true, true])
    await menu(wrapper, 'save')
    expect(events()).toEqual([false, true, false])
    expect(exposed(wrapper).isDirty()).toBe(false)
    await input(wrapper, 'C20').setValue('0,25')
    expect(events().at(-1)).toBe(true)
  })
})

describe('Bericht und Fußzeile', () => {
  it('der Bericht nennt Vorlage, Rechtsstand, Rechenkern und die Prüfsumme der Eingaben – dieselbe wie in Datei und Export', async () => {
    const wrapper = await withSample()
    await wrapper.get('[data-step="report"]').trigger('click')
    await settle()
    const identity = wrapper.get('[data-report-page] [data-report-identity]')
    expect(identity.text()).toContain('Stichprobenvorlagen')
    expect(identity.text()).toContain(`Rechenkern: ${ENGINE_VERSION}`)
    const checksum = await workspaceChecksum(exposed(wrapper).state)
    expect(checksum).toMatch(/^sha256:[0-9a-f]{64}$/)
    expect(identity.get('[data-report-checksum]').text()).toBe(`Prüfsumme der Eingaben: ${checksum}`)
    // Die Zeile gehört zur Druckseite und trägt keine Klasse, die das Druck-Stylesheet ausblendet.
    expect(identity.classes()).toEqual(['fa-st__report-identity'])
  })

  it('die Fußzeile nennt die Prüfgrundlage: Neuberechnung der Vorlage in Microsoft Excel', () => {
    expect(mountCalculator().get('[data-template-status]').text()).toContain('Neuberechnung der Vorlage mit Microsoft Excel (Version 16.0.20326).')
  })
})
