/**
 * Expectation of a parity case – same shape as `Expectation`/`ParityCase` of
 * @auditcore/ui-core (test/parity/cases.ts), declared here so the type check
 * of this package does not pull in the sources of ui-core and common.
 */

export interface Expectation {
  /** Texts that must occur in the rendered subtree. */
  texts?: readonly string[]
  /** Accessible roles with names (`getByRole(role, { name })`). */
  roles?: ReadonlyArray<readonly [string, string | RegExp]>
  /** Number of matches per CSS selector. */
  counts?: Readonly<Record<string, number>>
}

export interface ParityCase<P> {
  name: string
  props: () => P
  expect: Expectation
}
