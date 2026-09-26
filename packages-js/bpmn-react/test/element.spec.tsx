import { createRef } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render } from '@testing-library/react'
import { ELEMENT_ATTRIBUTES, ELEMENT_EVENTS } from '@auditcore/bpmn-flowaudit/ui'
import { InMemoryStorage as Storage } from '@auditcore/bpmn-flowaudit'
import { ATTRIBUTE_PROPS, EVENT_PROPS } from '../src/element/contract'
import { FlowauditBpmnEditor, type FlowauditBpmnEditorHandle } from '../src/element/FlowauditBpmnEditor'
import { fixture, until } from './helpers'

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('FlowauditBpmnEditor (React, contract of <flowaudit-bpmn-editor>)', () => {
  it('maps every attribute and event of the web component contract', () => {
    expect(Object.values(ATTRIBUTE_PROPS)).toEqual([...ELEMENT_ATTRIBUTES])
    expect(Object.values(EVENT_PROPS)).toEqual(ELEMENT_EVENTS)
  })

  it('renders the editor from the xml prop and reports ready', async () => {
    const onReady = vi.fn()
    const ref = createRef<FlowauditBpmnEditorHandle>()
    const { container } = render(<FlowauditBpmnEditor ref={ref} xml={fixture('schema-1.1.bpmn')} diagramId="d0" onReady={onReady} className="app" />)
    await until(() => Boolean(container.querySelector('.djs-container')) && onReady.mock.calls.length > 0)
    expect(onReady).toHaveBeenCalledWith({ diagramId: 'd0' })
    expect(container.querySelector('[role="toolbar"]')).not.toBeNull()
    expect(ref.current!.element!.className).toBe('flowaudit-bpmn-editor app')
    expect(await ref.current!.getXml()).toContain('bpmn:definitions')
  })

  it('loads through a storage property and saves back with a save event', async () => {
    const storage = new Storage({ diagrams: { d1: fixture('enrichment.bpmn') } })
    const onSave = vi.fn()
    const { container } = render(<FlowauditBpmnEditor diagramId="d1" storage={storage} onSave={onSave} />)
    await until(() => Boolean(container.querySelector('.djs-container')) && (container.textContent ?? '').includes('Antrag'))
    fireEvent.keyDown(container.querySelector('.fa-editor')!, { key: 's', ctrlKey: true })
    await until(() => onSave.mock.calls.length > 0)
    const [detail] = onSave.mock.calls[0]!
    expect(detail.xml).toContain('bpmn:definitions')
    expect(await storage.loadDiagram('d1')).toBe(detail.xml)
  })

  it('loads from src and reports load errors as error events', async () => {
    const fetchMock = vi.fn(async () => new Response('', { status: 404, statusText: 'Not Found' }))
    vi.stubGlobal('fetch', fetchMock)
    const onError = vi.fn()
    render(<FlowauditBpmnEditor src="/diagramme/nicht-da.bpmn" onError={onError} />)
    await until(() => onError.mock.calls.length > 0)
    expect(fetchMock).toHaveBeenCalledWith('/diagramme/nicht-da.bpmn', expect.anything())
    expect(onError).toHaveBeenCalledWith({ message: '404 Not Found' })
  })

  it('passes read-only to the editor', async () => {
    const { container } = render(<FlowauditBpmnEditor readonly xml={fixture('enrichment.bpmn')} />)
    await until(() => Boolean(container.querySelector('.fa-toolbar .fa-btn--primary')))
    expect(container.querySelector<HTMLButtonElement>('.fa-toolbar .fa-btn--primary')!.disabled).toBe(true)
  })
})
