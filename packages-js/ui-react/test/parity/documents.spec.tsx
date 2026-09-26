import { describe, expect, it } from 'vitest'
import FaComparisons from '../../../ui/src/documents/FaComparisons.vue'
import { fakePort } from '../../../ui-core/test/documents/fake-port'
import { comparisonsCases } from '../../../ui-core/test/parity/cases-documents'
import { FlowauditComparisons } from '../../src/documents/FlowauditComparisons'
import { both, byTestId } from './interact'
import { expectParity, renderBoth } from './setup'

describe('Parität Dokumentvergleiche Vue ↔ React', () => {
  for (const entry of comparisonsCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(FaComparisons, { ...entry.props() }, <FlowauditComparisons {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

describe('Parität Dokumentvergleiche nach Interaktion', () => {
  it('Absenden ohne Dateien, Gesetzessynopse, Schwelle, Abschnitt, Suche, Öffnen und zurück', async () => {
    const vuePort = fakePort()
    const reactPort = fakePort()
    const rendered = await renderBoth(FaComparisons, { port: vuePort }, <FlowauditComparisons port={reactPort} />)
    await both(rendered, (root) => root.querySelector('form'), { kind: 'submit' })
    expect(rendered.react.querySelector('.fa-comparisons-form__problems')?.textContent).toContain('Die bisherige Fassung fehlt.')
    await both(rendered, (root) => root.querySelector('input[type="number"]'), { kind: 'input', value: '50' })
    await both(rendered, (root) => root.querySelectorAll('.fa-comparisons-form__group input[type="checkbox"]')[7], { kind: 'click' })
    await both(rendered, (root) => root.querySelector('input[type="radio"][value="article_law"]'), { kind: 'click' })
    await both(rendered, (root) => root.querySelector('input[type="search"]'), { kind: 'input', value: 'al_stamm' })
    expect(rendered.react.querySelectorAll('.fa-comparisons-list__item')).toHaveLength(1)
    await both(rendered, (root) => root.querySelector('.fa-comparisons-list__actions button'), { kind: 'click' })
    expect(reactPort.load.mock.calls).toEqual(vuePort.load.mock.calls)
    expect(rendered.react.querySelector('.fa-synopsis')).not.toBeNull()
    await both(rendered, (root) => root.querySelector('.fa-comparisons__open > button'), { kind: 'click' })
    await both(rendered, byTestId('comparisons-oldFile'), { kind: 'change', value: '' })
    expect(reactPort.create).not.toHaveBeenCalled()
  })
})
