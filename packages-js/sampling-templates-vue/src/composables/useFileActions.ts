/**
 * Dateiaktionen: Arbeitsstand speichern, Ergebnis exportieren, Datei öffnen
 * (`.json`, Export `.xlsx`, ausgefüllte Vorlage). Der Excel-Austausch wird erst
 * geladen, wenn er gebraucht wird; es gibt keine Netzanfragen. Jede Aktion
 * meldet einen Fehler sichtbar, statt ihn zu verschlucken; eine ausgefüllte
 * Vorlage wird erst nach einer Vorschau übernommen.
 */
import { formatDateTime, type DownloadFile } from '@auditcore/common'
import {
  MAX_WORKSPACE_SIZE,
  WORKFLOW_STEPS,
  describeNotice,
  describeOpenError,
  openWorkspace,
  saveWorkspace,
  type CellMap,
  type SheetModule,
  type Translate,
  type WorkspaceState,
} from '@auditcore/sampling-templates-core'
import type { WorkbookImport } from '@auditcore/sampling-templates-core/xlsx'
import { shallowRef, type ShallowRef } from 'vue'
import type { ImportPreviewData } from '../components/ImportPreview.vue'
import type { SamplingSession } from './useSamplingSession'

export interface FileActionOptions {
  sheets: () => readonly SheetModule[]
  t: Translate
  /** Vorsatz der vorgeschlagenen Dateinamen. */
  filePrefix?: () => string | undefined
  /** Übergibt eine Datei an den Browser (Standard: Download über Blob). */
  deliver: (file: DownloadFile) => void | Promise<void>
  onSaved?: (fileName: string) => void
  onOpened?: (fileName: string) => void
  onExported?: (fileName: string) => void
}

export interface FileActions {
  save: () => Promise<void>
  exportResult: () => Promise<void>
  open: (file: File) => Promise<void>
  /** Vorschau einer ausgefüllten Vorlage, die auf Übernahme wartet. */
  preview: ShallowRef<ImportPreviewData | null>
  applyPreview: () => void
  cancelPreview: () => void
}

type TemplateImport = Extract<WorkbookImport, { kind: 'template' }>

/** Blätter, die kein Verfahren sind (Arbeitsschritte um das Methodenblatt herum). */
const NOT_A_METHOD: ReadonlySet<string> = new Set(WORKFLOW_STEPS.flatMap((step) => (step.sheet ? [step.sheet] : [])))

const loadXlsx = () => import('@auditcore/sampling-templates-core/xlsx')

/** Arbeitsstand nach der Übernahme: die Blätter der Vorlage ersetzen die bisherigen Eingaben dieser Blätter. */
function candidate(current: WorkspaceState, imported: TemplateImport): WorkspaceState {
  const sheets = { ...current.sheets }
  for (const id of imported.filled) sheets[id] = imported.sheets[id] ?? {}
  // Verfahren: das in Blatt 18 der Mappe gewählte, sonst das bisherige, sonst das erste ausgefüllte Methodenblatt.
  return { ...current, activeMethod: imported.method ?? current.activeMethod ?? imported.filled.find((id) => !NOT_A_METHOD.has(id)) ?? null, sheets }
}

const countValues = (imported: TemplateImport): number =>
  imported.filled.reduce((total, id) => {
    const inputs = imported.sheets[id]
    return total + (Array.isArray(inputs) ? (inputs as readonly CellMap[]).reduce((sum, row) => sum + Object.keys(row).length, 0) : Object.keys(inputs ?? {}).length)
  }, 0)

type Compare = typeof import('@auditcore/sampling-templates-core/xlsx').compareWithWorkbook

/** Vorschau einer ausgefüllten Vorlage: alle Umdeutungen und die Gegenprobe gegen die Rechenwerte der Mappe; Übernahme erst auf Bestätigung. */
function useTemplatePreview(session: SamplingSession, options: FileActionOptions) {
  const { t } = options
  const preview = shallowRef<ImportPreviewData | null>(null)
  let pendingState: WorkspaceState | null = null

  function cancelPreview(): void {
    preview.value = null
    pendingState = null
  }

  return {
    preview,
    cancelPreview,
    show(imported: TemplateImport, fileName: string, compare: Compare): void {
      if (imported.filled.length === 0 && imported.issues.length === 0) return session.notify('warning', t('noticeTemplateEmpty', { file: fileName }))
      pendingState = candidate(session.workspace.value, imported)
      const cached = Object.fromEntries(imported.filled.map((id) => [id, imported.cached[id] ?? {}]))
      const differences = compare(pendingState, cached, options.sheets())
      preview.value = { file: fileName, sheets: imported.filled, count: countValues(imported), pending: imported.pending, issues: imported.issues, differences }
    },
    applyPreview(): void {
      const data = preview.value
      if (!data || !pendingState) return
      const notices = [{ tone: 'info' as const, text: t('noticeTemplate', { file: data.file, sheets: data.sheets.join(', ') }) }]
      session.replace(pendingState, { fileName: null, dirty: true, sample: false }, notices)
      options.onOpened?.(data.file)
      cancelPreview()
    },
  }
}

export function useFileActions(session: SamplingSession, options: FileActionOptions): FileActions {
  const { t } = options
  const template = useTemplatePreview(session, options)

  /** Führt eine Dateiaktion aus und meldet jeden Fehler in der Oberfläche. */
  async function reported(message: string, action: () => Promise<void>): Promise<void> {
    try {
      await action()
    } catch (error) {
      console.error(error)
      session.notify('danger', message)
    }
  }

  const save = (): Promise<void> =>
    reported(t('errorSave'), async () => {
      const saved = await saveWorkspace(session.workspace.value, { sheets: options.sheets(), t, filePrefix: options.filePrefix?.() })
      await options.deliver({ blob: new Blob([saved.text], { type: 'application/json' }), filename: saved.fileName, mediaType: 'application/json' })
      session.markSaved(saved.fileName)
      session.say(t('saved'))
      options.onSaved?.(saved.fileName)
    })

  const exportResult = (): Promise<void> =>
    reported(t('errorSave'), async () => {
      const { exportWorkbook } = await loadXlsx()
      const exported = await exportWorkbook(session.workspace.value, { sheets: options.sheets(), t, filePrefix: options.filePrefix?.() })
      const blob = new Blob([exported.data.slice().buffer], { type: exported.mediaType })
      await options.deliver({ blob, filename: exported.fileName, mediaType: exported.mediaType })
      session.say(t('exported'))
      options.onExported?.(exported.fileName)
    })

  async function applyText(text: string, fileName: string): Promise<void> {
    const result = await openWorkspace(text, { sheets: options.sheets() })
    if (!result.ok) return session.notify('danger', describeOpenError(result.error, t))
    const notices = result.notices.map((notice) => ({ tone: 'warning' as const, text: describeNotice(notice, t) }))
    session.replace(result.state, { fileName, dirty: false, sample: false }, notices)
    session.say(result.savedAt ? t('openedAt', { date: formatDateTime(result.savedAt) }) : t('opened'))
    options.onOpened?.(fileName)
  }

  async function openWorkbook(file: File): Promise<void> {
    const xlsx = await loadXlsx()
    if (file.size > xlsx.MAX_WORKBOOK_SIZE) return session.notify('danger', t('errorTooLarge'))
    let imported: WorkbookImport
    try {
      imported = xlsx.importWorkbook(new Uint8Array(await file.arrayBuffer()), options.sheets())
    } catch (error) {
      if (error instanceof xlsx.WorkbookError) return session.notify('danger', t('errorWorkbookRead'))
      throw error
    }
    if (imported.kind === 'workspace') await applyText(imported.text, file.name)
    else if (imported.kind === 'template') template.show(imported, file.name, xlsx.compareWithWorkbook)
    else session.notify('danger', t('errorWorkbook'))
  }

  const open = (file: File): Promise<void> =>
    reported(t('errorFile', { file: file.name }), async () => {
      const name = file.name.toLowerCase()
      if (name.endsWith('.xlsx')) return openWorkbook(file)
      if (!name.endsWith('.json')) return session.notify('danger', t('errorFileType'))
      if (file.size > MAX_WORKSPACE_SIZE) return session.notify('danger', t('errorTooLarge'))
      await applyText(await file.text(), file.name)
    })

  return { save, exportResult, open, preview: template.preview, applyPreview: template.applyPreview, cancelPreview: template.cancelPreview }
}
