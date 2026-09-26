import { FaVvt } from '@flowaudit/ui'
import { fireEvent as domEvent } from '@testing-library/dom'
import { act, fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { vvtCases } from '../../../ui-core/test/parity/cases-vvt'
import { fakePort } from '../../../ui-core/test/dataprotection/fake-port'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditVvt } from '../../src/dataprotection/FlowauditVvt'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

describe('Parität VVT Vue ↔ React', () => {
  for (const entry of vvtCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(FaVvt, { ...entry.props() }, <FlowauditVvt {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

type Step = (root: HTMLElement) => Element | null | undefined

/** Dieselbe Interaktion auf beiden Fassungen, danach DOM und Formularzustand vergleichen. */
async function both(rendered: Rendered, find: Step, event: 'click' | 'input' | 'change', value?: string | boolean): Promise<void> {
  for (const [root, fire] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
    const target = find(root) as HTMLInputElement
    expect(target, 'Ziel der Interaktion fehlt').toBeTruthy()
    if (typeof value === 'boolean') fire.click(target)
    else if (value !== undefined) fire[event === 'change' ? 'change' : 'input'](target, { target: { value } })
    else fire.click(target)
    await flushPromises()
    await tick()
  }
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

const button = (label: string): Step => (root) => Array.from(root.querySelectorAll('button')).find((node) => node.textContent?.trim() === label)

describe('Parität VVT nach Interaktion', () => {
  it('Tätigkeit wählen, Feld ändern, Historie, Referat anlegen, Freigabe anzeigen', async () => {
    const rendered = await renderBoth(FaVvt, { port: fakePort(), actor: 'daten-b' }, <FlowauditVvt port={fakePort()} actor="daten-b" />)
    await both(rendered, (root) => root.querySelectorAll('.fa-vvt__item')[2], 'click')
    await both(rendered, (root) => root.querySelector('[data-testid="vvt-detail"] textarea'), 'input', 'Zweck neu')
    await both(rendered, (root) => root.querySelector('[data-testid="vvt-detail"] input[type="radio"]'), 'click', true)
    await both(rendered, button('Versionshistorie'), 'click')
    await both(rendered, (root) => root.querySelector('[data-testid="vvt-cover"] .fa-dataprotection__bar input'), 'input', 'Referat Z 9')
    await both(rendered, button('Referat hinzufügen'), 'click')
    await both(rendered, button('Änderungen verwerfen'), 'click')
    await both(rendered, button('Freigegebene Fassung anzeigen'), 'click')
    await act(async () => undefined)
  })
})
