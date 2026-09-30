import { defineElement, type ElementDefinition } from '@auditcore/ui/elements'
import FaAppLayout from './FaAppLayout.vue'
import FaLoginLayout from './FaLoginLayout.vue'
import FaPageTransition from './FaPageTransition.vue'
import FaThemeSwitch from './FaThemeSwitch.vue'
import FaExportActions from './FaExportActions.vue'

export const LAYOUT_ELEMENTS: readonly ElementDefinition[] = [
  { tag: 'flowaudit-app-layout', component: FaAppLayout },
  { tag: 'flowaudit-login-layout', component: FaLoginLayout },
  { tag: 'flowaudit-page-transition', component: FaPageTransition },
  { tag: 'flowaudit-theme-switch', component: FaThemeSwitch },
  { tag: 'flowaudit-export-actions', component: FaExportActions },
]

/** Registriert die Layout-Web-Components im Light DOM, ohne vorhandene Tags zu überschreiben. */
export function defineFlowauditLayoutElements(only?: readonly ElementDefinition['tag'][]): readonly ElementDefinition[] {
  const selected = only ? LAYOUT_ELEMENTS.filter((entry) => only.includes(entry.tag)) : LAYOUT_ELEMENTS
  for (const entry of selected) defineElement(entry)
  return selected
}
