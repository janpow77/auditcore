<script setup lang="ts">
import type { DownloadFile } from '@auditcore/common'
import { saveFile as browserSaveFile } from '@auditcore/common/browser'
import { FAMILIES, SHEETS, localizeFamilies, samplingTemplatesMessages, tableOf, withMessages, workspaceChecksum, type Family, type MessageKey, type SheetModule, type Translate, type WorkspaceState } from '@auditcore/sampling-templates-core'
import { FaButton, FaDialog, translate, useI18n, type Locale } from '@auditcore/ui'
import { computed, nextTick, ref, watch } from 'vue'
import DataTableDialog from './components/DataTableDialog.vue'
import MethodBar from './components/MethodBar.vue'
import MethodPicker from './components/MethodPicker.vue'
import ImportPreview from './components/ImportPreview.vue'
import KpiStrip from './components/KpiStrip.vue'
import NoticeList from './components/NoticeList.vue'
import ReportView from './components/ReportView.vue'
import ResultPanel from './components/ResultPanel.vue'
import SheetForm from './components/SheetForm.vue'
import UnitList from './components/UnitList.vue'
import WorkspaceMenu from './components/WorkspaceMenu.vue'
import { useAnnouncer, useFileDrop, useUnloadGuard } from './composables/useBrowserGuards'
import { useFileActions } from './composables/useFileActions'
import { useLocalDraft } from './composables/useLocalDraft'
import { useSamplingSession } from './composables/useSamplingSession'
import type { DraftMode, MenuAction } from './types'

/**
 * Stichprobenrechner als Ganzes: Verfahrensauswahl, Rechenblatt mit mitlaufender
 * Ergebnisspalte, Arbeitsstand als Datei und Excel-Export. Alles läuft im Browser;
 * es gibt keine Netzanfragen.
 */
const props = withDefaults(
  defineProps<{
    /** Blätter mit und ohne Rechenkern (Standard: Register des Kerns). */
    sheets?: readonly SheetModule[]
    /** Verfahrensfamilien der Auswahl (Standard: Katalog nach Blatt 00). */
    families?: readonly Family[]
    locale?: Locale
    /** Überschriebene bzw. englische Texte der Oberfläche. */
    messages?: { de?: Partial<Record<MessageKey, string>>; en?: Partial<Record<MessageKey, string>> }
    /**
     * Zwischenstand im Web Storage dieses Browsers: `off` (Vorgabe), `session` (nur diese Sitzung) oder
     * `device` (auf diesem Gerät behalten). Den Umschalter bietet die Anwendung an (Slot `draft`, Ereignis `draft`).
     */
    draft?: DraftMode
    /** Veraltet: `true` entspricht `draft="device"`. */
    localDraft?: boolean
    /** Schlüssel des lokalen Entwurfs; je Anwendung verschieden wählen. */
    draftKey?: string
    /** Browser-Warnung bei ungespeicherten Änderungen. */
    guardUnload?: boolean
    initialState?: WorkspaceState
    /** Vorsatz der Dateinamen von Arbeitsstand und Export (Standard: „Stichprobe“). */
    filePrefix?: string
    /** Datenmarke der Anwendung als Text neben dem Titel; mehr Gestaltung über den Slot `mark`. */
    dataMark?: string
    /** Eigene Übergabe von Dateien an den Browser (Standard: Download über Blob). */
    saveFile?: (file: DownloadFile) => void | Promise<void>
    /** Menü „Arbeitsstand“ im Rechner; `false` bei eigenem Menü der Anwendung (`runAction()`, `openFile()`). */
    workspaceMenu?: boolean
  }>(),
  { sheets: () => SHEETS, families: () => FAMILIES, locale: undefined, messages: undefined, draft: 'off', localDraft: false, draftKey: 'entwurf', guardUnload: true, initialState: undefined, filePrefix: undefined, dataMark: undefined, saveFile: undefined, workspaceMenu: true },
)
const emit = defineEmits<{ change: [state: WorkspaceState]; saved: [fileName: string]; opened: [fileName: string]; exported: [fileName: string]; draft: [status: { mode: DraftMode; stored: boolean }]; dirty: [dirty: boolean] }>()

const { locale } = useI18n(samplingTemplatesMessages, () => props.locale)
const catalogs = computed(() => withMessages(props.messages))
const t: Translate = (key, params) => translate(catalogs.value, locale.value, key, params)

const session = useSamplingSession({ sheets: () => props.sheets, t, locale: () => locale.value, initial: props.initialState })
const files = useFileActions(session, {
  sheets: () => props.sheets,
  t,
  filePrefix: () => props.filePrefix,
  deliver: (file) => (props.saveFile ?? browserSaveFile)(file),
  onSaved: (name) => emit('saved', name),
  onOpened: (name) => emit('opened', name),
  onExported: (name) => emit('exported', name),
})
/** Stufe des Zwischenstands; die frühere Prop `localDraft` steht für „auf diesem Gerät“. */
const draftMode = computed<DraftMode>(() => (props.draft !== 'off' ? props.draft : props.localDraft ? 'device' : 'off'))
const draft = useLocalDraft(session, { mode: () => draftMode.value, onStored: (stored) => emit('draft', { mode: draftMode.value, stored }), key: () => props.draftKey, hasInitialState: () => props.initialState !== undefined, sheets: () => props.sheets, t })
const { workspace, meta, notices, pickerOpen, flash, step, activeSheet, currentSheet, sections, summary, guide, strataCount, listView, selectedUnit, pasteColumns, report } = session
const shownFamilies = computed(() => localizeFamilies(props.families, locale.value))
/** Die Verfahrensauswahl steht im Schritt „Verfahren“, solange kein Verfahren gewählt ist oder es gewechselt wird. */
const choosing = computed(() => step.value === 'method' && (pickerOpen.value || activeSheet.value === null))

/** Aktion, die auf Bestätigung wartet: Sie würde ungespeicherte Änderungen (`discard`) oder die Eingaben einer Schicht (`stratum`) verwerfen. */
const pending = ref<{ run: () => void; kind: 'discard' | 'stratum' } | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
/** Blatt der gerade geöffneten Nachschlagetabelle (X1a). */
const shownTable = ref<string | null>(null)
/** Zähler, der das Formular nach Neu, Öffnen und Beispielwerten neu aufbaut. */
const revision = ref(0)

function guarded(action: () => void): void {
  const run = (): void => {
    action()
    revision.value += 1
  }
  if (meta.value.dirty) pending.value = { run, kind: 'discard' }
  else run()
}

const confirmDiscard = (): void => void (pending.value?.run(), (pending.value = null))

/** „Schicht entfernen“: Trägt die letzte Schicht Eingaben, fragt die Oberfläche vorher nach. */
function removeStratum(): void {
  if (session.lastStratumFilled.value) pending.value = { run: session.removeStratum, kind: 'stratum' }
  else session.removeStratum()
}

/** Nach der Wahl eines Blatts steht der Fokus auf dem Blatt (sonst fiele er mit der Kachel auf die Seite zurück). */
const sheetView = ref<HTMLElement | null>(null)
function selectMethod(id: string): void {
  session.selectMethod(id)
  void nextTick(() => sheetView.value?.focus())
}

const openFile = (file: File): void => guarded(() => void files.open(file))
/** Übernahme der Vorlage aus der Vorschau; das Formular wird danach neu aufgebaut. */
const applyImport = (): void => void (files.applyPreview(), (revision.value += 1))
const drop = useFileDrop(openFile)

function onMenu(action: MenuAction): void {
  if (action === 'open') fileInput.value?.click()
  else if (action === 'save') void files.save()
  else if (action === 'new') guarded(resetAll)
  else if (action === 'sample') guarded(session.loadSample)
  else draft.clear()
}

/** Prüfsumme der Eingaben für den Bericht; sie ordnet den Ausdruck dem Arbeitsstand zu. */
const checksum = ref('')
watch([workspace, report], ([state, shown]) => (shown ? void workspaceChecksum(state).then((value) => (checksum.value = value)) : undefined), { immediate: true })

/** Bericht drucken bzw. als PDF sichern: der Druckdialog des Browsers; das Druck-Stylesheet zeigt nur die Berichtsseite. */
const print = (): void => window.print()

/** Zurücksetzen: leeres Formular und kein Zwischenstand mehr, in keiner der beiden Ablagen. */
function resetAll(): void {
  session.reset()
  draft.clear(false)
}

function onFileChosen(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (file) openFile(file)
}

const statusText = computed(() => {
  const name = meta.value.fileName ?? t(meta.value.sample ? 'statusSample' : 'statusNew')
  if (meta.value.dirty) return `${name} · ${t('statusChanged')}`
  return meta.value.fileName ? `${name} · ${t('statusSaved')}` : name
})
const statusClass = computed(() => (meta.value.dirty ? 'fa-st__status--changed' : meta.value.fileName ? 'fa-st__status--saved' : ''))
const announced = useAnnouncer(() => {
  const view = summary.value
  if (!view) return ''
  const strong = view.rows.filter((row) => row.strong).map((row) => `${row.label} ${row.value}`)
  const primary = `${view.primaryLabel} ${view.primaryValue ? `${view.primaryValue} ${view.primaryUnit}` : view.primaryNote || t('noValue')}`
  return t('resultsUpdated', { summary: [primary, ...strong, ...(view.invalidNote ? [view.invalidNote] : [])].join(', ') })
})

useUnloadGuard(() => props.guardUnload && meta.value.dirty)
watch(workspace, (state) => emit('change', state))
/** Ungesicherte Änderungen, für den Routenwächter der Anwendung: Ereignis `dirty` und die Methode `isDirty()`. */
const dirty = computed(() => meta.value.dirty)
watch(dirty, (value) => emit('dirty', value), { immediate: true })

defineExpose({ dirty, isDirty: (): boolean => meta.value.dirty, state: workspace, open: files.open, save: files.save, exportResult: files.exportResult, reset: resetAll, loadSample: session.loadSample, openFile, runAction: onMenu, clearDraft: () => draft.clear(false) })
</script>

<template>
  <section class="fa-st" :aria-label="t('title')" @dragenter="drop.onDragEnter" @dragover="drop.onDragOver" @dragleave="drop.onDragLeave" @drop="drop.onDrop">
    <header class="fa-st__bar">
      <div class="fa-st__bar-inner fa-st__inner">
        <div class="fa-st__brand">
          <h2 class="fa-st__title">{{ t('title') }}</h2>
          <p class="fa-st__muted">{{ currentSheet && !choosing ? currentSheet.definition.title : t('subtitle') }}</p>
        </div>
        <div v-if="$slots.mark || dataMark" class="fa-st__mark" data-mark><slot name="mark">{{ dataMark }}</slot></div>
        <p class="fa-st__status" :class="statusClass" data-status><span class="fa-st__dot" aria-hidden="true"></span>{{ statusText }}</p>
        <WorkspaceMenu v-if="workspaceMenu" :t="t" :draft="draftMode !== 'off'" @action="onMenu" />
        <FaButton variant="primary" :label="t('exportResult')" data-action="export" @click="files.exportResult()" />
        <input ref="fileInput" type="file" accept=".json,.xlsx,application/json" hidden :aria-label="t('menuOpen')" @change="onFileChosen" />
      </div>
    </header>

    <MethodBar :definition="activeSheet?.definition ?? null" :step="step" :choosing="choosing" :sheets="sheets" :t="t" @change="((step = 'method'), (pickerOpen = true))" @step="session.setStep" @table="shownTable = $event" />
    <div class="fa-st__inner"><NoticeList :notices="notices" :sample="meta.sample && !choosing" :t="t" @dismiss="session.dismiss" @clear="guarded(resetAll)" /></div>
    <MethodPicker v-if="choosing" :families="shownFamilies" :sheets="sheets" :t="t" :current="workspace.activeMethod" :guide="guide" @select="selectMethod" @table="shownTable = $event" />
    <div v-else-if="currentSheet" ref="sheetView" class="fa-st__inner fa-st__sheet" tabindex="-1" :aria-label="currentSheet.definition.title" :data-sheet-view="currentSheet.id">
      <UnitList
        v-if="listView"
        :view="listView"
        :selected="selectedUnit"
        :method-number="activeSheet?.definition.number ?? ''"
        :paste-columns="pasteColumns"
        :t="t"
        :locale="locale"
        @select="selectedUnit = $event"
        @add="session.addUnit"
        @remove="session.removeUnit"
        @paste="session.pasteUnits"
        @transfer="session.transferSubsamples"
      />
      <ReportView v-if="report" :report="report" :checksum="checksum" :t="t" @update="session.setInput" @print="print" />
      <div v-else-if="summary" class="fa-st__main">
        <KpiStrip :summary="summary" :t="t" />
        <SheetForm
          :key="`${currentSheet.id}-${selectedUnit}-${revision}`"
          :sections="sections"
          :strata="strataCount"
          :t="t"
          @update="session.setInput"
          @add-stratum="session.addStratum"
          @remove-stratum="removeStratum"
        />
        <aside class="fa-st__aside" :aria-label="t('results')">
          <ResultPanel :summary="summary" :t="t" />
          <p class="fa-st__muted">{{ t('privacy') }}</p>
        </aside>
      </div>
    </div>

    <footer class="fa-st__footer fa-st__inner">
      <p class="fa-st__muted" data-disclaimer>{{ t('disclaimer') }}</p>
      <p class="fa-st__muted" data-template-status>{{ t('templateStatus') }} {{ t('verificationNote') }}</p>
      <p v-if="draftMode !== 'off'" class="fa-st__muted" data-draft-note>{{ t(draftMode === 'session' ? 'draftNoteSession' : 'draftNote') }}</p>
      <slot name="draft" :mode="draftMode" :stored="draft.stored.value" :clear="() => draft.clear()"></slot>
      <p v-if="locale !== 'de'" class="fa-st__muted" data-translation-note>{{ t('workingTranslation') }}</p>
      <p class="fa-st__flash" role="status" data-flash>{{ flash }}</p>
    </footer>
    <p class="fa-sr-only" aria-live="polite" aria-atomic="true" data-live>{{ announced }}</p>
    <div v-if="drop.dragging.value" class="fa-st__drop">{{ t('dropHere') }}</div>

    <DataTableDialog :table="shownTable ? (tableOf(shownTable, sheets) ?? null) : null" :t="t" :locale="locale" @close="shownTable = null" />
    <ImportPreview :preview="files.preview.value" :t="t" :locale="locale" @apply="applyImport" @cancel="files.cancelPreview" />
    <FaDialog :open="pending !== null" :title="t(pending?.kind === 'stratum' ? 'removeStratumTitle' : 'discardTitle')" size="sm" :locale="locale" @update:open="pending = null">
      <p class="fa-st__scope">{{ t(pending?.kind === 'stratum' ? 'removeStratumText' : 'discardText') }}</p>
      <template #footer>
        <FaButton :label="t('cancel')" @click="pending = null" />
        <FaButton variant="danger" :label="t(pending?.kind === 'stratum' ? 'removeStratum' : 'discard')" data-action="discard" @click="confirmDiscard" />
      </template>
    </FaDialog>
  </section>
</template>

