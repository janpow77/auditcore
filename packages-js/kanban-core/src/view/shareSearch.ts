/** Personensuche des Teilen-Dialogs: späte Antworten verwerfen, bereits Freigegebene ausblenden. */
import type { Share } from '../model'
import type { UserRef } from '../port'
import { createKanbanStore, type KanbanStore } from './store'

export interface ShareSearchState {
  results: UserRef[]
  /** Namen aus bisherigen Suchen (Anzeige der Freigaben). */
  known: ReadonlyMap<string, UserRef>
}

export interface ShareSearch {
  store: KanbanStore<ShareSearchState>
  /** Neue Suche; ohne Text oder Suchfunktion leert sie die Treffer. */
  query: (text: string, search: ((query: string) => Promise<UserRef[]>) | null | undefined, shares: readonly Share[]) => Promise<void>
  clear: () => void
}

export const SHARE_RESULT_LIMIT = 8

/** Anzeigename einer freigegebenen Person: Suchtreffer, sonst bekannte Nutzer, sonst Kennung. */
export function shareName(userId: string, known: ReadonlyMap<string, UserRef>, users: readonly UserRef[]): string {
  return known.get(userId)?.name ?? users.find((user) => user.id === userId)?.name ?? userId
}

export function createShareSearch(): ShareSearch {
  const store = createKanbanStore<ShareSearchState>({ results: [], known: new Map() })
  let request = 0

  async function query(text: string, search: ((query: string) => Promise<UserRef[]>) | null | undefined, shares: readonly Share[]): Promise<void> {
    const ticket = ++request
    if (!text.trim() || !search) {
      store.set({ results: [] })
      return
    }
    const found = await search(text)
    if (ticket !== request) return
    const known = new Map(store.get().known)
    for (const user of found) known.set(user.id, user)
    const shared = new Set(shares.map((share) => share.user_id))
    store.set({ known, results: found.filter((user) => !shared.has(user.id)).slice(0, SHARE_RESULT_LIMIT) })
  }

  return { store, query, clear: () => { request += 1; store.set({ results: [] }) } }
}
