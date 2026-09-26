import { RestError } from '@auditcore/common'
import { act, cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { fakePort, register } from '../../ui-core/test/dataprotection/fake-port'
import { FlowauditVvt, type FlowauditVvtProps } from '../src'

const flush = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  document.body.innerHTML = ''
})

async function renderVvt(props: Partial<FlowauditVvtProps> = {}) {
  const port = fakePort()
  const view = render(<FlowauditVvt port={port} actor="daten-b" {...props} />)
  await flush()
  return { port, ...view }
}

const byTestId = (id: string) => screen.getByTestId(id)
const button = (label: string) => screen.getAllByRole('button').find((node) => node.textContent?.trim() === label) as HTMLElement

describe('FlowauditVvt (nativ)', () => {
  it('zeigt Fassung, Deckblatt, Tätigkeiten je Referat und die Hinweise der Bibliothek', async () => {
    await renderVvt()
    expect(screen.getByRole('heading', { level: 2 }).textContent).toContain('Verzeichnis von Verarbeitungstätigkeiten')
    expect(byTestId('vvt-status').textContent).toContain('Fassung 2 – Entwurf')
    expect((byTestId('vvt-cover').querySelector('input') as HTMLInputElement).value).toBe('Musterbehörde des Landes')
    const list = byTestId('vvt-list')
    expect(Array.from(list.querySelectorAll('h4')).map((h) => h.textContent)).toEqual(['Referat Z 1', 'Referat Z 6'])
    expect(list.textContent).toContain('2 Pflichtangaben fehlen')
    expect(list.textContent).toContain('vollständig')
    expect(byTestId('vvt-issues').textContent).toContain('2 Pflichtangaben fehlen, 2 Hinweise')
  })

  it('wählt eine Tätigkeit, markiert Pflichtfelder und prüft Eingaben über den Port', async () => {
    const { port } = await renderVvt()
    vi.useFakeTimers()
    const items = byTestId('vvt-list').querySelectorAll('.fa-vvt__item')
    fireEvent.click(items[2] as HTMLElement)
    expect(items[2]?.getAttribute('aria-current')).toBe('true')
    const detail = byTestId('vvt-detail')
    expect(detail.getAttribute('aria-label')).toBe('Terminplanung über Online-Dienst')
    const storage = Array.from(detail.querySelectorAll('.fa-dataprotection__field')).find((field) => field.textContent?.startsWith('Speicherdauer')) as HTMLElement
    const textarea = storage.querySelector('textarea') as HTMLTextAreaElement
    expect(textarea.getAttribute('aria-invalid')).toBe('true')
    expect(textarea.getAttribute('aria-describedby')).toBeTruthy()
    fireEvent.change(textarea, { target: { value: '2 Jahre' } })
    expect(byTestId('vvt-status').textContent).toContain('Ungespeicherte Änderungen')
    await act(() => vi.advanceTimersByTimeAsync(500))
    expect(port.checkRegister).toHaveBeenCalledTimes(1)
    expect(vi.mocked(port.checkRegister).mock.calls[0]![0].taetigkeiten[2]?.speicherdauer).toBe('2 Jahre')
    expect(byTestId('vvt-issues').textContent).toContain('Alle Pflichtangaben')
  })

  it('speichert den Entwurf mit der gelesenen Revision und meldet das Ereignis', async () => {
    const onDraftSaved = vi.fn()
    const { port, container } = await renderVvt({ onDraftSaved })
    const flag = Array.from(container.querySelectorAll<HTMLInputElement>('input[type="radio"]')).find((input) => !input.checked) as HTMLInputElement
    fireEvent.click(flag)
    fireEvent.click(button('Entwurf speichern'))
    await flush()
    expect(port.saveDraft).toHaveBeenCalledWith(expect.objectContaining({ referate: ['Referat Z 1', 'Referat Z 6'] }), register.draft!.revision)
    expect(onDraftSaved).toHaveBeenCalledWith({ version: 2, revision: register.draft!.revision + 1 })
    expect(container.querySelector('[aria-live="polite"]')?.textContent).toContain('Entwurf gespeichert')
  })

  it('zeigt das Vier-Augen-Prinzip vorab und meldet Serverfehler', async () => {
    const port = fakePort({ releaseRegister: vi.fn(async () => { throw new RestError('Vier-Augen-Prinzip verletzt.', 403, 'vier_augen_verletzt') }) })
    const editor = render(<FlowauditVvt port={port} actor="daten-a" />)
    await flush()
    expect(byTestId('vvt-release-hint').textContent).toContain('Vier-Augen-Prinzip')
    expect(within(editor.container).getByRole('button', { name: /^Freigeben/ }).hasAttribute('disabled')).toBe(true)
    editor.unmount()
    const onError = vi.fn()
    const other = render(<FlowauditVvt port={port} actor="daten-b" onError={onError} />)
    await flush()
    fireEvent.click(within(other.container).getByRole('button', { name: /^Freigeben/ }))
    await flush()
    expect(within(other.container).getByRole('alert').textContent).toBe('Vier-Augen-Prinzip verletzt.')
    expect(onError).toHaveBeenCalledWith({ code: 'vier_augen_verletzt', message: 'Vier-Augen-Prinzip verletzt.', status: 403 })
  })

  it('exportiert CSV mit Formelschutz und schaltet zwischen Entwurf und Freigabe', async () => {
    const onExported = vi.fn()
    await renderVvt({ onExported })
    fireEvent.click(button('CSV'))
    const exported = onExported.mock.calls[0]?.[0] as { filename: string; content: string }
    expect(exported.filename).toBe('Verarbeitungsverzeichnis_Fassung_2.csv')
    expect(exported.content).toContain("'=Voreinstellung des Anbieters")
    fireEvent.click(button('Freigegebene Fassung anzeigen'))
    expect(byTestId('vvt-status').textContent).toContain('Fassung 1 – freigegeben')
    expect(byTestId('vvt-detail').querySelector('textarea')).toBeNull()
    expect(byTestId('vvt-list').querySelectorAll('.fa-vvt__item')).toHaveLength(2)
  })

  it('bleibt ohne Bearbeitungsrecht reine Ansicht und spricht Englisch', async () => {
    const { container } = await renderVvt({ editable: false, locale: 'en' })
    expect(screen.getByRole('heading', { level: 2 }).textContent).toContain('Record of processing activities')
    expect(container.querySelector('textarea')).toBeNull()
    expect(screen.getAllByRole('button').some((node) => node.textContent?.startsWith('Release'))).toBe(false)
  })

  it('meldet einen fehlenden Port', () => {
    render(<FlowauditVvt />)
    expect(screen.getByRole('alert').textContent).toContain('Kein Port übergeben')
  })
})
