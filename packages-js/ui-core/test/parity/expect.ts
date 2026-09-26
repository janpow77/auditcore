/** Erwartungen eines Paritätsfalls prüfen – für Vue und React identisch (DOM Testing Library). */
import { within } from '@testing-library/dom'
import { expect } from 'vitest'
import type { Expectation } from './cases'

export function checkExpectation(root: HTMLElement, expectation: Expectation): void {
  const text = (root.textContent ?? '').replace(/\s+/g, ' ')
  for (const expected of expectation.texts ?? []) expect(text).toContain(expected)
  for (const [role, name] of expectation.roles ?? []) expect(within(root).getAllByRole(role, { name }).length).toBeGreaterThan(0)
  for (const [selector, count] of Object.entries(expectation.counts ?? {})) expect(root.querySelectorAll(selector)).toHaveLength(count)
}
