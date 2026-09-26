import { defineCustomElement, type Component, type DefineComponent } from 'vue'

export type ElementTag = `flowaudit-${string}`

/** Eine Komponente, die als Web Component `flowaudit-<name>` bereitgestellt wird. */
export interface ElementDefinition {
  tag: ElementTag
  component: Component
}

/**
 * Registriert eine Komponente als Custom Element im Light DOM (kein Shadow
 * DOM): Designtoken und `@auditcore/ui/style.css` der Seite gelten direkt.
 * Bereits registrierte Namen werden nicht erneut definiert.
 */
export function defineElement(definition: ElementDefinition): CustomElementConstructor {
  const existing = customElements.get(definition.tag)
  if (existing) return existing
  // SFC-Standardexporte sind DefineComponent; der allgemeine Typ Component passt auf keine Überladung.
  const component = definition.component as unknown as DefineComponent
  const element = defineCustomElement(component, { shadowRoot: false })
  customElements.define(definition.tag, element)
  return element
}

export function defineElements(definitions: readonly ElementDefinition[]): void {
  for (const definition of definitions) defineElement(definition)
}
