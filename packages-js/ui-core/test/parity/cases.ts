/**
 * Gemeinsame Paritätsfälle: Vue-Fassung (`@flowaudit/ui`) und React-Fassung
 * (`@flowaudit/ui-react`) werden mit denselben Eingaben gerendert und gegen
 * dieselben Erwartungen (Texte, Rollen, Namen) sowie gegeneinander (DOM)
 * geprüft. Daten: Fixtures der echten Python-Backends, keine Personendaten.
 */

export interface Expectation {
  /** Texte, die im gerenderten Teilbaum vorkommen müssen. */
  texts?: readonly string[]
  /** Zugängliche Rollen mit Namen (`getByRole(role, { name })`). */
  roles?: ReadonlyArray<readonly [string, string | RegExp]>
  /** Anzahl Treffer je CSS-Selektor. */
  counts?: Readonly<Record<string, number>>
}

export interface ParityCase<P> {
  name: string
  props: () => P
  expect: Expectation
}
