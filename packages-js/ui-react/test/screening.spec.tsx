import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { FlowauditScreeningReview, defineFlowauditElements } from '../src'
import fixture from '../../ui/test/fixtures/screening-contract.json'

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

const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('React-Hülle Screening-Trefferprüfung', () => {
  it('übergibt Port und runId als Eigenschaften und leitet error weiter', async () => {
    const run = fixture.run as { run_id: string; contract: string }
    const port = {
      settings: vi.fn(async () => fixture.settings),
      sources: vi.fn(async () => fixture.sources),
      runs: vi.fn(async () => ({ contract: run.contract, runs: [fixture.run] })),
      run: vi.fn(async (_runId: string) => fixture.run),
      log: vi.fn(async () => Promise.reject(new Error('offline'))),
      createRun: vi.fn(),
      decide: vi.fn(),
      secondReview: vi.fn(),
    }
    const onError = vi.fn()
    host = document.createElement('div')
    document.body.append(host)
    root = createRoot(host)
    act(() => root?.render(<FlowauditScreeningReview port={port as never} runId={run.run_id} onError={onError} />))
    await act(flush)
    await act(flush)
    expect(port.settings).toHaveBeenCalled()
    expect(port.run.mock.calls[0]?.[0]).toBe(run.run_id)
    expect(onError).toHaveBeenCalledWith({ code: 'network_error', message: 'Verbindung fehlgeschlagen: offline', status: 0 }, expect.any(CustomEvent))
    expect(host.querySelector('flowaudit-screening-review h2')?.textContent).toBe('Screening-Trefferprüfung')
  })
})
