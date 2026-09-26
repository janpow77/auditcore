import { flushPromises, mount } from '@vue/test-utils'
import { cleanup, render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { afterEach, expect } from 'vitest'
import { defineComponent, h, type Component } from 'vue'
import { formState, normalizeDom } from '../../../ui-core/test/parity/dom'
import { checkExpectation } from '../../../ui-core/test/parity/expect'
import type { Expectation } from '../../../ui-core/test/parity/cases'
import { flush } from '../helpers'

afterEach(() => {
  cleanup()
  document.body.innerHTML = ''
})

export interface Rendered {
  vue: HTMLElement
  react: HTMLElement
}

/** Vue and React version with the same inputs; returns both root elements. */
export async function renderBoth(vueComponent: Component, props: object, react: ReactElement): Promise<Rendered> {
  const host = document.createElement('div')
  document.body.append(host)
  const wrapper = mount(defineComponent({ setup: () => () => h(vueComponent, props as Record<string, unknown>) }), { attachTo: host })
  await flushPromises()
  const { container } = render(react)
  await flush()
  await flushPromises()
  return { vue: wrapper.element as HTMLElement, react: container.firstElementChild as HTMLElement }
}

/** Same expectations for both, then the same DOM and form state. */
export function expectParity(rendered: Rendered, expectation: Expectation = {}): void {
  checkExpectation(rendered.vue, expectation)
  checkExpectation(rendered.react, expectation)
  expect(normalizeDom(rendered.react)).toBe(normalizeDom(rendered.vue))
  expect(formState(rendered.react)).toEqual(formState(rendered.vue))
}

/** Same DOM for a part of both trees (selector inside each root). */
export function expectPartParity(rendered: Rendered, selector: string): void {
  const vue = rendered.vue.querySelector(selector)
  const react = rendered.react.querySelector(selector)
  expect(vue, `Vue: ${selector}`).not.toBeNull()
  expect(react, `React: ${selector}`).not.toBeNull()
  expect(normalizeDom(react as Element)).toBe(normalizeDom(vue as Element))
  expect(formState(react as Element)).toEqual(formState(vue as Element))
}
