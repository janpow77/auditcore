/**
 * Editor parity Vue ↔ React: both `FlowauditEditor`s load the same fixture,
 * run the same steps and are compared part by part; XML output (load, save,
 * export, re-import) must be identical.
 */
import { createRef } from 'react'
import { describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { fireEvent, render } from '@testing-library/react'
import { FlowauditEditor as VueEditor } from '@flowaudit/bpmn-vue'
import { EDITOR_CASES, type EditorParityCase, type EditorStep } from '../../../bpmn-flowaudit/test/parity/cases-editor'
import { checkExpectation } from '../../../ui-core/test/parity/expect'
import { FlowauditEditor } from '../../src/FlowauditEditor'
import type { FlowauditEditorHandle } from '../../src/editorProps'
import { fixture, flush, until } from '../helpers'
import { expectPartParity } from './setup'

interface Side {
  root: HTMLElement
  select: (id: string) => void
  getXml: () => Promise<string | undefined>
}

type VueApi = { select(id: string): void; getXml(): Promise<string> }

async function mountVue(testCase: EditorParityCase, xml: string, onSave: (xml: string) => void): Promise<Side> {
  const host = document.body.appendChild(document.createElement('div'))
  const wrapper = mount(VueEditor, { props: { xml, name: testCase.props?.name ?? 'Muster', lockApproved: false, ...testCase.props, onSave: (payload: { xml: string }) => onSave(payload.xml) }, attachTo: host })
  const api = wrapper.vm as unknown as VueApi
  return { root: wrapper.element as HTMLElement, select: (id) => api.select(id), getXml: () => api.getXml() }
}

function mountReact(testCase: EditorParityCase, xml: string, onSave: (xml: string) => void): Side {
  const ref = createRef<FlowauditEditorHandle>()
  const { container } = render(<FlowauditEditor ref={ref} xml={xml} name={testCase.props?.name ?? 'Muster'} lockApproved={false} {...testCase.props} onSave={(payload) => onSave(payload.xml)} />)
  return { root: container.firstElementChild as HTMLElement, select: (id) => void ref.current?.select(id), getXml: async () => ref.current?.getXml() }
}

const loaded = (side: Side) => Boolean(side.root.querySelector('.djs-container')) && Boolean(side.root.querySelector('.fa-statusbar'))

function target(side: Side, selector: string): Element {
  const element = side.root.matches(selector) ? side.root : side.root.querySelector(selector)
  if (!element) throw new Error(`Ziel fehlt: ${selector}`)
  return element
}

/** Typing as Vue's `setValue` does it: `input`, then `change`. */
function typeInto(element: Element, value: string): void {
  fireEvent.input(element, { target: { value } })
  fireEvent.change(element, { target: { value } })
}

function runStep(side: Side, step: EditorStep): void {
  if (step.kind === 'select') return side.select(step.id)
  const element = target(side, step.target)
  if (step.kind === 'key') fireEvent.keyDown(element, { key: step.key, ctrlKey: Boolean(step.ctrl) })
  else if (step.kind === 'click') fireEvent.click(element)
  else typeInto(element, step.value)
}

async function settle(): Promise<void> {
  await flush()
  await flushPromises()
  await flush()
}

async function both(testCase: EditorParityCase) {
  const xml = fixture(testCase.fixture)
  const saved = { vue: [] as string[], react: [] as string[] }
  const vue = await mountVue(testCase, xml, (value) => saved.vue.push(value))
  const react = mountReact(testCase, xml, (value) => saved.react.push(value))
  await until(() => loaded(vue) && loaded(react))
  for (const step of testCase.steps) {
    runStep(vue, step)
    runStep(react, step)
    await settle()
  }
  return { vue, react, saved }
}

describe('FlowauditEditor parity Vue ↔ React', () => {
  it.each(EDITOR_CASES.map((testCase) => [testCase.name, testCase] as const))('%s', async (_name, testCase) => {
    const { vue, react } = await both(testCase)
    checkExpectation(vue.root, testCase.expect)
    checkExpectation(react.root, testCase.expect)
    for (const part of testCase.parts) expectPartParity({ vue: vue.root, react: react.root }, part)
  })

  it('loads, saves and exports the same XML (round trip)', async () => {
    const testCase = EDITOR_CASES[0]!
    const { vue, react, saved } = await both(testCase)
    const [vueXml, reactXml] = [await vue.getXml(), await react.getXml()]
    expect(reactXml).toBe(vueXml)
    fireEvent.keyDown(vue.root, { key: 's', ctrlKey: true })
    fireEvent.keyDown(react.root, { key: 's', ctrlKey: true })
    await until(() => saved.vue.length > 0 && saved.react.length > 0)
    expect(saved.react[0]).toBe(saved.vue[0])
    const again = await both({ ...testCase, fixture: testCase.fixture })
    expect(await again.react.getXml()).toBe(reactXml)
  })

  it('writes the same XML after the same property edit', async () => {
    const testCase = EDITOR_CASES[1]!
    const { vue, react } = await both(testCase)
    for (const side of [vue, react]) {
      const input = target(side, '.fa-tab-general input')
      typeInto(input, 'Antrag abschließend bewilligen')
      fireEvent.blur(input)
    }
    await settle()
    const [vueXml, reactXml] = [await vue.getXml(), await react.getXml()]
    expect(vueXml).toContain('name="Antrag abschließend bewilligen"')
    expect(reactXml).toBe(vueXml)
    expectPartParity({ vue: vue.root, react: react.root }, '.fa-side')
    expectPartParity({ vue: vue.root, react: react.root }, '.fa-toolbar')
  })
})
