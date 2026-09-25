import type { Component } from 'vue'

/** Eine Demo-Seite je Komponente; neue Komponenten tragen sich hier ein. */
export interface DemoPage {
  id: string
  title: string
  group: 'Grundlagen' | 'Komponenten'
  load: () => Promise<{ default: Component }>
}

export const DEMO_PAGES: readonly DemoPage[] = [
  { id: 'basis', title: 'Basiskomponenten', group: 'Grundlagen', load: () => import('./pages/base/BasePage.vue') },
  { id: 'tabelle', title: 'Tabelle', group: 'Grundlagen', load: () => import('./pages/base/TablePage.vue') },
  { id: 'web-components', title: 'Web Components', group: 'Grundlagen', load: () => import('./pages/base/ElementsPage.vue') },
  { id: 'kanban', title: 'Kanban', group: 'Komponenten', load: () => import('./pages/kanban/KanbanPage.vue') },
  { id: 'synopse', title: 'Synopse / Versionsvergleich', group: 'Komponenten', load: () => import('./pages/synopsis/SynopsisPage.vue') },
]

export function findPage(id: string): DemoPage {
  return DEMO_PAGES.find((page) => page.id === id) ?? (DEMO_PAGES[0] as DemoPage)
}
