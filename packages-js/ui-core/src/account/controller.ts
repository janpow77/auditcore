import { createStore, IDLE, type RequestState } from '../store'
import type { AccountDocument, AccountItem, AccountPort } from './types'

export interface AccountCallbacks {
  selected?: (item: AccountItem) => void
  failed?: (message: string) => void
}
export interface AccountData extends RequestState<string> {
  items: readonly AccountItem[]
  selectedId: string | null
  document: AccountDocument | null
  draft: Readonly<Record<string, string>>
  dirty: boolean
  images: Readonly<Record<string, string>>
}
export interface AccountSource {
  port: () => AccountPort | null | undefined
  callbacks?: () => AccountCallbacks
}
export const INITIAL_ACCOUNT: AccountData = {
  ...IDLE, items: [], selectedId: null, document: null, draft: {}, dirty: false, images: {},
}
const errorText = (error: unknown) => error instanceof Error ? error.message : String(error)

function requests(source: AccountSource, store: ReturnType<typeof createStore<AccountData>>) {
  let epoch = 0
  async function run(kind: string, task: (port: AccountPort, current: () => boolean) => Promise<void>) {
    const port = source.port()
    if (!port) return
    const ticket = ++epoch
    const current = () => ticket === epoch && source.port() === port
    store.set({ busy: kind, error: null, notice: '' })
    try { await task(port, current) }
    catch (error) {
      if (current()) {
        store.set({ error: errorText(error) })
        source.callbacks?.().failed?.(errorText(error))
      }
    } finally { if (current()) store.set({ busy: null }) }
  }
  return { run, invalidate: () => { epoch++ } }
}

export function createAccountController(source: AccountSource) {
  const store = createStore<AccountData>({ ...INITIAL_ACCOUNT })
  const accept = (document: AccountDocument) => store.set({
    document, draft: { ...document.values }, selectedId: document.id, dirty: false, images: {},
  })
  const { run, invalidate } = requests(source, store)
  return {
    store,
    dispose() { invalidate(); store.set({ ...INITIAL_ACCOUNT }) },
    async load() {
      invalidate()
      store.set({ ...INITIAL_ACCOUNT })
      await run('load', async (port, current) => {
        const items = await port.list()
        if (current()) store.set({ items })
      })
    },
    async select(id: string) {
      const state = store.get()
      const item = state.items.find((entry) => entry.id === id)
      if (!item || state.dirty || state.busy) return
      await run('read', async (port, current) => {
        const document = await port.read(id)
        if (current()) { accept(document); source.callbacks?.().selected?.(item) }
      })
    },
    edit(id: string, value: string) {
      const state = store.get()
      const field = state.document?.fields.find((entry) => entry.id === id)
      if (!state.document?.editable || !field || field.readonly || state.busy) return
      store.set({ draft: { ...state.draft, [id]: value }, dirty: true, notice: '', images: { ...state.images, [id]: '' } })
    },
    discard() {
      const document = store.get().document
      if (document && !store.get().busy) accept(document)
    },
    async save() {
      const state = store.get()
      if (!state.document?.editable || state.busy || !state.dirty) return
      const document = state.document
      const values = Object.fromEntries(document.fields.filter((f) => !f.readonly).map((f) => [f.id, state.draft[f.id] ?? '']))
      await run('save', async (port, current) => {
        const saved = await port.save(document.id, document.revision, values)
        if (current()) { accept(saved); store.set({ notice: 'saved' }) }
      })
    },
    async upload(fieldId: string, file: Blob) {
      const state = store.get()
      const document = state.document
      const field = document?.fields.find((f) => f.id === fieldId)
      if (!document?.editable || field?.type !== 'image' || field.readonly || state.busy) return
      await run('upload', async (port, current) => {
        if (!port.upload) throw new Error('Bilder werden von diesem Anschluss nicht unterstützt.')
        const image = await port.upload(document.id, fieldId, file)
        if (current()) store.set({ draft: { ...store.get().draft, [fieldId]: image.id },
          images: { ...store.get().images, [fieldId]: image.url }, dirty: true })
      })
    },
  }
}
export type AccountController = ReturnType<typeof createAccountController>
