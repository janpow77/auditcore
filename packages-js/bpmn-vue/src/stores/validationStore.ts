/**
 * Validation store: runs the rules in the browser after changes (debounced)
 * and optionally a server validation through the `ValidationPort`.
 */

import { computed, ref, shallowRef } from 'vue'
import {
  countIssues,
  sortIssues,
  validateModel,
  type ProfileData,
  type ValidationIssue,
  type ValidationPort,
} from '@flowaudit/bpmn-flowaudit'
import type { EditorStore } from './editorStore'

export interface ValidationStoreOptions {
  profile: () => ProfileData | null
  port?: ValidationPort
  delay?: number
}

export type ValidationStore = ReturnType<typeof createValidationStore>

export function createValidationStore(editorStore: EditorStore, options: ValidationStoreOptions) {
  const issues = shallowRef<ValidationIssue[]>([])
  const serverIssues = shallowRef<ValidationIssue[]>([])
  const running = ref(false)
  const error = ref<string | null>(null)
  let timer: ReturnType<typeof setTimeout> | undefined

  function runLocal(): void {
    if (!editorStore.state.ready) return
    try {
      issues.value = sortIssues(validateModel(editorStore.model(), { profile: options.profile() }).issues)
    } catch (caught) {
      error.value = (caught as Error).message
    }
  }

  async function runServer(): Promise<void> {
    if (!options.port) return
    running.value = true
    error.value = null
    try {
      serverIssues.value = sortIssues(await options.port.validate(await editorStore.exportXml(), { profile: options.profile()?.id }))
    } catch (caught) {
      error.value = (caught as Error).message
    } finally {
      running.value = false
    }
  }

  function schedule(): void {
    clearTimeout(timer)
    timer = setTimeout(runLocal, options.delay ?? 400)
  }

  editorStore.onChange(schedule)

  const all = computed(() => (serverIssues.value.length ? serverIssues.value : issues.value))
  const count = computed(() => countIssues(all.value))
  const byElement = computed(() => {
    const map = new Map<string, ValidationIssue[]>()
    for (const item of all.value) if (item.elementId) map.set(item.elementId, [...(map.get(item.elementId) ?? []), item])
    return map
  })

  return { issues: all, count, byElement, running, error, runLocal, runServer, schedule, hasServer: Boolean(options.port) }
}
