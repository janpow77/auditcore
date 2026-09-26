/**
 * Kern aus `@flowaudit/ui-core` unter den bisherigen Namen der Vue-Fassung
 * (Status- und Präfixtexte, Prüfhinweise). Fachlogik liegt nur im Kern.
 */
export * from '@flowaudit/ui-core'
export {
  dataprotectionStatusLabel as statusLabel,
  dataprotectionLabel as prefixedLabel,
  type RegisterIssue as Issue,
} from '@flowaudit/ui-core'
