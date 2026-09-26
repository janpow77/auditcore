/**
 * Kern aus `@auditcore/ui-core` unter den bisherigen Namen der Vue-Fassung
 * (Status- und Präfixtexte, Prüfhinweise). Fachlogik liegt nur im Kern.
 */
export * from '@auditcore/ui-core'
export {
  dataprotectionStatusLabel as statusLabel,
  dataprotectionLabel as prefixedLabel,
  type RegisterIssue as Issue,
} from '@auditcore/ui-core'
