import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import type { Evaluation } from '@flowaudit/ui'
import { FlowauditRiskFlags, defineFlowauditElements } from '../src'
import evaluationJson from '../../ui/test/risk/fixtures/evaluation-year-bound.json'

;(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

const evaluation = evaluationJson as unknown as Evaluation
let root: Root | null = null
let host: HTMLElement

beforeAll(() => {
  defineFlowauditElements()
})

afterEach(() => {
  act(() => root?.unmount())
  root = null
  document.body.innerHTML = ''
})

const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('FlowauditRiskFlags', () => {
  it('übergibt die Auswertung als Eigenschaft und meldet die Datensatzauswahl', async () => {
    const onRecordSelect = vi.fn()
    host = document.createElement('div')
    document.body.append(host)
    root = createRoot(host)
    act(() => root?.render(<FlowauditRiskFlags evaluation={evaluation} heading="Belege VP-19" onRecordSelect={onRecordSelect} />))
    await act(flush)
    const element = host.querySelector('flowaudit-risk-flags') as HTMLElement
    expect(element.querySelector('h2')?.textContent).toBe('Belege VP-19')
    expect(element.querySelectorAll('.fa-risk-table tbody tr')).toHaveLength(10)
    element.querySelector('.fa-risk-table tbody tr')?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await act(flush)
    expect(onRecordSelect).toHaveBeenCalledWith(0, expect.any(CustomEvent))
    expect(element.querySelector('[data-testid="risk-detail"]')?.textContent).toContain('Datensatz B-001')
  })
})
