import { createRef } from 'react'
import { act, cleanup, render } from '@testing-library/react'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { InMemoryStorage } from '@flowaudit/bpmn-flowaudit'
import { FlowauditBpmnEditor, type FlowauditBpmnEditorHandle } from '../src/FlowauditBpmnEditor'
import { ATTRIBUTE_PROPS, EVENT_PROPS } from '../src/contract'
import { defineFakeElement, type FakeEditorElement } from './fakeElement'

beforeAll(defineFakeElement)
afterEach(cleanup)

const element = (container: HTMLElement) => container.querySelector('flowaudit-bpmn-editor') as FakeEditorElement

describe('FlowauditBpmnEditor (React)', () => {
  it('sets string settings as attributes and removes them again', () => {
    const { container, rerender } = render(<FlowauditBpmnEditor apiBase="/api/bpmn" diagramId="d1" locale="en" readonly theme="dark" className="editor" />)
    const el = element(container)
    expect(el.getAttribute('api-base')).toBe('/api/bpmn')
    expect(el.getAttribute('diagram-id')).toBe('d1')
    expect(el.getAttribute('readonly')).toBe('')
    expect(el.getAttribute('theme')).toBe('dark')
    expect(el.className).toBe('editor')
    rerender(<FlowauditBpmnEditor apiBase="/api/bpmn" readonly={false} />)
    expect(el.hasAttribute('readonly')).toBe(false)
    expect(el.hasAttribute('diagram-id')).toBe(false)
  })

  it('sets objects as element properties', () => {
    const storage = new InMemoryStorage()
    const ports = { validation: { validate: async () => [] } }
    const { container } = render(<FlowauditBpmnEditor xml="<x/>" storage={storage} ports={ports} profileData={null} />)
    const el = element(container)
    expect(el.xml).toBe('<x/>')
    expect(el.storage).toBe(storage)
    expect(el.ports).toBe(ports)
    expect(el.profileData).toBeNull()
    expect(el.getAttribute('xml')).toBeNull()
  })

  it('binds custom events to the onXyz callbacks and uses the latest callbacks', () => {
    const first = vi.fn()
    const second = vi.fn()
    const onSelectionChange = vi.fn()
    const { container, rerender } = render(<FlowauditBpmnEditor onSave={first} onSelectionChange={onSelectionChange} />)
    rerender(<FlowauditBpmnEditor onSave={second} onSelectionChange={onSelectionChange} />)
    act(() => {
      element(container).emit('save', { xml: '<x/>', info: null })
      element(container).emit('selection-change', { elementId: 'Task_1' })
    })
    expect(first).not.toHaveBeenCalled()
    expect(second).toHaveBeenCalledWith({ xml: '<x/>', info: null })
    expect(onSelectionChange).toHaveBeenCalledWith({ elementId: 'Task_1' })
  })

  it('removes the listeners on unmount', () => {
    const onChange = vi.fn()
    const { container, unmount } = render(<FlowauditBpmnEditor onChange={onChange} />)
    const el = element(container)
    unmount()
    el.emit('change', { xml: '<y/>' })
    expect(onChange).not.toHaveBeenCalled()
  })

  it('delegates the ref methods to the element', async () => {
    const ref = createRef<FlowauditBpmnEditorHandle>()
    const { container } = render(<FlowauditBpmnEditor ref={ref} xml="<z/>" />)
    expect(ref.current?.element).toBe(element(container))
    expect(await ref.current?.getXml()).toBe('<z/>')
    expect(await ref.current?.getSvg()).toBe('<svg/>')
    ref.current?.select('Task_2')
    expect(element(container).selected).toBe('Task_2')
  })

  it('maps every attribute and event of the web component', () => {
    expect(Object.values(ATTRIBUTE_PROPS)).toEqual(['src', 'api-base', 'diagram-id', 'name', 'locale', 'theme', 'readonly', 'profile', 'author'])
    expect(Object.values(EVENT_PROPS)).toEqual(['ready', 'change', 'save', 'selection-change', 'diagram-info-change', 'error'])
  })
})
