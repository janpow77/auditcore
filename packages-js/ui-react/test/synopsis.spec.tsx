import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import type { Comparison } from '@flowaudit/ui'
import { FlowauditSynopsis, defineFlowauditElements } from '../src'
import standardJson from '../../ui/demo/pages/synopsis/standard.json'

;(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true
const standard = standardJson as unknown as Comparison
let root: Root | null = null

beforeAll(() => {
  defineFlowauditElements()
})

afterEach(() => {
  act(() => root?.unmount())
  root = null
  document.body.innerHTML = ''
})

describe('FlowauditSynopsis (React)', () => {
  it('setzt comparison als Eigenschaft und leitet navigate und Layoutwechsel weiter', async () => {
    const onNavigate = vi.fn()
    const onLayoutChange = vi.fn()
    const host = document.createElement('div')
    document.body.append(host)
    root = createRoot(host)
    act(() => root?.render(<FlowauditSynopsis comparison={standard} onNavigate={onNavigate} onLayoutChange={onLayoutChange} />))
    await act(() => new Promise((resolve) => setTimeout(resolve, 0)))
    const element = host.querySelector('flowaudit-synopsis') as HTMLElement
    expect(element.querySelector('h2')?.textContent).toBe(standard.title)
    element.querySelector('section')?.dispatchEvent(new KeyboardEvent('keydown', { key: 'n', bubbles: true }))
    expect(onNavigate).toHaveBeenCalledWith(standard.result.rows[0]?.row_id, expect.any(CustomEvent))
    const inline = Array.from(element.querySelectorAll('button')).find((button) => button.textContent?.trim() === 'Im Text')
    inline?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(onLayoutChange).toHaveBeenCalledWith('inline', expect.any(CustomEvent))
  })
})
