import { fireEvent as domEvent } from '@testing-library/dom'
import { fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import IdentifierCheck from '../../../ui/src/identifiers/IdentifierCheck.vue'
import { BATCH_CSV, fakeIdentifiersPort } from '../../../ui-core/test/identifiers/fake-port'
import { identifierCases } from '../../../ui-core/test/parity/cases-identifiers'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditIdentifierCheck } from '../../src/identifiers/FlowauditIdentifierCheck'
import { both, byTestId } from './interact'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

describe('Parität Kennung prüfen Vue ↔ React', () => {
  for (const entry of identifierCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(IdentifierCheck, { ...entry.props() }, <FlowauditIdentifierCheck {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

async function upload(rendered: Rendered, file: File): Promise<void> {
  for (const [root, events] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
    const input = root.querySelector('[data-testid="ident-file"]') as HTMLInputElement
    Object.defineProperty(input, 'files', { value: [file], configurable: true })
    events.change(input)
    for (let i = 0; i < 3; i += 1) {
      await flushPromises()
      await tick()
    }
  }
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

describe('Parität Kennung prüfen nach Interaktion', () => {
  it('Einzelprüfung mit Land, Profilwechsel, Pflichtangaben', async () => {
    const vuePort = fakeIdentifiersPort()
    const reactPort = fakeIdentifiersPort()
    const rendered = await renderBoth(IdentifierCheck, { port: vuePort }, <FlowauditIdentifierCheck port={reactPort} />)
    await both(rendered, byTestId('ident-kind'), { kind: 'change', value: 'vat_id' })
    await both(rendered, byTestId('ident-value'), { kind: 'input', value: '136695976' })
    await both(rendered, byTestId('ident-country'), { kind: 'input', value: 'de' })
    await both(rendered, byTestId('ident-check'), { kind: 'submit' })
    expect(rendered.react.querySelector('[data-testid="ident-result"]')?.textContent).toContain('gültig')
    await both(rendered, byTestId('ident-kind'), { kind: 'change', value: 'iban' })
    await both(rendered, byTestId('ident-check'), { kind: 'submit' })
    expect(rendered.react.querySelector('[data-testid="ident-result"]')?.textContent).toContain('IBAN-Prüfziffer ist falsch')
    await both(rendered, byTestId('ident-profile'), { kind: 'change', value: 'flowworkshop.legacy' })
    expect(rendered.react.querySelectorAll('[data-testid="ident-kind"] option')).toHaveLength(2)
    await both(rendered, byTestId('ident-profile'), { kind: 'change', value: '' })
    await both(rendered, byTestId('ident-check'), { kind: 'submit' })
    expect(rendered.react.querySelector('.fa-ident__error')?.textContent).toBe('Prüfprofil wählen.')
    expect(reactPort.calls).toEqual(vuePort.calls)
  })

  it('Stapelprüfung: Datei laden, Spalten zuordnen, prüfen, Auffälligkeiten filtern', async () => {
    const vuePort = fakeIdentifiersPort()
    const reactPort = fakeIdentifiersPort()
    const rendered = await renderBoth(IdentifierCheck, { port: vuePort }, <FlowauditIdentifierCheck port={reactPort} />)
    await upload(rendered, new File([BATCH_CSV], 'kennungen.csv', { type: 'text/csv' }))
    await both(rendered, byTestId('ident-batch-kind'), { kind: 'change', value: '' })
    await both(rendered, byTestId('ident-batch-run'), { kind: 'submit' })
    expect(rendered.react.querySelector('.fa-ident__error')?.textContent).toBe('Kennungsart für alle Zeilen oder eine Spalte mit Kennungsart wählen.')
    await both(rendered, byTestId('ident-col-value'), { kind: 'change', value: '2' })
    await both(rendered, byTestId('ident-col-kind'), { kind: 'change', value: '1' })
    await both(rendered, byTestId('ident-col-ref'), { kind: 'change', value: '0' })
    await both(rendered, byTestId('ident-batch-run'), { kind: 'submit' })
    expect(rendered.react.querySelectorAll('.fa-ident__table tbody tr')).toHaveLength(5)
    await both(rendered, byTestId('ident-only-issues'), { kind: 'click' })
    expect(rendered.react.querySelectorAll('.fa-ident__table tbody tr')).toHaveLength(3)
    expect(reactPort.calls.batch).toEqual(vuePort.calls.batch)
    expect(reactPort.calls.batch).toHaveLength(1)
  })
})
