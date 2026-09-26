import { describe, it } from 'vitest'
import { fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import FieldFormVue from '../../../bpmn-vue/src/panels/FieldForm.vue'
import ListEditorVue from '../../../bpmn-vue/src/panels/ListEditor.vue'
import LegalBasisEditorVue from '../../../bpmn-vue/src/panels/legal/LegalBasisEditor.vue'
import LegalSearchVue from '../../../bpmn-vue/src/panels/legal/LegalSearch.vue'
import MarkerPickerVue from '../../../bpmn-vue/src/panels/tabs/MarkerPicker.vue'
import { FIELD_FORM_CASES, LEGAL_CASES, LIST_EDITOR_CASES, MARKER_CASES } from '../../../bpmn-flowaudit/test/parity/cases-panels'
import { FieldForm } from '../../src/panels/FieldForm'
import { ListEditor } from '../../src/panels/ListEditor'
import { LegalBasisEditor } from '../../src/panels/legal/LegalBasisEditor'
import { LegalSearch } from '../../src/panels/legal/LegalSearch'
import { MarkerPicker } from '../../src/panels/tabs/MarkerPicker'
import { flush } from '../helpers'
import { expectParity, renderBoth, type Rendered } from './setup'

const noop = () => undefined

/** Same interaction on both trees, then settle both frameworks. */
async function onBoth(rendered: Rendered, act: (root: HTMLElement) => void): Promise<void> {
  act(rendered.vue)
  act(rendered.react)
  await flushPromises()
  await flush()
}

describe('parity: FieldForm', () => {
  for (const item of FIELD_FORM_CASES) {
    it(item.name, async () => {
      const props = item.props()
      expectParity(await renderBoth(FieldFormVue, props, <FieldForm {...props} onUpdate={noop} />), item.expect)
    })
  }
})

describe('parity: ListEditor', () => {
  for (const item of LIST_EDITOR_CASES) {
    it(item.name, async () => {
      const props = item.props()
      expectParity(await renderBoth(ListEditorVue, props, <ListEditor {...props} onUpdate={noop} />), item.expect)
    })
  }

  it('after opening an entry and editing a field', async () => {
    const props = LIST_EDITOR_CASES[0]!.props()
    const rendered = await renderBoth(ListEditorVue, props, <ListEditor {...props} onUpdate={noop} />)
    await onBoth(rendered, (root) => fireEvent.click(root.querySelectorAll('.fa-list-editor__toggle')[1]!))
    await onBoth(rendered, (root) => {
      const input = root.querySelector<HTMLInputElement>('.fa-field-form input.fa-input')!
      fireEvent.change(input, { target: { value: 'K2a' } })
    })
    expectParity(rendered, { counts: { '.fa-field-form': 1 } })
  })
})

describe('parity: legal bases', () => {
  for (const item of LEGAL_CASES) {
    it(item.name, async () => {
      const props = item.props()
      expectParity(await renderBoth(LegalBasisEditorVue, props, <LegalBasisEditor {...props} onUpdate={noop} />), item.expect)
    })
  }

  it('opened legacy entry and structured entry', async () => {
    const props = { items: [...LEGAL_CASES[0]!.props().items, ...LEGAL_CASES[1]!.props().items] }
    const rendered = await renderBoth(LegalBasisEditorVue, props, <LegalBasisEditor {...props} onUpdate={noop} />)
    await onBoth(rendered, (root) => fireEvent.click(root.querySelectorAll('.fa-list-editor__toggle')[1]!))
    expectParity(rendered, { texts: ['interne Weisung'] })
    await onBoth(rendered, (root) => fireEvent.click(root.querySelectorAll('.fa-list-editor__toggle')[0]!))
    expectParity(rendered, { counts: { '.fa-field-form': 1 } })
  })

  it('search with a typed citation', async () => {
    const rendered = await renderBoth(LegalSearchVue, {}, <LegalSearch onChoose={noop} />)
    expectParity(rendered)
    await onBoth(rendered, (root) => fireEvent.input(root.querySelector('input')!, { target: { value: 'Art. 74 VO (EU) 2021/1060' } }))
    expectParity(rendered, { roles: [['option', /Art\. 74/]] })
  })
})

describe('parity: MarkerPicker', () => {
  for (const item of MARKER_CASES) {
    it(item.name, async () => {
      const props = item.props()
      expectParity(await renderBoth(MarkerPickerVue, props, <MarkerPicker {...props} onUpdate={noop} />), item.expect)
    })
  }
})
