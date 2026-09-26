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
  { id: 'risiko-merkmale', title: 'Risiko-Merkmale', group: 'Komponenten', load: () => import('./pages/risk/RiskFlagsPage.vue') },
  { id: 'web-components', title: 'Web Components', group: 'Grundlagen', load: () => import('./pages/base/ElementsPage.vue') },
  { id: 'stichprobe', title: 'Stichprobe', group: 'Komponenten', load: () => import('./pages/sampling/SamplingPage.vue') },
  { id: 'benford', title: 'Benford-Analyse', group: 'Komponenten', load: () => import('./pages/benford/BenfordPage.vue') },
  { id: 'kennung', title: 'Kennung prüfen', group: 'Komponenten', load: () => import('./pages/identifiers/IdentifierPage.vue') },
  { id: 'screening', title: 'Screening-Trefferprüfung', group: 'Komponenten', load: () => import('./pages/screening/ScreeningPage.vue') },
  { id: 'kanban', title: 'Kanban', group: 'Komponenten', load: () => import('./pages/kanban/KanbanPage.vue') },
  { id: 'datenbank-kanban', title: 'Datenbankansicht (Kanban)', group: 'Komponenten', load: () => import('./pages/dbkanban/DbKanbanPage.vue') },
  { id: 'datenschutz', title: 'Datenschutz: VVT und DSFA', group: 'Komponenten', load: () => import('./pages/dataprotection/DataProtectionPage.vue') },
  { id: 'geo-karte', title: 'Geo-Karte', group: 'Komponenten', load: () => import('./pages/geo/GeoPage.vue') },
  { id: 'dokumentvergleiche', title: 'Dokumentvergleiche', group: 'Komponenten', load: () => import('./pages/documents/ComparisonsPage.vue') },
  { id: 'synopse', title: 'Synopse / Versionsvergleich', group: 'Komponenten', load: () => import('./pages/synopsis/SynopsisPage.vue') },
]

export function findPage(id: string): DemoPage {
  return DEMO_PAGES.find((page) => page.id === id) ?? (DEMO_PAGES[0] as DemoPage)
}
