import { useState, type ReactElement } from 'react'
import { flushPromises } from '@vue/test-utils'
import { describe, it } from 'vitest'
import { defineComponent, h, ref, type Component } from 'vue'
import type { KeyKind } from '@flowaudit/bpmn-flowaudit'
import { checkExpectation } from '../../../ui-core/test/parity/expect'
import { ENRICHMENT_CASE, EXPORT_CASE, fixtureModel, INFO_CASE, ISSUE_CASE, KEY_FILTER_CASE, SEARCH_CASE, SHORTCUT_CASE, XML_CASE, type DialogCase } from '../../../bpmn-flowaudit/test/parity/cases-dialogs'
import VueInfo from '../../../bpmn-vue/src/components/dialogs/DiagramInfoDialog.vue'
import VueSearch from '../../../bpmn-vue/src/components/dialogs/ElementSearch.vue'
import VueEnrichment from '../../../bpmn-vue/src/components/dialogs/EnrichmentDialog.vue'
import VueExport from '../../../bpmn-vue/src/components/dialogs/ExportDialog.vue'
import VueShortcuts from '../../../bpmn-vue/src/components/dialogs/ShortcutHelp.vue'
import VueXml from '../../../bpmn-vue/src/components/dialogs/XmlDialog.vue'
import VueIssues from '../../../bpmn-vue/src/components/views/IssueList.vue'
import VueKeyFilter from '../../../bpmn-vue/src/components/views/KeyFilterBar.vue'
import { provideEditorContext, type EditorContext as VueContext } from '../../../bpmn-vue/src/stores/context'
import { EditorContextProvider, type EditorContext } from '../../src/context'
import { DiagramInfoDialog, type DiagramInfoDialogProps } from '../../src/dialogs/DiagramInfoDialog'
import { ElementSearch, type ElementSearchProps } from '../../src/dialogs/ElementSearch'
import { EnrichmentDialog, type EnrichmentDialogProps } from '../../src/dialogs/EnrichmentDialog'
import { ExportDialog, type ExportDialogProps } from '../../src/dialogs/ExportDialog'
import { ShortcutHelp } from '../../src/dialogs/ShortcutHelp'
import { XmlDialog, type XmlDialogProps } from '../../src/dialogs/XmlDialog'
import { IssueList, type IssueListProps } from '../../src/views/IssueList'
import { KeyFilterBar } from '../../src/views/KeyFilterBar'
import { flush } from '../helpers'
import { expectParity, renderBoth, type Rendered } from './setup'

const noop = () => undefined
type Props = Record<string, unknown>

/** Types into an input or text area the way a user does (native setter + `input` event). */
function typeInto(element: HTMLInputElement | HTMLTextAreaElement, value: string): void {
  const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(element), 'value')?.set
  setter?.call(element, value)
  element.dispatchEvent(new Event('input', { bubbles: true }))
}

async function interact(rendered: Rendered, test: DialogCase<Props>): Promise<void> {
  for (const root of [rendered.vue, rendered.react]) {
    if (test.type) typeInto(root.querySelector(test.type.selector) as HTMLInputElement, test.type.value)
    if (test.click) (root.querySelectorAll<HTMLElement>(test.click.selector)[test.click.index ?? 0] as HTMLElement).click()
  }
  await flushPromises()
  await flush()
  await flushPromises()
}

async function runCase(test: DialogCase<Props>, vue: Component, react: (props: Props) => ReactElement, props: Props = test.props()): Promise<void> {
  const rendered = await renderBoth(vue, props, react(props))
  expectParity(rendered, test.expect)
  if (!test.type && !test.click) return
  await interact(rendered, test)
  expectParity(rendered, test.after ?? {})
  if (test.after) checkExpectation(rendered.react, test.after)
}

const fakeStore = <S extends object>(state: S) => ({ get: () => state, set: noop, subscribe: () => noop })
const reactContext = { editor: { store: fakeStore({ ready: false, changes: 0, info: null }) }, selection: { store: fakeStore({ element: null, version: 0 }) }, validation: { store: fakeStore({ local: [], server: [], running: false, error: null }) }, ports: {}, profile: () => null, readonly: () => false } as unknown as EditorContext
const vueContext = { editor: { state: { ready: false, changes: 0 } }, selection: {}, validation: {}, ports: {}, profile: () => null, readonly: () => false } as unknown as VueContext

const VueInfoInContext = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs }) {
    provideEditorContext(vueContext)
    return () => h(VueInfo, attrs)
  },
})

const VueKeyFilterState = defineComponent({
  inheritAttrs: false,
  setup(_, { attrs }) {
    const kind = ref(attrs.kind as KeyKind)
    const value = ref(attrs.value as string)
    return () => h(VueKeyFilter, { ...attrs, kind: kind.value, value: value.value, 'onUpdate:kind': (next: KeyKind) => (kind.value = next), 'onUpdate:value': (next: string) => (value.value = next) })
  },
})

function ReactKeyFilterState(props: Props) {
  const [kind, setKind] = useState(props.kind as KeyKind)
  const [value, setValue] = useState(props.value as string)
  return <KeyFilterBar keys={props.keys as Record<KeyKind, Record<string, string[]>>} kind={kind} value={value} hits={props.hits as number} onKindChange={setKind} onValueChange={setValue} onClear={noop} />
}

describe('parity of dialogs and views (Vue ↔ React)', () => {
  it(EXPORT_CASE.name, () => runCase(EXPORT_CASE, VueExport, (p) => <ExportDialog {...(p as unknown as ExportDialogProps)} onOpenChange={noop} onExport={noop} />))
  it(ENRICHMENT_CASE.name, () => runCase(ENRICHMENT_CASE, VueEnrichment, (p) => <EnrichmentDialog {...(p as unknown as EnrichmentDialogProps)} onOpenChange={noop} onApply={noop} />))
  it(XML_CASE.name, () => runCase(XML_CASE, VueXml, (p) => <XmlDialog {...(p as unknown as XmlDialogProps)} onOpenChange={noop} onApply={noop} />))
  it(SHORTCUT_CASE.name, () => runCase(SHORTCUT_CASE, VueShortcuts, () => <ShortcutHelp open onOpenChange={noop} />))
  it(SEARCH_CASE.name, async () => {
    const props = { ...SEARCH_CASE.props(), model: await fixtureModel() }
    await runCase({ ...SEARCH_CASE, after: { roles: [['option', /Antrag eingegangen/]] } }, VueSearch, (p) => <ElementSearch {...(p as unknown as ElementSearchProps)} onOpenChange={noop} onJump={noop} />, props)
  })
  it(ISSUE_CASE.name, () => runCase(ISSUE_CASE, VueIssues, (p) => <IssueList {...(p as unknown as IssueListProps)} />))
  it(KEY_FILTER_CASE.name, () => runCase(KEY_FILTER_CASE, VueKeyFilterState, (p) => <ReactKeyFilterState {...p} />))
  it(INFO_CASE.name, () =>
    runCase(INFO_CASE, VueInfoInContext, (p) => (
      <EditorContextProvider value={reactContext}>
        <DiagramInfoDialog {...(p as unknown as DiagramInfoDialogProps)} onOpenChange={noop} />
      </EditorContextProvider>
    )),
  )
})
