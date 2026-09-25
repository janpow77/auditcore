import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { FlowauditBenford, FlowauditSampling, defineFlowauditElements } from '../src'
import analysis from '../../ui/test/fixtures/benford-analysis.json'
import benfordProfiles from '../../ui/test/fixtures/benford-profiles.json'
import samplingProfiles from '../../ui/test/fixtures/sampling-profiles.json'

;(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

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

function render(node: React.ReactNode): void {
  host = document.createElement('div')
  document.body.append(host)
  root = createRoot(host)
  act(() => root?.render(node))
}

const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('React-Hüllen Stichprobe und Benford', () => {
  it('übergibt den Port als Eigenschaft an flowaudit-sampling', async () => {
    const port = { profiles: vi.fn(async () => samplingProfiles), size: vi.fn(), allocation: vi.fn(), selection: vi.fn(), exportSelection: vi.fn() }
    render(<FlowauditSampling port={port as never} items={[{ id: 'a', value: 1 }]} />)
    await act(flush)
    await act(flush)
    expect(port.profiles).toHaveBeenCalled()
    expect(host.querySelector('[data-testid="sampling-population"]')?.textContent).toContain('1 Elemente')
  })

  it('leitet analysis-completed an onAnalysisCompleted weiter', async () => {
    const onAnalysisCompleted = vi.fn()
    const port = { profiles: vi.fn(async () => benfordProfiles), analyse: vi.fn(async () => analysis) }
    render(<FlowauditBenford port={port as never} values={[1, 2, 3]} onAnalysisCompleted={onAnalysisCompleted} />)
    await act(flush)
    await act(flush)
    await act(async () => {
      host.querySelector('form')?.dispatchEvent(new Event('submit'))
      await flush()
    })
    expect(onAnalysisCompleted).toHaveBeenCalledWith(analysis, expect.any(CustomEvent))
  })
})
