import { fireEvent as domEvent } from '@testing-library/dom'
import { act, fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ScreeningReview from '../../../ui/src/screening/ScreeningReview.vue'
import { screeningCases } from '../../../ui-core/test/parity/cases-screening'
import { fakePort, run } from '../../../ui-core/test/screening/fake-port'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { FlowauditScreeningReview } from '../../src/screening/FlowauditScreeningReview'
import { expectParity, renderBoth, tick, type Rendered } from './setup'

describe('Parität Screening-Trefferprüfung Vue ↔ React', () => {
  for (const entry of screeningCases) {
    it(entry.name, async () => {
      const rendered = await renderBoth(ScreeningReview, { ...entry.props() }, <FlowauditScreeningReview {...entry.props()} />)
      expectParity(rendered, entry.expect)
    })
  }
})

type Step = (root: HTMLElement) => Element | null | undefined
type Action = { kind: 'click' } | { kind: 'input' | 'change'; value: string } | { kind: 'submit' }

/** Dieselbe Interaktion auf beiden Fassungen, danach DOM und Formularzustand vergleichen. */
async function both(rendered: Rendered, find: Step, action: Action): Promise<void> {
  for (const [root, fire] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
    const target = find(root) as HTMLInputElement
    expect(target, 'Ziel der Interaktion fehlt').toBeTruthy()
    if (action.kind === 'click') fire.click(target)
    else if (action.kind === 'submit') fire.submit(target)
    else fire[action.kind](target, { target: { value: action.value } })
    await flushPromises()
    await tick()
  }
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

/** Beide Fassungen zeigen den Text (die Interaktion hat gewirkt). */
function shows(rendered: Rendered, text: string, present = true): void {
  for (const root of [rendered.vue, rendered.react]) expect(root.textContent?.includes(text)).toBe(present)
}

const button = (label: string): Step => (root) => Array.from(root.querySelectorAll('button')).find((node) => node.textContent?.trim() === label)
const decision = '[aria-labelledby="fa-screening-decision-title"]'
const filterSelect = (index: number): Step => (root) => root.querySelectorAll('.fa-screening__filters select')[index]

describe('Parität Screening nach Interaktion', () => {
  it('Treffer wählen, Entscheidung mit Pflichtbegründung, Filter, nächster Treffer', async () => {
    const rendered = await renderBoth(ScreeningReview, { port: fakePort(), runId: run.run_id }, <FlowauditScreeningReview port={fakePort()} runId={run.run_id} />)
    await both(rendered, (root) => root.querySelectorAll('.fa-screening__hit')[1], { kind: 'click' })
    await both(rendered, button('Treffer verwerfen'), { kind: 'click' })
    await both(rendered, (root) => root.querySelector(`${decision} form`), { kind: 'submit' })
    shows(rendered, 'Eine Begründung ist Pflicht.')
    await both(rendered, (root) => root.querySelector(`${decision} textarea`), { kind: 'input', value: 'Geburtsjahr widerspricht.' })
    await both(rendered, (root) => root.querySelector(`${decision} input[type="checkbox"]`), { kind: 'click' })
    await both(rendered, filterSelect(0), { kind: 'change', value: 'open' })
    expect(rendered.react.querySelectorAll('.fa-screening__hit')).toHaveLength(1)
    await both(rendered, (root) => root.querySelector('.fa-screening__filters input[type="search"]'), { kind: 'input', value: 'beispiel' })
    await both(rendered, filterSelect(0), { kind: 'change', value: '' })
    await both(rendered, button('Nächster offener Treffer'), { kind: 'click' })
    await act(async () => undefined)
  })

  it('neuer Prüflauf: Prüfart wechseln, Formularfehler, Lauf öffnen', async () => {
    const rendered = await renderBoth(ScreeningReview, { port: fakePort() }, <FlowauditScreeningReview port={fakePort()} />)
    await both(rendered, (root) => root.querySelectorAll('input[name="fa-screening-kind"]')[1], { kind: 'click' })
    shows(rendered, 'flowinvoice.pep_bulk')
    await both(rendered, (root) => root.querySelector('[data-testid="screening-start"]')?.closest('form'), { kind: 'submit' })
    shows(rendered, 'Mindestens einen Namen angeben.')
    await both(rendered, (root) => root.querySelectorAll('input[name="fa-screening-kind"]')[0], { kind: 'click' })
    await both(rendered, (root) => root.querySelector('.fa-screening__runs button'), { kind: 'click' })
    shows(rendered, 'Score-Aufschlüsselung')
    await act(async () => undefined)
  })
})
