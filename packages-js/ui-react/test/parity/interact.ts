/** Dieselbe Interaktion auf Vue- und React-Fassung, danach DOM und Formularzustand vergleichen. */
import { fireEvent as domEvent } from '@testing-library/dom'
import { fireEvent } from '@testing-library/react'
import { flushPromises } from '@vue/test-utils'
import { expect } from 'vitest'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { tick, type Rendered } from './setup'

export type Step = (root: HTMLElement) => Element | null | undefined

export type Action = { kind: 'click' } | { kind: 'input' | 'change'; value: string } | { kind: 'submit' }

export const byTestId = (id: string): Step => (root) => root.querySelector(`[data-testid="${id}"]`)

function fire(target: Element, action: Action, events: typeof domEvent | typeof fireEvent): void {
  if (action.kind === 'click') events.click(target)
  else if (action.kind === 'submit') events.submit(target.closest('form') ?? target)
  else events[action.kind](target, { target: { value: action.value } })
}

export async function both(rendered: Rendered, find: Step, action: Action): Promise<void> {
  for (const [root, events] of [[rendered.vue, domEvent], [rendered.react, fireEvent]] as const) {
    const target = find(root)
    expect(target, 'Ziel der Interaktion fehlt').toBeTruthy()
    fire(target as Element, action, events)
    await flushPromises()
    await tick()
    await flushPromises()
    await tick()
  }
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}
