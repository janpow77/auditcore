import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import FaVvt from '../../src/dataprotection/FaVvt.vue'
import { RestError } from '../../src/rest'
import { fakePort, register } from '../../../ui-core/test/dataprotection/fake-port'

afterEach(() => {
  vi.useRealTimers()
  document.body.innerHTML = ''
})

async function mountVvt(props: Record<string, unknown> = {}) {
  const port = fakePort()
  const wrapper = mount(FaVvt, { props: { port, actor: 'daten-b', ...props }, attachTo: document.body })
  await flushPromises()
  return { port, wrapper }
}

describe('FaVvt', () => {
  it('zeigt Fassung, Deckblatt, Tätigkeiten je Referat und die Hinweise der Bibliothek', async () => {
    const { wrapper } = await mountVvt()
    expect(wrapper.get('h2').text()).toContain('Verzeichnis von Verarbeitungstätigkeiten')
    expect(wrapper.get('[data-testid="vvt-status"]').text()).toContain('Fassung 2 – Entwurf')
    expect(wrapper.get('[data-testid="vvt-cover"] input').element).toHaveProperty('value', 'Musterbehörde des Landes')
    const list = wrapper.get('[data-testid="vvt-list"]')
    expect(list.findAll('h4').map((h) => h.text())).toEqual(['Referat Z 1', 'Referat Z 6'])
    expect(list.text()).toContain('2 Pflichtangaben fehlen')
    expect(list.text()).toContain('vollständig')
    expect(wrapper.get('[data-testid="vvt-issues"]').text()).toContain('2 Pflichtangaben fehlen, 2 Hinweise')
  })

  it('wählt eine Tätigkeit per Tastatur/Klick, markiert Pflichtfelder und prüft Eingaben über den Port', async () => {
    vi.useFakeTimers()
    const { port, wrapper } = await mountVvt()
    const items = wrapper.findAll('.fa-vvt__item')
    await items[2]!.trigger('click')
    expect(items[2]!.attributes('aria-current')).toBe('true')
    const detail = wrapper.get('[data-testid="vvt-detail"]')
    expect(detail.attributes('aria-label')).toBe('Terminplanung über Online-Dienst')
    const storage = detail.findAll('.fa-dataprotection__field').find((field) => field.text().startsWith('Speicherdauer'))!
    expect(storage.get('textarea').attributes('aria-invalid')).toBe('true')
    expect(storage.get('textarea').attributes('aria-describedby')).toBeTruthy()
    await storage.get('textarea').setValue('2 Jahre')
    expect(wrapper.get('[data-testid="vvt-status"]').text()).toContain('Ungespeicherte Änderungen')
    await vi.advanceTimersByTimeAsync(500)
    expect(port.checkRegister).toHaveBeenCalledTimes(1)
    expect(vi.mocked(port.checkRegister).mock.calls[0]![0].taetigkeiten[2]?.speicherdauer).toBe('2 Jahre')
    await flushPromises()
    expect(wrapper.get('[data-testid="vvt-issues"]').text()).toContain('Alle Pflichtangaben')
  })

  it('speichert den Entwurf mit der gelesenen Revision und meldet das Ereignis', async () => {
    const { port, wrapper } = await mountVvt()
    const flag = wrapper.findAll('input[type="radio"]').find((input) => (input.element as HTMLInputElement).checked === false)!
    await flag.setValue(true)
    const save = wrapper.findAll('button').find((button) => button.text() === 'Entwurf speichern')!
    await save.trigger('click')
    await flushPromises()
    expect(port.saveDraft).toHaveBeenCalledWith(expect.objectContaining({ referate: ['Referat Z 1', 'Referat Z 6'] }), register.draft!.revision)
    expect(wrapper.emitted('draft-saved')?.[0]).toEqual([{ version: 2, revision: register.draft!.revision + 1 }])
    expect(wrapper.get('[aria-live="polite"]').text()).toContain('Entwurf gespeichert')
  })

  it('zeigt das Vier-Augen-Prinzip vorab und meldet Serverfehler', async () => {
    const port = fakePort({ releaseRegister: vi.fn(async () => { throw new RestError('Vier-Augen-Prinzip verletzt.', 403, 'vier_augen_verletzt') }) })
    const editor = mount(FaVvt, { props: { port, actor: 'daten-a' } })
    await flushPromises()
    expect(editor.get('[data-testid="vvt-release-hint"]').text()).toContain('Vier-Augen-Prinzip')
    const release = editor.findAll('button').find((button) => button.text().startsWith('Freigeben'))!
    expect(release.attributes('disabled')).toBeDefined()
    const other = mount(FaVvt, { props: { port, actor: 'daten-b' } })
    await flushPromises()
    await other.findAll('button').find((button) => button.text().startsWith('Freigeben'))!.trigger('click')
    await flushPromises()
    expect(other.get('[role="alert"]').text()).toBe('Vier-Augen-Prinzip verletzt.')
    expect(other.emitted('error')?.[0]).toEqual([{ code: 'vier_augen_verletzt', message: 'Vier-Augen-Prinzip verletzt.', status: 403 }])
  })

  it('exportiert CSV mit Formelschutz und schaltet zwischen Entwurf und Freigabe', async () => {
    const { wrapper } = await mountVvt()
    await wrapper.findAll('button').find((button) => button.text() === 'CSV')!.trigger('click')
    const exported = wrapper.emitted('exported')?.[0]?.[0] as { filename: string; content: string }
    expect(exported.filename).toBe('Verarbeitungsverzeichnis_Fassung_2.csv')
    expect(exported.content).toContain("'=Voreinstellung des Anbieters")
    await wrapper.findAll('button').find((button) => button.text() === 'Freigegebene Fassung anzeigen')!.trigger('click')
    expect(wrapper.get('[data-testid="vvt-status"]').text()).toContain('Fassung 1 – freigegeben')
    expect(wrapper.find('[data-testid="vvt-detail"] textarea').exists()).toBe(false)
    expect(wrapper.get('[data-testid="vvt-list"]').findAll('.fa-vvt__item')).toHaveLength(2)
  })

  it('bleibt ohne Bearbeitungsrecht reine Ansicht und spricht Englisch', async () => {
    const { wrapper } = await mountVvt({ editable: false, locale: 'en' })
    expect(wrapper.get('h2').text()).toContain('Record of processing activities')
    expect(wrapper.find('textarea').exists()).toBe(false)
    expect(wrapper.findAll('button').some((button) => button.text().startsWith('Release'))).toBe(false)
  })

  it('meldet einen fehlenden Port', () => {
    const wrapper = mount(FaVvt)
    expect(wrapper.get('[role="alert"]').text()).toContain('Kein Port übergeben')
  })
})
