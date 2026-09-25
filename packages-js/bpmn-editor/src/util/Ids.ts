/**
 * Vergabe eindeutiger Kennungen je Diagramm.
 *
 * Beim Import werden alle vorhandenen IDs „beansprucht“; neue IDs bestehen
 * aus einem lesbaren Präfix und einer zufälligen Base36-Folge.
 */

export default class Ids {
  private readonly claimed = new Map<string, unknown>()

  claim(id: string, element: unknown = true): void {
    this.claimed.set(id, element)
  }

  unclaim(id: string): void {
    this.claimed.delete(id)
  }

  assigned(id: string): unknown {
    return this.claimed.get(id)
  }

  clear(): void {
    this.claimed.clear()
  }

  next(): string {
    let id: string
    do {
      id = Math.random().toString(36).slice(2, 9).padEnd(7, '0')
    } while (this.claimed.has(id) || !/^[a-z]/.test(id))
    return id
  }

  nextPrefixed(prefix: string, element: unknown = true): string {
    let id: string
    do {
      id = `${prefix}${this.next()}`
    } while (this.claimed.has(id))
    this.claim(id, element)
    return id
  }
}

const REGISTRY = new WeakMap<object, Ids>()

/** Liefert (und legt bei Bedarf an) die Kennungsverwaltung einer moddle-Instanz. */
export function getIds(moddle: object): Ids {
  let ids = REGISTRY.get(moddle)
  if (!ids) {
    ids = new Ids()
    REGISTRY.set(moddle, ids)
  }
  return ids
}
