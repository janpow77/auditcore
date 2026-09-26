/**
 * Validation controller: runs the rules in the browser after changes
 * (debounced) and optionally a server validation through the
 * `ValidationPort`. Derived values (all issues, counts, per element) come
 * from `validationView`.
 */

import { countIssues, sortIssues, validateModel, type ProfileData, type ValidationIssue, type ValidationPort } from '../index'
import type { EditorCore } from './editorCore'
import { createStore } from './store'

export interface ValidationState {
  local: ValidationIssue[]
  server: ValidationIssue[]
  running: boolean
  error: string | null
}

export interface ValidationCoreOptions {
  profile: () => ProfileData | null
  port?: ValidationPort
  delay?: number
}

export interface ValidationView {
  issues: ValidationIssue[]
  count: ReturnType<typeof countIssues>
  byElement: Map<string, ValidationIssue[]>
}

export type ValidationCore = ReturnType<typeof createValidationCore>

/** Server issues win over local ones once the server was asked. */
export function validationView(state: ValidationState): ValidationView {
  const issues = state.server.length ? state.server : state.local
  const byElement = new Map<string, ValidationIssue[]>()
  for (const item of issues) if (item.elementId) byElement.set(item.elementId, [...(byElement.get(item.elementId) ?? []), item])
  return { issues, count: countIssues(issues), byElement }
}

export function createValidationCore(editor: EditorCore, options: ValidationCoreOptions) {
  const store = createStore<ValidationState>({ local: [], server: [], running: false, error: null })
  let timer: ReturnType<typeof setTimeout> | undefined

  function runLocal(): void {
    if (!editor.store.get().ready) return
    try {
      store.set({ local: sortIssues(validateModel(editor.model(), { profile: options.profile() }).issues) })
    } catch (caught) {
      store.set({ error: (caught as Error).message })
    }
  }

  async function runServer(): Promise<void> {
    if (!options.port) return
    store.set({ running: true, error: null })
    try {
      store.set({ server: sortIssues(await options.port.validate(await editor.exportXml(), { profile: options.profile()?.id })) })
    } catch (caught) {
      store.set({ error: (caught as Error).message })
    } finally {
      store.set({ running: false })
    }
  }

  function schedule(): void {
    clearTimeout(timer)
    timer = setTimeout(runLocal, options.delay ?? 400)
  }

  const stop = editor.onChange(schedule)

  return {
    store,
    runLocal,
    runServer,
    schedule,
    hasServer: Boolean(options.port),
    dispose: () => (clearTimeout(timer), stop()),
  }
}
