/** Abgeleitete Anzeige der Vergleichsverwaltung (reine Funktion, von Vue und React genutzt). */
import type { ComparisonsData } from './controller'
import { DEFAULT_MAX_UPLOAD_BYTES, defaultProfile, formatBytes, formProblems, involvesPdf, type FormProblem, type UploadFile } from './form'
import { filterSummaries, summaryView, type SummaryView } from './list'
import type { ComparisonsMessageKey, ComparisonsTranslate } from './messages'

export interface ProblemView {
  field: FormProblem['field']
  text: string
}

export interface ProfileOption {
  /** Leer: Vorgabe des Servers. */
  value: string
  label: string
}

export interface ComparisonsView {
  rows: SummaryView[]
  total: number
  countText: string
  /** Hinweis bei leerer Liste, sonst `null`. */
  emptyText: string | null
  problems: ProblemView[]
  profileOptions: ProfileOption[]
  sizeHint: string
  oldFileText: string
  newFileText: string
  oldFileLabel: string
  newFileLabel: string
  pdfHint: boolean
  busyText: string
  pendingTitle: string | null
  openTitle: string | null
}

export interface ComparisonsViewOptions {
  lang: string
  maxBytes?: number
}

function fileText(file: UploadFile | null, t: ComparisonsTranslate, lang: string): string {
  return file ? t('fileChosen', { name: file.name, size: formatBytes(file.size, lang) }) : ''
}

function profileOptions(state: ComparisonsData, t: ComparisonsTranslate): ProfileOption[] {
  const fallback = defaultProfile(state.profiles)
  return state.profiles.map((profile) => ({
    value: profile.id === fallback?.id ? '' : profile.id,
    label: t(profile.id === fallback?.id ? 'profileDefault' : 'profileOption', { id: profile.id, version: profile.version }),
  }))
}

function emptyText(state: ComparisonsData, shown: number, t: ComparisonsTranslate): string | null {
  if (!state.loaded || shown > 0) return null
  return state.items.length === 0 ? t('empty') : t('noMatches')
}

function titleOf(state: ComparisonsData, id: string | null): string | null {
  if (id === null) return null
  return state.items.find((item) => item.id === id)?.title ?? id
}

function problems(state: ComparisonsData, t: ComparisonsTranslate, maxBytes: number, lang: string): ProblemView[] {
  if (!state.submitted) return []
  return formProblems(state.form, maxBytes, lang).map((problem) => ({ field: problem.field, text: t(problem.key, problem.params) }))
}

export function comparisonsView(state: ComparisonsData, t: ComparisonsTranslate, options: ComparisonsViewOptions): ComparisonsView {
  const { lang } = options
  const maxBytes = options.maxBytes ?? DEFAULT_MAX_UPLOAD_BYTES
  const rows = filterSummaries(state.items, state.query).map((item) => summaryView(item, t, lang))
  const articleLaw = state.form.kind === 'article_law'
  return {
    rows,
    total: state.items.length,
    countText: t('listCount', { count: rows.length, total: state.items.length }),
    emptyText: emptyText(state, rows.length, t),
    problems: problems(state, t, maxBytes, lang),
    profileOptions: profileOptions(state, t),
    sizeHint: t('fileHint', { size: formatBytes(maxBytes, lang) }),
    oldFileText: fileText(state.form.oldFile, t, lang),
    newFileText: fileText(state.form.newFile, t, lang),
    oldFileLabel: t(articleLaw ? 'oldFileArticleLaw' : 'oldFile'),
    newFileLabel: t(articleLaw ? 'newFileArticleLaw' : 'newFile'),
    pdfHint: !articleLaw && involvesPdf(state.form),
    busyText: state.busy ? t(`busy_${state.busy}` as ComparisonsMessageKey) : '',
    pendingTitle: titleOf(state, state.pendingRemove),
    openTitle: titleOf(state, state.openId),
  }
}
