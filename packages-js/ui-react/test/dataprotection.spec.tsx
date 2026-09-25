import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { FlowauditDsfa, FlowauditVvt, defineFlowauditElements } from '../src'
import fixture from '../../ui/test/fixtures/dataprotection-contract.json'

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

function render(node: React.ReactNode): void {
  host = document.createElement('div')
  document.body.append(host)
  root = createRoot(host)
  act(() => root?.render(node))
}

describe('React-Hüllen VVT und DSFA', () => {
  it('<FlowauditVvt> übergibt Port und actor und leitet error weiter', async () => {
    const port = {
      profile: vi.fn(async () => fixture.profile),
      register: vi.fn(async () => Promise.reject(new Error('offline'))),
    }
    const onError = vi.fn()
    render(<FlowauditVvt port={port as never} actor="daten-b" onError={onError} />)
    await act(flush)
    await act(flush)
    expect(port.profile).toHaveBeenCalled()
    expect(onError).toHaveBeenCalledWith({ code: 'network_error', message: 'Verbindung fehlgeschlagen: offline', status: 0 }, expect.any(CustomEvent))
    expect(host.querySelector('flowaudit-vvt h2')?.textContent).toContain('Verzeichnis von Verarbeitungstätigkeiten')
  })

  it('<FlowauditDsfa> öffnet die Tätigkeit aus activityId', async () => {
    const port = {
      profile: vi.fn(async () => fixture.profile),
      overview: vi.fn(async () => fixture.overview),
      assessment: vi.fn(async () => fixture.released_assessment),
    }
    render(<FlowauditDsfa port={port as never} activityId="pruefung" />)
    await act(flush)
    await act(flush)
    await act(flush)
    expect(port.assessment).toHaveBeenCalledWith('demo-assessment-1')
    expect(host.querySelector('flowaudit-dsfa [data-testid="dsfa-head"]')?.textContent).toContain('Vorhabenprüfung mit Stichprobe')
  })
})
