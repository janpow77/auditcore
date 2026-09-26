/**
 * Vorlagen des Kerns (packages-js/ui-core) für `npm run ui:neu`: Texte,
 * Datentypen, Port, Anzeige, Controller, Stil, Kerntest und Paritätsfälle.
 * Jede Funktion erhält die abgeleiteten Namen (`namesFor` in ui-new.mjs).
 */

export const coreMessages = (n) => `import { defineMessages } from '../i18n'

/** Texte von ${n.vue} (Vue) und ${n.react} (React); sichtbare Texte nur hier. */
export const ${n.messages} = defineMessages({
  de: {
    title: '${n.component}',
    loading: 'Einträge werden geladen …',
    empty: 'Keine Einträge vorhanden.',
    failed: 'Anfrage abgelehnt: {message}',
  },
  en: {
    title: '${n.component}',
    loading: 'Loading entries …',
    empty: 'No entries.',
    failed: 'Request rejected: {message}',
  },
})

export type ${n.Group}MessageKey = keyof typeof ${n.messages}.de
`

export const coreTypes = (n) => `/** Eintrag der Liste (Vertrag des Ports; an den REST-Vertrag des Backends anpassen). */
export interface ${n.Group}Item {
  id: string
  label: string
}

/** Fachlogik hinter der Oberfläche; Vue und React rufen nur diesen Port auf. */
export interface ${n.Group}Port {
  list: () => Promise<readonly ${n.Group}Item[]>
}
`

export const corePort = (n) => `import type { ${n.Group}Item, ${n.Group}Port } from './types'

/**
 * Port im Arbeitsspeicher (Demo, Tests). Eine REST-Umsetzung baut auf
 * \`requestJson\` aus \`${n.commonPackage}\` auf (Vorbild: \`extrapolation/rest-port.ts\`).
 */
export function create${n.Group}MemoryPort(items: readonly ${n.Group}Item[]): ${n.Group}Port {
  return { list: async () => items }
}
`

export const coreView = (n) => `import type { ${n.Group}Data } from './controller'
import type { ${n.Group}Item } from './types'

/** Zeile der Liste, wie Vue und React sie darstellen. */
export interface ${n.Group}Row {
  id: string
  label: string
  selected: boolean
}

export function ${n.group}Rows(state: ${n.Group}Data): ${n.Group}Row[] {
  return state.items.map((item) => ({ id: item.id, label: item.label, selected: item.id === state.selectedId }))
}

export function ${n.group}Selection(state: ${n.Group}Data): ${n.Group}Item | null {
  return state.items.find((item) => item.id === state.selectedId) ?? null
}

/** Hinweis „keine Einträge“ nur nach abgeschlossener, fehlerfreier Anfrage. */
export function ${n.group}IsEmpty(state: ${n.Group}Data): boolean {
  return state.busy === null && state.error === null && state.items.length === 0
}
`

export const coreController = (n) => `// Zustandsautomat von <${n.tag}> (Vue und React): lädt die Einträge über
// den Port und verwaltet die Auswahl. Vue bindet ihn mit useStore, React mit
// useStoreState.

import { createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import type { ${n.Group}Item, ${n.Group}Port } from './types'

export interface ${n.Group}Callbacks {
  selected?: (item: ${n.Group}Item) => void
  failed?: (message: string) => void
}

/** Stand; \`error\` ist die Meldung der letzten abgelehnten Anfrage. */
export interface ${n.Group}Data extends RequestState<string> {
  items: readonly ${n.Group}Item[]
  selectedId: string | null
}

export interface ${n.Group}Source {
  port: () => ${n.Group}Port | null | undefined
  callbacks?: () => ${n.Group}Callbacks
}

export interface ${n.Group}Controller {
  store: Store<${n.Group}Data>
  load: () => Promise<void>
  select: (id: string) => void
}

export const ${n.initial}: ${n.Group}Data = { ...IDLE, items: [], selectedId: null }

const errorText = (error: unknown): string => (error instanceof Error ? error.message : String(error))

export function ${n.createController}(source: ${n.Group}Source): ${n.Group}Controller {
  const store = createStore<${n.Group}Data>({ ...${n.initial} })
  const run = createRunner(store, () => source.port() ?? null, errorText, (message) => source.callbacks?.().failed?.(message))
  return {
    store,
    async load() {
      const items = await run('load', (port) => port.list())
      if (items) store.set({ items, selectedId: null })
    },
    select(id) {
      const item = store.get().items.find((entry) => entry.id === id)
      if (!item) return
      store.set({ selectedId: id })
      source.callbacks?.().selected?.(item)
    },
  }
}
`

export const coreIndex = (n) => `export { ${n.messages}, type ${n.Group}MessageKey } from './messages'
export type * from './types'
export { create${n.Group}MemoryPort } from './port'
export * from './controller'
export * from './view'
`

export const coreTest = (n) => `import { describe, expect, it } from 'vitest'
import { ${n.createController}, create${n.Group}MemoryPort, ${n.group}IsEmpty, ${n.group}Rows, ${n.group}Selection, type ${n.Group}Port } from '../../src'

const items = [{ id: 'a', label: 'Eintrag A' }, { id: 'b', label: 'Eintrag B' }]

function controller(port: ${n.Group}Port | null = create${n.Group}MemoryPort(items)) {
  const events: string[] = []
  const created = ${n.createController}({ port: () => port, callbacks: () => ({ selected: (item) => events.push(item.id), failed: (message) => events.push(message) }) })
  return { created, events }
}

describe('${n.createController}', () => {
  it('lädt die Einträge und wählt aus', async () => {
    const { created, events } = controller()
    await created.load()
    created.select('b')
    const state = created.store.get()
    expect(${n.group}Rows(state).map((row) => row.selected)).toEqual([false, true])
    expect(${n.group}Selection(state)?.label).toBe('Eintrag B')
    expect(events).toEqual(['b'])
  })

  it('meldet Fehler des Ports', async () => {
    const { created, events } = controller({ list: async () => { throw new Error('Dienst nicht erreichbar') } })
    await created.load()
    expect(created.store.get().error).toBe('Dienst nicht erreichbar')
    expect(events).toEqual(['Dienst nicht erreichbar'])
  })

  it('ohne Port: leer, keine Auswahl unbekannter Einträge', async () => {
    const { created, events } = controller(null)
    await created.load()
    created.select('x')
    expect(${n.group}IsEmpty(created.store.get())).toBe(true)
    expect(events).toEqual([])
  })
})
`

export const coreStyle = (n) => `/* ${n.component} – ${n.vue} (Vue) und ${n.react} (React). Farben nur aus --fa-*-Variablen. */
.${n.css} { display: flex; flex-direction: column; gap: var(--fa-space-3); font: var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans); color: var(--fa-color-text); }
.${n.css}__list { display: flex; flex-direction: column; gap: var(--fa-space-1); margin: 0; padding: 0; list-style: none; }
.${n.css}__item { width: 100%; padding: var(--fa-space-2) var(--fa-space-3); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); background: var(--fa-color-surface); color: inherit; font: inherit; text-align: start; cursor: pointer; }
.${n.css}__item:focus-visible { outline: none; border-color: var(--fa-color-accent); box-shadow: var(--fa-focus-ring); }
.${n.css}__item--selected { border-color: var(--fa-color-accent); }
.${n.css}__muted { margin: 0; color: var(--fa-color-text-muted); }
.${n.css}__failure { margin: 0; padding: var(--fa-space-2) var(--fa-space-3); border-radius: var(--fa-radius); background: var(--fa-color-danger-soft); color: var(--fa-color-danger); }
`

export const parityCases = (n) => `/**
 * Paritätsfälle von ${n.component} (Vue \`${n.vue}\` ↔ React \`${n.react}\`).
 * Synthetische Daten, keine Personendaten.
 */
import { create${n.Group}MemoryPort, type ${n.Group}Port } from '../../src'
import type { ParityCase } from './cases'

export interface ${n.Group}CaseProps {
  port?: ${n.Group}Port | null
  locale?: 'de' | 'en'
}

export const ${n.group}Items = [{ id: 'a', label: 'Eintrag A' }, { id: 'b', label: 'Eintrag B' }]

export const ${n.cases}: ReadonlyArray<ParityCase<${n.Group}CaseProps>> = [
  {
    name: 'Einträge aus dem Port',
    props: () => ({ port: create${n.Group}MemoryPort(${n.group}Items) }),
    expect: { texts: ['Eintrag A'], roles: [['button', 'Eintrag B']], counts: { li: 2, '[aria-pressed="true"]': 0 } },
  },
  {
    name: 'leer',
    props: () => ({ port: create${n.Group}MemoryPort([]) }),
    expect: { texts: ['Keine Einträge vorhanden.'], counts: { li: 0 } },
  },
  {
    name: 'Fehler des Ports, englisch',
    props: () => ({ port: { list: async () => { throw new Error('offline') } }, locale: 'en' }),
    expect: { texts: ['Request rejected: offline'], counts: { '[role="alert"]': 1 } },
  },
]
`
