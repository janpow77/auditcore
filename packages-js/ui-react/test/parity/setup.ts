import { flushPromises, mount } from '@vue/test-utils'
import { act, cleanup, render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { afterEach, expect, vi } from 'vitest'
import type { Component } from 'vue'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { checkExpectation } from '../../../ui-core/test/parity/expect'
import type { Expectation } from '../../../ui-core/test/parity/cases'

// Paritätsdateien rendern Vue und React nacheinander, die Interaktionsabläufe mit
// vielen Schritten; in der CI dauern sie bis etwa 1,5 s. 10 s gelten nur für die
// Dateien, die diese Hilfe laden (vi.setConfig wirkt je Datei).
vi.setConfig({ testTimeout: 10_000 })

afterEach(() => {
  cleanup()
  document.body.innerHTML = ''
})

export const tick = () => act(() => new Promise<void>((resolve) => setTimeout(resolve, 0)))

export interface Rendered {
  vue: HTMLElement
  react: HTMLElement
}

/** Vue- und React-Fassung mit denselben Eingaben rendern und die Wurzelelemente liefern. */
export async function renderBoth(vueComponent: Component, props: Record<string, unknown>, react: ReactElement): Promise<Rendered> {
  const host = document.createElement('div')
  document.body.append(host)
  const wrapper = mount(vueComponent, { props, attachTo: host })
  await flushPromises()
  const { container } = render(react)
  await tick()
  await flushPromises()
  await tick()
  return { vue: wrapper.element as HTMLElement, react: container.firstElementChild as HTMLElement }
}

/** Gleiche Erwartungen für beide, dann DOM und Formularzustand gleich. */
export function expectParity(rendered: Rendered, expectation: Expectation): void {
  checkExpectation(rendered.vue, expectation)
  checkExpectation(rendered.react, expectation)
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}
