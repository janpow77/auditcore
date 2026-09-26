// Zustandsautomat von <flowaudit-vvt> (Vue und React): Laden, Bearbeiten,
// Vollständigkeitsprüfung, Speichern, Freigeben, Export.

import { createDelay, createRunner, createStore, IDLE, type RequestState, type Store } from '../store'
import { registerCsv, registerFilename, registerHtml, registerMarkdown, type ExportTexts } from './exporters'
import type { DataProtectionTranslate } from './messages'
import {
  cloneContent,
  currentVersion,
  editedBy,
  emptyActivity,
  emptyContent,
  withActivity,
  withDepartments,
  withField,
  withoutActivity,
  withPerson,
} from './registerView'
import { asError, statusLabel, type DataProtectionError, type RequestHooks } from './requests'
import type { DataProtectionPort, DataProtectionProfile, FieldValue, Issue, Person, RegisterContent, RegisterState, VersionView } from './types'

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

export interface VvtData extends RequestState<DataProtectionError> {
  profile: DataProtectionProfile | null
  register: RegisterState | null
  showing: 'draft' | 'released'
  working: RegisterContent | null
  checked: Issue[] | null
  /** Ausgewählte Tätigkeit (Index in `content.taetigkeiten`). */
  selected: number | null
  history: boolean
}

/** Abgeleitete Werte eines Stands (reine Funktion, von beiden Oberflächen genutzt). */
export interface VvtView {
  version: VersionView | null
  editing: boolean
  content: RegisterContent
  dirty: boolean
  issues: Issue[]
}

function editingOf(state: VvtData): boolean {
  return state.working !== null && state.showing === 'draft'
}

/** Inhalt als Grundlage des Bearbeitens: offener Entwurf, sonst freigegebene Fassung. */
function editBase(register: RegisterState | null): RegisterContent {
  return register?.draft?.content ?? register?.released?.content ?? emptyContent()
}

function shownContent(state: VvtData, version: VersionView | null, editing: boolean): RegisterContent {
  if (editing && state.working) return state.working
  return version?.content ?? emptyContent()
}

function shownIssues(state: VvtData, version: VersionView | null, editing: boolean): Issue[] {
  if (editing && state.checked) return state.checked
  return version?.issues ?? []
}

export function vvtView(state: VvtData): VvtView {
  const version = currentVersion(state.register, state.showing)
  const editing = editingOf(state)
  const dirty = state.working !== null && JSON.stringify(state.working) !== JSON.stringify(editBase(state.register))
  return { version, editing, content: shownContent(state, version, editing), dirty, issues: shownIssues(state, version, editing) }
}

/** Vier-Augen-Hinweis: die angemeldete Person hat den offenen Entwurf bearbeitet. */
export function vvtFourEyes(state: VvtData, actor: string): boolean {
  return editedBy(state.register?.draft ?? null, actor)
}

export function vvtVersionLabel(t: DataProtectionTranslate, version: VersionView | null): string {
  return version ? t('versionLabel', { version: version.version, status: statusLabel(t, version.status) }) : t('noVersion')
}

/** Beschriftungen der Exporte (Druckansicht, Markdown, CSV). */
export function vvtExportTexts(t: DataProtectionTranslate): ExportTexts {
  return {
    yes: t('yes'), no: t('no'), empty: t('empty'), title: t('vvtTitle'), department: t('colDepartment'),
    withoutDepartment: t('withoutDepartment'), controller: t('controller'), dpo: t('dpo'), version: t('colVersion'),
    issues: t('issuesExport'), noIssues: t('noIssues'), required: t('blockingLabel'), hint: t('hintLabel'),
    field: t('field'), content: t('content'), generated: t('generated'),
  }
}

const MIME: Readonly<Record<VvtExportFormat, [string, string]>> = {
  print: ['text/html;charset=utf-8', 'html'],
  markdown: ['text/markdown;charset=utf-8', 'md'],
  csv: ['text/csv;charset=utf-8', 'csv'],
}

export function buildVvtExport(state: VvtData, format: VvtExportFormat, t: DataProtectionTranslate, lang: string): VvtExport {
  const view = vvtView(state)
  const input = {
    content: view.content,
    columns: state.profile?.register.columns ?? [],
    issues: view.issues,
    versionLabel: vvtVersionLabel(t, view.version),
    texts: vvtExportTexts(t),
    lang,
  }
  const [mimeType, extension] = MIME[format]
  const render = { csv: registerCsv, markdown: registerMarkdown, print: registerHtml }[format]
  const text = render({ ...input, generatedAt: new Date().toLocaleString(lang) })
  return { format, filename: registerFilename(view.version?.version ?? null, extension), mimeType, content: text }
}

const INITIAL: VvtData = {
  ...IDLE, profile: null, register: null, showing: 'draft', working: null, checked: null, selected: null, history: false,
}

function reset(store: Store<VvtData>, register: RegisterState, editable: boolean): void {
  store.set({
    register,
    checked: null,
    showing: register.draft ? 'draft' : 'released',
    working: editable && register.draft ? cloneContent(register.draft.content) : null,
  })
}

type Run = ReturnType<typeof createRunner<DataProtectionPort, DataProtectionError, VvtData>>

/** Eingaben im Entwurf: Inhalt ändern, Prüfung der Bibliothek anstoßen, Ansicht wechseln. */
function editActions(store: Store<VvtData>, run: Run, hooks: VvtHooks) {
  const delay = createDelay(() => hooks.checkDelay ?? 400)

  async function check(): Promise<void> {
    const current = store.get().working
    if (!current) return
    const result = await run('check', (active) => active.checkRegister(current))
    if (result && store.get().working === current) store.set({ checked: result.issues })
  }

  function update(next: RegisterContent): void {
    store.set({ working: next })
    delay.schedule(() => void check())
  }

  function show(which: 'draft' | 'released'): void {
    const draft = store.get().register?.draft
    store.set((state) => ({ showing: which, working: which === 'draft' && draft && !state.working ? cloneContent(draft.content) : state.working }))
  }

  function startDraft(): void {
    const register = store.get().register
    if (register?.draft) return show('draft')
    store.set({ working: cloneContent(register?.released?.content ?? emptyContent()), showing: 'draft', checked: null })
  }

  function discard(): void {
    const draft = store.get().register?.draft
    store.set({ working: draft ? cloneContent(draft.content) : null, checked: null })
  }

  return { check, update, show, startDraft, discard, dispose: delay.cancel }
}

/** Änderungen am Inhalt über die reinen Funktionen aus `registerView`. */
function contentActions(store: Store<VvtData>, update: (next: RegisterContent) => void) {
  const content = (): RegisterContent => vvtView(store.get()).content
  return {
    select: (index: number | null) => store.set({ selected: index }),
    toggleHistory: () => store.set((state) => ({ history: !state.history })),
    changeField(key: string, value: FieldValue): void {
      const selected = store.get().selected
      if (selected !== null) update(withField(content(), selected, key, value))
    },
    addActivity(department: string): void {
      const columns = store.get().profile?.register.columns ?? []
      update(withActivity(content(), emptyActivity(columns, department)))
      store.set({ selected: content().taetigkeiten.length - 1 })
    },
    removeActivity(): void {
      const selected = store.get().selected
      if (selected === null) return
      update(withoutActivity(content(), selected))
      store.set({ selected: content().taetigkeiten.length ? 0 : null })
    },
    changePerson: (part: 'verantwortlicher' | 'dsb', person: Person) => update(withPerson(content(), part, person)),
    changeDepartments: (departments: readonly string[]) => update(withDepartments(content(), departments)),
  }
}

/** Speichern und Freigeben über den Port; danach wird der Stand neu gelesen. */
function writeActions(store: Store<VvtData>, run: Run, hooks: VvtHooks, t: () => DataProtectionTranslate) {
  async function reload(): Promise<void> {
    const register = await run('load', (active) => active.register())
    if (register) reset(store, register, true)
  }

  async function save(): Promise<VersionView | null> {
    const current = store.get().working
    if (!current) return null
    const expected = store.get().register?.draft?.revision ?? null
    const saved = await run('save', (active) => active.saveDraft(current, expected))
    if (!saved) return null
    await reload()
    store.set({ notice: t()('saved', { version: saved.version, revision: saved.revision }) })
    hooks.onSaved?.(saved)
    return saved
  }

  async function release(): Promise<VersionView | null> {
    const draft = store.get().register?.draft
    if (!draft) return null
    const released = await run('release', (active) => active.releaseRegister(draft.revision))
    if (!released) return null
    await reload()
    store.set({ notice: t()('released', { version: released.version }) })
    hooks.onReleased?.(released)
    return released
  }

  return { save, release }
}

export interface VvtControllerOptions extends VvtHooks {
  port: () => DataProtectionPort | null
  t: () => DataProtectionTranslate
}

export function createVvtController(options: VvtControllerOptions) {
  const store = createStore<VvtData>(INITIAL)
  const hooks: VvtHooks = { ...options, networkMessage: options.networkMessage ?? ((message) => options.t()('networkError', { message })) }
  const run = createRunner(store, options.port, (error) => asError(error, hooks), hooks.onError)
  const edit = editActions(store, run, hooks)

  async function load(editable: boolean): Promise<void> {
    const loaded = await run('load', async (active) => Promise.all([active.profile(), active.register()]))
    if (!loaded) return
    store.set({ profile: loaded[0] })
    reset(store, loaded[1], editable)
    if (store.get().selected === null && vvtView(store.get()).content.taetigkeiten.length) store.set({ selected: 0 })
  }

  function exportAs(format: VvtExportFormat, lang: string): VvtExport {
    const payload = buildVvtExport(store.get(), format, options.t(), lang)
    store.set({ notice: options.t()('exported', { filename: payload.filename }) })
    return payload
  }

  return {
    store,
    load,
    exportAs,
    setNotice: (notice: string) => store.set({ notice }),
    ...edit,
    ...contentActions(store, edit.update),
    ...writeActions(store, run, hooks, options.t),
  }
}

export type VvtController = ReturnType<typeof createVvtController>
