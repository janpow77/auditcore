import type { AccountDocument, AccountItem, AccountPort } from './types'

/** Nur synthetische Demo/Testdaten; keine Autorisierungs- oder Persistenzschicht. */
export function createAccountMemoryPort(items: readonly AccountItem[], documents: readonly AccountDocument[] = []): AccountPort {
  const records = new Map(documents.map((document) => [document.id, structuredClone(document)]))
  const read = async (id: string): Promise<AccountDocument> => {
    const record = records.get(id)
    if (record) return structuredClone(record)
    const item = items.find((entry) => entry.id === id)
    if (!item) throw new Error('Eintrag nicht verfügbar.')
    return { id, title: item.label, description: '', kind: 'profile', revision: 0, fields: [], values: {}, editable: false }
  }
  return { list: async () => items, read,
    async save(id, revision, values) {
      const record = await read(id)
      if (!record.editable) throw new Error('Keine Schreibberechtigung.')
      if (record.revision !== revision) throw new Error('Die Daten wurden inzwischen geändert.')
      const allowed = record.fields.filter((f) => !f.readonly).map((f) => f.id)
      if (Object.keys(values).some((key) => !allowed.includes(key))) throw new Error('Feld nicht bearbeitbar.')
      const saved = { ...record, revision: revision + 1, values: { ...record.values, ...values } }
      records.set(id, saved)
      return structuredClone(saved)
    },
  }
}

/** Der injizierte Transport ergänzt Session, CSRF und Fehlerabbildung der Anwendung. */
export interface AccountTransport {
  request: <T>(method: 'GET' | 'POST', path: string, body?: unknown) => Promise<T>
  upload?: AccountPort['upload']
  imageUrl?: AccountPort['imageUrl']
}
export function createAccountRestPort(transport: AccountTransport, base = '/api/account'): AccountPort {
  const path = (id: string) => `${base}/documents/${encodeURIComponent(id)}`
  return {
    list: () => transport.request('GET', `${base}/documents`),
    read: (id) => transport.request('GET', path(id)),
    save: (id, revision, values) => transport.request('POST', path(id), { revision, values }),
    upload: transport.upload, imageUrl: transport.imageUrl,
  }
}
