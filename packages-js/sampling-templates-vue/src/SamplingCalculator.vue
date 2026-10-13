<script setup lang="ts">
import type { DownloadFile } from '@auditcore/common'
import { saveFile as browserSaveFile } from '@auditcore/common/browser'
import { FAMILIES, SHEETS, localizeFamilies, samplingTemplatesMessages, tableOf, withMessages, type Family, type MessageKey, type SheetModule, type Translate, type WorkspaceState } from '@auditcore/sampling-templates-core'
import { FaButton, FaDialog, translate, useI18n, type Locale } from '@auditcore/ui'
import { computed, ref, watch } from 'vue'
import DataTableDialog from './components/DataTableDialog.vue'
import MethodBar from './components/MethodBar.vue'
import MethodPicker from './components/MethodPicker.vue'
import ImportPreview from './components/ImportPreview.vue'
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
import type { MenuAction } from './types'

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
    /** Lokalen Entwurf im Web Storage dieses Browsers halten; die Anwendung schaltet ihn bewusst ein. */
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
  }>(),
  { sheets: () => SHEETS, families: () => FAMILIES, locale: undefined, messages: undefined, localDraft: false, draftKey: 'entwurf', guardUnload: true, initialState: undefined, filePrefix: undefined, dataMark: undefined, saveFile: undefined },
)
const emit = defineEmits<{ change: [state: WorkspaceState]; saved: [fileName: string]; opened: [fileName: string]; exported: [fileName: string] }>()

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
const draft = useLocalDraft(session, { enabled: () => props.localDraft, key: () => props.draftKey, hasInitialState: () => props.initialState !== undefined, sheets: () => props.sheets, t })
const { workspace, meta, notices, pickerOpen, flash, step, activeSheet, currentSheet, sections, summary, guide, strataCount, listView, selectedUnit, pasteColumns, report } = session
const shownFamilies = computed(() => localizeFamilies(props.families, locale.value))
/** Die Verfahrensauswahl steht im Schritt „Verfahren“, solange kein Verfahren gewählt ist oder es gewechselt wird. */
const choosing = computed(() => step.value === 'method' && (pickerOpen.value || activeSheet.value === null))

/** Aktion, die ungespeicherte Änderungen verwerfen würde und auf Bestätigung wartet. */
const pending = ref<(() => void) | null>(null)
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
  if (meta.value.dirty) pending.value = run
  else run()
}

function confirmDiscard(): void {
  pending.value?.()
  pending.value = null
}

const openFile = (file: File): void => guarded(() => void files.open(file))
/** Übernahme der Vorlage aus der Vorschau; das Formular wird danach neu aufgebaut. */
function applyImport(): void {
  files.applyPreview()
  revision.value += 1
}
const drop = useFileDrop(openFile)

function onMenu(action: MenuAction): void {
  if (action === 'open') fileInput.value?.click()
  else if (action === 'save') void files.save()
  else if (action === 'new') guarded(session.reset)
  else if (action === 'sample') guarded(session.loadSample)
  else draft.clear()
}

/** Bericht drucken bzw. als PDF sichern: der Druckdialog des Browsers; das Druck-Stylesheet zeigt nur die Berichtsseite. */
const print = (): void => window.print()

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
  return t('resultsUpdated', { summary: [primary, ...strong].join(', ') })
})

useUnloadGuard(() => props.guardUnload && meta.value.dirty)
watch(workspace, (state) => emit('change', state))

defineExpose({ state: workspace, open: files.open, save: files.save, exportResult: files.exportResult, reset: session.reset, loadSample: session.loadSample })
</script>

<template>
  <section class="fa-st" :aria-label="t('title')" @dragenter="drop.onDragEnter" @dragover="drop.onDragOver" @dragleave="drop.onDragLeave" @drop="drop.onDrop">
    <header class="fa-st__bar">
      <div class="fa-st__bar-inner fa-st__inner">
        <div class="fa-st__brand">
          <h2 class="fa-st__title">{{ t('title') }}</h2>
          <p class="fa-st__muted">{{ currentSheet && !choosing ? `${currentSheet.definition.number} · ${currentSheet.definition.title}` : t('subtitle') }}</p>
        </div>
        <div v-if="$slots.mark || dataMark" class="fa-st__mark" data-mark><slot name="mark">{{ dataMark }}</slot></div>
        <p class="fa-st__status" :class="statusClass" data-status><span class="fa-st__dot" aria-hidden="true"></span>{{ statusText }}</p>
        <WorkspaceMenu :t="t" :draft="localDraft" @action="onMenu" />
        <FaButton variant="primary" :label="t('exportResult')" data-action="export" @click="files.exportResult()" />
        <input ref="fileInput" type="file" accept=".json,.xlsx,application/json" hidden :aria-label="t('menuOpen')" @change="onFileChosen" />
      </div>
    </header>

    <MethodBar :definition="activeSheet?.definition ?? null" :step="step" :sheets="sheets" :t="t" @change="((step = 'method'), (pickerOpen = true))" @step="session.setStep" @table="shownTable = $event" />
    <div class="fa-st__inner"><NoticeList :notices="notices" :sample="meta.sample && !choosing" :t="t" @dismiss="session.dismiss" @clear="guarded(session.reset)" /></div>
    <MethodPicker v-if="choosing" :families="shownFamilies" :sheets="sheets" :t="t" :current="workspace.activeMethod" :guide="guide" @select="session.selectMethod" @table="shownTable = $event" />
    <div v-else-if="currentSheet" class="fa-st__inner" :data-sheet-view="currentSheet.id">
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
      <ReportView v-if="report" :report="report" :t="t" @update="session.setInput" @print="print" />
      <div v-else-if="summary" class="fa-st__main">
        <SheetForm
          :key="`${currentSheet.id}-${selectedUnit}-${revision}`"
          :sections="sections"
          :strata="strataCount"
          :t="t"
          @update="session.setInput"
          @add-stratum="session.addStratum"
          @remove-stratum="session.removeStratum"
        />
        <aside class="fa-st__aside" :aria-label="t('results')">
          <ResultPanel :summary="summary" :t="t" />
          <p class="fa-st__muted">{{ t('privacy') }}</p>
        </aside>
      </div>
    </div>

    <footer class="fa-st__footer fa-st__inner">
      <p class="fa-st__muted" data-disclaimer>{{ t('disclaimer') }}</p>
      <p class="fa-st__muted" data-template-status>{{ t('templateStatus') }}</p>
      <p v-if="localDraft" class="fa-st__muted">{{ t('draftNote') }}</p>
      <p v-if="locale !== 'de'" class="fa-st__muted" data-translation-note>{{ t('workingTranslation') }}</p>
      <p class="fa-st__flash" role="status" data-flash>{{ flash }}</p>
    </footer>
    <p class="fa-sr-only" aria-live="polite" aria-atomic="true" data-live>{{ announced }}</p>
    <div v-if="drop.dragging.value" class="fa-st__drop">{{ t('dropHere') }}</div>

    <DataTableDialog :table="shownTable ? (tableOf(shownTable, sheets) ?? null) : null" :t="t" :locale="locale" @close="shownTable = null" />
    <ImportPreview :preview="files.preview.value" :t="t" :locale="locale" @apply="applyImport" @cancel="files.cancelPreview" />
    <FaDialog :open="pending !== null" :title="t('discardTitle')" size="sm" :locale="locale" @update:open="pending = null">
      <p>{{ t('discardText') }}</p>
      <template #footer>
        <FaButton :label="t('cancel')" @click="pending = null" />
        <FaButton variant="danger" :label="t('discard')" data-action="discard" @click="confirmDiscard" />
      </template>
    </FaDialog>
  </section>
</template>
