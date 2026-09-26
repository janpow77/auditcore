import { inject, type InjectionKey } from 'vue'
import type { IdentifierTranslate } from '@flowaudit/ui-core'
import type { UseIdentifierCheck } from './useIdentifierCheck'

/** Gemeinsamer Zustand, Übersetzung und Kennung der Teilkomponenten von „Kennung prüfen“. */
export interface IdentifierContext {
  view: UseIdentifierCheck
  t: IdentifierTranslate
  id: string
}

export const IDENTIFIER_CONTEXT: InjectionKey<IdentifierContext> = Symbol('flowaudit-identifiers')

export function useIdentifierContext(): IdentifierContext {
  const context = inject(IDENTIFIER_CONTEXT, null)
  if (!context) throw new Error('Teilkomponenten nur innerhalb von IdentifierCheck verwenden.')
  return context
}
