import './theme/tokens.css'
import './kanban/kanban.css'
/**
 * Einstieg für Web Components: `import { defineFlowauditElements } from '@flowaudit/ui/elements'`
 * und zusätzlich `@flowaudit/ui/style.css` laden.
 */
import { defineElements, type ElementDefinition, type ElementTag } from './elements/define'
import { isLocale, setDefaultLocale, type Locale } from './i18n'
import { ELEMENTS } from './registry'

export { defineElement, defineElements, type ElementDefinition, type ElementTag } from './elements/define'
export { ELEMENTS } from './registry'

export interface DefineOptions {
  /** Nur diese Elemente registrieren; Standard: alle. */
  only?: readonly ElementTag[]
  /** Sprache aller Elemente ohne eigenes `locale`-Attribut. */
  locale?: Locale
}

export function defineFlowauditElements(options: DefineOptions = {}): readonly ElementDefinition[] {
  if (options.locale && isLocale(options.locale)) setDefaultLocale(options.locale)
  const selected = options.only ? ELEMENTS.filter((entry) => options.only?.includes(entry.tag)) : ELEMENTS
  defineElements(selected)
  return selected
}
