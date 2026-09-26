import { createRef, StrictMode } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render } from '@testing-library/react'
import { FlowauditEditor } from '../src/FlowauditEditor'
import type { FlowauditEditorHandle, FlowauditEditorProps } from '../src/editorProps'
import { fixture, flush, until } from './helpers'

afterEach(cleanup)

async function mountEditor(props: Partial<FlowauditEditorProps> = {}) {
  const ref = createRef<FlowauditEditorHandle>()
  const handlers = { onXmlChange: vi.fn(), onSave: vi.fn(), onError: vi.fn(), onReady: vi.fn(), onSelectionChange: vi.fn() }
  const view = render(<FlowauditEditor ref={ref} xml={fixture('schema-1.1.bpmn')} name="Muster" lockApproved={false} {...handlers} {...props} />)
  await until(() => Boolean(view.container.querySelector('.djs-container')) && (view.container.textContent ?? '').includes('Bewilligung'))
  return { ...view, ref, ...handlers }
}

const root = (container: HTMLElement) => container.querySelector('.fa-editor') as HTMLElement
const select = async (ref: { current: FlowauditEditorHandle | null }, id: string) => {
  ref.current!.select(id)
  await flush()
}

describe('FlowauditEditor (React)', () => {
  it('imports a 1.1 diagram with the core editor and renders toolbar, palette and status bar', async () => {
    const { container, onReady } = await mountEditor()
    expect(container.querySelector('[role="toolbar"]')).not.toBeNull()
    expect(container.querySelector('.fa-palette')).not.toBeNull()
    expect(container.querySelector('.fa-statusbar')).not.toBeNull()
    expect(onReady).toHaveBeenCalledTimes(1)
  })

  it('shows the properties of the selected element and writes changes back into the XML', async () => {
    const { container, ref, onXmlChange, onSelectionChange } = await mountEditor()
    await select(ref, 'Task_Bewilligen')
    await until(() => Boolean(container.querySelector('[role="tablist"][aria-orientation]')))
    expect(onSelectionChange).toHaveBeenLastCalledWith('Task_Bewilligen')
    const tabs = Array.from(container.querySelectorAll('.fa-props [role="tab"]')).map((tab) => tab.id)
    expect(tabs).toEqual(expect.arrayContaining(['fa-tab-general', 'fa-tab-legal', 'fa-tab-control', 'fa-tab-findings']))
    const name = container.querySelector<HTMLInputElement>('.fa-tab-general input')!
    fireEvent.change(name, { target: { value: 'Antrag abschließend bewilligen' } })
    fireEvent.blur(name)
    await until(() => onXmlChange.mock.calls.length > 0)
    const xml = onXmlChange.mock.calls.at(-1)![0] as string
    expect(xml).toContain('name="Antrag abschließend bewilligen"')
    expect(xml).toContain('flowaudit:diagrammInfo')
  })

  it('switches tabs with the arrow keys (WAI-ARIA tabs)', async () => {
    const { container, ref } = await mountEditor()
    await select(ref, 'Task_Bewilligen')
    await until(() => Boolean(container.querySelector('#fa-tab-general')))
    fireEvent.keyDown(container.querySelector('#fa-tab-general')!, { key: 'ArrowDown' })
    expect(container.querySelector('.fa-props [role="tab"][aria-selected="true"]')!.id).not.toBe('fa-tab-general')
  })

  it('validates locally after import and lists issues with a jump to the element', async () => {
    const { container, ref } = await mountEditor()
    const count = ref.current!.validation!.store.get().local.length
    expect(count).toBeGreaterThan(0)
    fireEvent.click(container.querySelector('.fa-statusbar button')!)
    await until(() => Boolean(container.querySelector('.fa-issues')))
    expect(container.querySelector('.fa-issues')!.textContent).toMatch(/BPMN-/)
  })

  it('reports save with XML and diagram info on Ctrl+S', async () => {
    const { container, onSave } = await mountEditor()
    fireEvent.keyDown(root(container), { key: 's', ctrlKey: true })
    await until(() => onSave.mock.calls.length > 0)
    const [payload] = onSave.mock.calls[0]!
    expect(payload.xml).toContain('bpmn:definitions')
    expect(payload.info).not.toBeNull()
  })

  it('does not save and disables inputs when read-only', async () => {
    const { container, ref, onSave } = await mountEditor({ readonly: true })
    fireEvent.keyDown(root(container), { key: 's', ctrlKey: true })
    await flush()
    expect(onSave).not.toHaveBeenCalled()
    await select(ref, 'Task_Bewilligen')
    await until(() => Boolean(container.querySelector('.fa-tab-general')))
    expect(container.querySelector('.fa-tab-general input')!.hasAttribute('disabled')).toBe(true)
  })

  it('locks approved diagrams unless lockApproved is disabled', async () => {
    const { container, onSave } = await mountEditor({ lockApproved: true })
    fireEvent.keyDown(root(container), { key: 's', ctrlKey: true })
    await flush()
    expect(onSave).not.toHaveBeenCalled()
  })

  it('opens the shortcut help with „?“ and the element search with Ctrl+F', async () => {
    const { container } = await mountEditor()
    fireEvent.keyDown(root(container), { key: '?' })
    await until(() => Boolean(container.querySelector('[role="dialog"]')))
    expect(container.querySelector('[role="dialog"]')!.textContent).toContain('Rückgängig')
    fireEvent.click(container.querySelector('[role="dialog"] .fa-icon-btn')!)
    fireEvent.keyDown(root(container), { key: 'f', ctrlKey: true })
    await until(() => Boolean(container.querySelector('[role="dialog"] input')))
  })

  it('reports import errors instead of throwing', async () => {
    const onError = vi.fn()
    render(<FlowauditEditor xml="<kein-bpmn/>" name="X" onError={onError} />)
    await until(() => onError.mock.calls.length > 0)
    expect(onError.mock.calls[0]![0]).toBeTruthy()
  })

  it('re-imports when the xml prop changes and survives strict mode', async () => {
    const onReady = vi.fn()
    const view = render(<StrictMode><FlowauditEditor xml={fixture('schema-1.1.bpmn')} name="A" onReady={onReady} /></StrictMode>)
    await until(() => (view.container.textContent ?? '').includes('Bewilligung'))
    view.rerender(<StrictMode><FlowauditEditor xml={fixture('enrichment.bpmn')} name="A" onReady={onReady} /></StrictMode>)
    await until(() => (view.container.textContent ?? '').includes('Antrag'))
    expect(view.container.querySelectorAll('.djs-container')).toHaveLength(1)
  })
})
