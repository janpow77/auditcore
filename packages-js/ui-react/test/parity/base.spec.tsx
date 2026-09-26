import { FaButton, FaDialog, FaTextField } from '@flowaudit/ui'
import { flushPromises, mount } from '@vue/test-utils'
import { cleanup, fireEvent, render } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { buttonCases, dialogCases, textFieldCases } from '../../../ui-core/test/parity/cases-base'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { checkExpectation } from '../../../ui-core/test/parity/expect'
import { Button, Dialog, TextField } from '../../src'
import { expectParity, renderBoth } from './setup'

describe('Parität Basiskomponenten Vue ↔ React', () => {
  for (const entry of buttonCases) {
    it(`Schaltfläche: ${entry.name}`, async () => {
      expectParity(await renderBoth(FaButton, { ...entry.props() }, <Button {...entry.props()} />), entry.expect)
    })
  }
  for (const entry of textFieldCases) {
    it(`Eingabefeld: ${entry.name}`, async () => {
      const { modelValue = '', ...rest } = entry.props()
      expectParity(await renderBoth(FaTextField, { ...entry.props() }, <TextField {...rest} value={modelValue} onChange={() => undefined} />), entry.expect)
    })
  }
  for (const entry of dialogCases) {
    it(`Dialog: ${entry.name}`, async () => {
      // Beide Fassungen rendern in document.body (Teleport bzw. Portal); nacheinander vergleichen.
      const wrapper = mount(FaDialog, { props: { ...entry.props() }, attachTo: document.body })
      await flushPromises()
      const vue = document.body.querySelector('.fa-dialog') as HTMLElement
      checkExpectation(vue, entry.expect)
      const vueDom = normalizeDom(vue)
      const vueForm = formState(vue)
      wrapper.unmount()
      render(<Dialog {...entry.props()} onClose={() => undefined} />)
      const react = document.body.querySelector('.fa-dialog') as HTMLElement
      checkExpectation(react, entry.expect)
      expect(normalizeDom(react)).toBe(vueDom)
      expect(formState(react)).toEqual(vueForm)
      cleanup()
    })
  }
})

describe('Dialog (nativ)', () => {
  it('fängt den Fokus, schließt mit Escape und Hintergrund und gibt den Fokus zurück', () => {
    const opener = document.createElement('button')
    document.body.append(opener)
    opener.focus()
    const onClose = vi.fn()
    const view = render(<Dialog open title="Freigabe" onClose={onClose} footer={<button type="button">OK</button>} />)
    const panel = document.querySelector('[role="dialog"]') as HTMLElement
    expect(panel.contains(document.activeElement)).toBe(true)
    fireEvent.keyDown(panel, { key: 'Escape' })
    fireEvent.mouseDown(document.querySelector('.fa-dialog') as HTMLElement)
    expect(onClose).toHaveBeenCalledTimes(2)
    view.rerender(<Dialog open={false} title="Freigabe" onClose={onClose} />)
    expect(document.activeElement).toBe(opener)
  })
})
