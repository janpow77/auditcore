import { afterEach, describe, expect, it, vi } from 'vitest'
import { InMemoryStorage, type DiagramInfo } from '@auditcore/bpmn-flowaudit'
import { ELEMENT_EVENTS, ELEMENT_NAME, registerFlowauditBpmnEditor } from '../src/web-component/register'
import { readConfig } from '@auditcore/bpmn-flowaudit/ui'
import { fixture, until } from './helpers'

type EditorElement = HTMLElement & { xml?: string; storage?: InMemoryStorage; getXml(): Promise<string> }

afterEach(() => {
  document.body.innerHTML = ''
})

function create(setup: (element: EditorElement) => void): EditorElement {
  const element = document.createElement(ELEMENT_NAME) as EditorElement
  setup(element)
  document.body.appendChild(element)
  return element
}

describe('<flowaudit-bpmn-editor>', () => {
  it('registers once and renders the editor from the xml property', async () => {
    registerFlowauditBpmnEditor()
    expect(customElements.get(ELEMENT_NAME)).toBeDefined()
    const ready = vi.fn()
    const element = create((el) => {
      el.addEventListener('ready', ready)
      el.xml = fixture('schema-1.1.bpmn')
    })
    await until(() => element.querySelector('.djs-container') !== null && ready.mock.calls.length > 0)
    expect(element.querySelector('[role="toolbar"]')).not.toBeNull()
    expect(ELEMENT_EVENTS).toContain('diagram-info-change')
  })

  it('loads through a storage property and saves back with a save event', async () => {
    const storage = new InMemoryStorage({ diagrams: { d1: fixture('enrichment.bpmn') } })
    const saved: { xml: string; info: DiagramInfo | null }[] = []
    const element = create((el) => {
      el.setAttribute('diagram-id', 'd1')
      el.storage = storage
      el.addEventListener('save', (event) => saved.push((event as CustomEvent).detail))
    })
    await until(() => element.querySelector('.djs-container') !== null && element.textContent!.includes('Antrag'))
    element.querySelector('.fa-editor')!.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true, bubbles: true }))
    await until(() => saved.length > 0)
    expect(saved[0]!.xml).toContain('bpmn:definitions')
    expect(await storage.loadDiagram('d1')).toBe(saved[0]!.xml)
  })

  it('loads from src and reports load errors as error events', async () => {
    const fetchMock = vi.fn(async () => new Response('', { status: 404, statusText: 'Not Found' }))
    vi.stubGlobal('fetch', fetchMock)
    const errors: string[] = []
    create((el) => {
      el.addEventListener('error', (event) => errors.push((event as unknown as CustomEvent<{ message: string }>).detail.message))
      el.setAttribute('src', '/diagramme/nicht-da.bpmn')
    })
    await until(() => errors.length > 0)
    vi.unstubAllGlobals()
    expect(fetchMock).toHaveBeenCalledWith('/diagramme/nicht-da.bpmn', expect.anything())
    expect(errors[0]).toBe('404 Not Found')
  })

  it('sets the read-only attribute on the editor', async () => {
    const element = create((el) => {
      el.setAttribute('readonly', '')
      el.xml = fixture('enrichment.bpmn')
    })
    await until(() => element.querySelector('.fa-editor') !== null)
    expect(element.querySelector<HTMLButtonElement>('.fa-toolbar .fa-btn--primary')!.disabled).toBe(true)
  })
})

describe('standalone config', () => {
  it('merges meta tags, window config and query parameters', () => {
    document.head.innerHTML = '<meta name="flowaudit-api-base" content="/meta/api"><meta name="flowaudit-locale" content="en">'
    const win = { document, location: { search: '?profile=foerderperiode-2014-2020' }, FLOWAUDIT_CONFIG: { apiBase: '/intranet/api' } } as unknown as Window
    expect(readConfig(win)).toEqual({ apiBase: '/intranet/api', locale: 'en', profile: 'foerderperiode-2014-2020', author: undefined, title: undefined })
    document.head.innerHTML = ''
    expect(readConfig({ document, location: { search: '' } } as unknown as Window).apiBase).toBe('./api')
  })
})
