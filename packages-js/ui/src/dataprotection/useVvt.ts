// Zustand und Aktionen von <flowaudit-vvt> über einen DataProtectionPort.

import { computed, ref, shallowRef, type ComputedRef, type Ref, type ShallowRef } from 'vue'
import { registerCsv, registerFilename, registerHtml, registerMarkdown, type ExportTexts } from './exporters'
import { cloneContent, currentVersion, emptyContent } from './registerView'
import { createRequests, type DataProtectionError, type RequestHooks, type Requests } from './requests'
import type { DataProtectionPort, Issue, DataProtectionProfile, RegisterContent, RegisterState, VersionView } from './types'

export type VvtExportFormat = 'print' | 'markdown' | 'csv'

export interface VvtExport {
  format: VvtExportFormat
  filename: string
  mimeType: string
  content: string
}

export interface VvtHooks extends RequestHooks {
  onSaved?: (version: VersionView) => void
  onReleased?: (version: VersionView) => void
  /** Wartezeit der Vollständigkeitsprüfung nach einer Eingabe (ms). */
  checkDelay?: number
}

export interface VvtState extends Requests<DataProtectionPort> {
  profile: ShallowRef<DataProtectionProfile | null>
  register: ShallowRef<RegisterState | null>
  showing: Ref<'draft' | 'released'>
  working: ShallowRef<RegisterContent | null>
  version: ComputedRef<VersionView | null>
  content: ComputedRef<RegisterContent>
  issues: ComputedRef<Issue[]>
  editing: ComputedRef<boolean>
  dirty: ComputedRef<boolean>
  load: (editable: boolean) => Promise<void>
  update: (content: RegisterContent) => void
  check: () => Promise<void>
  startDraft: () => void
  discard: () => void
  save: () => Promise<VersionView | null>
  release: () => Promise<VersionView | null>
  show: (which: 'draft' | 'released') => void
  build: (format: VvtExportFormat, texts: ExportTexts, versionLabel: string, lang: string) => VvtExport
}

export type { DataProtectionError }

const MIME: Readonly<Record<VvtExportFormat, [string, string]>> = {
  print: ['text/html;charset=utf-8', 'html'],
  markdown: ['text/markdown;charset=utf-8', 'md'],
  csv: ['text/csv;charset=utf-8', 'csv'],
}

interface Core {
  requests: Requests<DataProtectionPort>
  hooks: VvtHooks
  profile: ShallowRef<DataProtectionProfile | null>
  register: ShallowRef<RegisterState | null>
  showing: Ref<'draft' | 'released'>
  working: ShallowRef<RegisterContent | null>
  checked: ShallowRef<Issue[] | null>
}

function reset(core: Core, state: RegisterState, editable: boolean): void {
  core.register.value = state
  core.checked.value = null
  core.showing.value = state.draft ? 'draft' : 'released'
  core.working.value = editable && state.draft ? cloneContent(state.draft.content) : null
}

/** Eingaben im Entwurf: Inhalt ändern, Prüfung der Bibliothek anstoßen, Ansicht wechseln. */
function editActions(core: Core) {
  const { requests, register, showing, working, checked, hooks } = core
  let timer: ReturnType<typeof setTimeout> | undefined

  async function check(): Promise<void> {
    const current = working.value
    if (!current) return
    const result = await requests.run('check', (active) => active.checkRegister(current))
    if (result && working.value === current) checked.value = result.issues
  }

  function update(next: RegisterContent): void {
    working.value = next
    clearTimeout(timer)
    timer = setTimeout(() => void check(), hooks.checkDelay ?? 400)
  }

  function show(which: 'draft' | 'released'): void {
    showing.value = which
    const draft = register.value?.draft
    if (which === 'draft' && draft && !working.value) working.value = cloneContent(draft.content)
  }

  function startDraft(): void {
    if (register.value?.draft) return show('draft')
    working.value = cloneContent(register.value?.released?.content ?? emptyContent())
    showing.value = 'draft'
    checked.value = null
  }

  function discard(): void {
    const draft = register.value?.draft
    working.value = draft ? cloneContent(draft.content) : null
    checked.value = null
  }

  return { check, update, show, startDraft, discard }
}

/** Speichern und Freigeben über den Port; danach wird der Stand neu gelesen. */
function writeActions(core: Core) {
  const { requests, register, working, hooks } = core

  async function reload(): Promise<void> {
    const state = await requests.run('load', (active) => active.register())
    if (state) reset(core, state, true)
  }

  async function save(): Promise<VersionView | null> {
    const current = working.value
    if (!current) return null
    const expected = register.value?.draft?.revision ?? null
    const saved = await requests.run('save', (active) => active.saveDraft(current, expected))
    if (!saved) return null
    await reload()
    hooks.onSaved?.(saved)
    return saved
  }

  async function release(): Promise<VersionView | null> {
    const draft = register.value?.draft
    if (!draft) return null
    const released = await requests.run('release', (active) => active.releaseRegister(draft.revision))
    if (!released) return null
    await reload()
    hooks.onReleased?.(released)
    return released
  }

  return { save, release }
}

export function useVvt(port: () => DataProtectionPort | null, hooks: VvtHooks = {}): VvtState {
  const core: Core = {
    requests: createRequests(port, hooks),
    hooks,
    profile: shallowRef<DataProtectionProfile | null>(null),
    register: shallowRef<RegisterState | null>(null),
    showing: ref<'draft' | 'released'>('draft'),
    working: shallowRef<RegisterContent | null>(null),
    checked: shallowRef<Issue[] | null>(null),
  }
  const { requests, profile, register, showing, working, checked } = core
  const version = computed(() => currentVersion(register.value, showing.value))
  const editing = computed(() => working.value !== null && showing.value === 'draft')
  const content = computed(() => (editing.value ? working.value : null) ?? version.value?.content ?? emptyContent())
  const editBase = computed(() => register.value?.draft?.content ?? register.value?.released?.content ?? emptyContent())
  const dirty = computed(() => working.value !== null && JSON.stringify(working.value) !== JSON.stringify(editBase.value))
  const issues = computed(() => (editing.value ? checked.value : null) ?? version.value?.issues ?? [])

  async function load(editable: boolean): Promise<void> {
    const loaded = await requests.run('load', async (active) => Promise.all([active.profile(), active.register()]))
    if (!loaded) return
    profile.value = loaded[0]
    reset(core, loaded[1], editable)
  }

  function build(format: VvtExportFormat, texts: ExportTexts, versionLabel: string, lang: string): VvtExport {
    const input = { content: content.value, columns: profile.value?.register.columns ?? [], issues: issues.value, versionLabel, texts, lang }
    const [mimeType, extension] = MIME[format]
    const render = { csv: registerCsv, markdown: registerMarkdown, print: registerHtml }[format]
    const text = render({ ...input, generatedAt: new Date().toLocaleString(lang) })
    return { format, filename: registerFilename(version.value?.version ?? null, extension), mimeType, content: text }
  }

  return { ...requests, profile, register, showing, working, version, content, issues, editing, dirty, load, build, ...editActions(core), ...writeActions(core) }
}
