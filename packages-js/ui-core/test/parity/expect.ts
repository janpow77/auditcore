/** Erwartungen eines Paritätsfalls prüfen – für Vue und React identisch (DOM Testing Library). */
import { within } from '@testing-library/dom'
import { expect } from 'vitest'
import type { Expectation } from './cases'

/** Treffer im Teilbaum einschließlich der Wurzel selbst. */
function count(root: HTMLElement, selector: string): number {
  return root.querySelectorAll(selector).length + (root.matches(selector) ? 1 : 0)
}

export function checkExpectation(root: HTMLElement, expectation: Expectation): void {
  const text = (root.textContent ?? '').replace(/\s+/g, ' ')
  // Rollen auch an der Wurzel finden (z. B. eine Schaltfläche als Wurzelelement): Suche ab dem
  // Elternelement, das in beiden Test-Umgebungen nur diese Komponente enthält.
  const scope = root.parentElement ?? root
  for (const expected of expectation.texts ?? []) expect(text).toContain(expected)
  for (const [role, name] of expectation.roles ?? []) expect(within(scope).getAllByRole(role, { name }).length).toBeGreaterThan(0)
  for (const [selector, amount] of Object.entries(expectation.counts ?? {})) expect(count(root, selector), selector).toBe(amount)
}
