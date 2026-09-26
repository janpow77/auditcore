<script setup lang="ts">
/**
 * FlowAudit BPMN editor: toolbar, palette, canvas with page grid, side panel
 * (properties, issues, walk-through, comparison), status bar and dialogs.
 * The XML is bound with `v-model:xml`; ports connect storage-independent
 * services of the application (legal search, KA/BK catalogue, validation,
 * ESI).
 */
import { computed, onMounted, ref, watch } from 'vue'
import { label, PALETTE_COLORS, profileReference, rolesFor, type Approval, type Comment, type DiagramInfo, type PaletteColor, type ProfileData, type ProfileSummary, type RoleAlias, type ValidationPort } from '@flowaudit/bpmn-flowaudit'
import { activeActions, choosePopoverColor, choosePopoverRole, createExporter, dialogPatch, filterKeys as keyIndex, handleShortcut, isLocked, readImportFile, savePayload, type CompareSource, type EditorFactory, type ToolbarAction } from '@flowaudit/bpmn-flowaudit/ui'
import { defaultEditorFactory } from '../editor/defaultFactory'
import { createI18n, provideI18n, type Locale } from '../i18n/useI18n'
import type { EditorPorts } from '../stores/context'
import { useEditorActions } from '../composables/useEditorActions'
import { useEditorSetup } from '../composables/useEditorSetup'
import EditorToolbar from './toolbar/EditorToolbar.vue'
import ToolPalette from './palette/ToolPalette.vue'
import PageGrid from './canvas/PageGrid.vue'
import StatusBar from './canvas/StatusBar.vue'
import CanvasPopover from './canvas/CanvasPopover.vue'
import ColorSwatches from './base/ColorSwatches.vue'
import KeyFilterBar from './views/KeyFilterBar.vue'
import EditorSidePanel from './EditorSidePanel.vue'
import EditorDialogs from './EditorDialogs.vue'
import '@flowaudit/bpmn-flowaudit/ui.css'

const props = withDefaults(
  defineProps<{
    xml: string
    name?: string
    diagramId?: string
    profile?: ProfileData | null
    profiles?: ProfileSummary[]
    ports?: EditorPorts & { validation?: ValidationPort }
    locale?: Locale
    readonly?: boolean
    lockApproved?: boolean
    comments?: Comment[]
    approvals?: Approval[]
    author?: string
    compareSources?: CompareSource[]
    palette?: readonly PaletteColor[]
    roleAliases?: RoleAlias[]
    replacements?: Record<string, string>
    hiddenActions?: ToolbarAction[]
    saving?: boolean
    editorFactory?: EditorFactory
    theme?: 'auto' | 'light' | 'dark'
  }>(),
  { name: '', diagramId: undefined, palette: undefined, editorFactory: undefined, theme: undefined, profile: null, profiles: () => [], ports: () => ({}), locale: 'de', lockApproved: true, comments: () => [], approvals: () => [], author: '', compareSources: () => [], roleAliases: () => [], replacements: () => ({}), hiddenActions: () => [] },
)
const emit = defineEmits<{
  (e: 'update:xml', xml: string): void
  (e: 'update:name', name: string): void
  (e: 'update:comments', comments: Comment[]): void
  (e: 'save', payload: { xml: string; info: DiagramInfo | null }): void
  (e: 'new'): void
  (e: 'analysis'): void
  (e: 'share'): void
  (e: 'export-excel'): void
  (e: 'approve', payload: { xml: string; info: DiagramInfo }): void
  (e: 'selection-change', elementId: string | null): void
  (e: 'error', message: string): void
  (e: 'ready'): void
  (e: 'info-change', info: DiagramInfo | null): void
}>()

const i18n = provideI18n(createI18n(props.locale))
const { t } = i18n
const host = ref<HTMLElement | null>(null)
const factory = props.editorFactory ?? defaultEditorFactory
const isReadonly = () => isLocked(props.readonly, props.lockApproved, setup.editor.state.info as DiagramInfo | null)

const setup = useEditorSetup(host, {
  xml: () => props.xml,
  profile: () => props.profile,
  readonly: isReadonly,
  locale: props.locale,
  ports: props.ports,
  factory,
  onXml: (xml) => emit('update:xml', xml),
  onError: (message) => ((setup.ui.message = t('editor.importError', { message })), emit('error', message)),
})
const { editor, selection, validation, ui } = setup
const exporter = createExporter({ editor, factory, name: () => props.name, diagramId: () => props.diagramId, profile: () => props.profile, author: () => props.author, replacements: () => props.replacements, palette: props.palette })

async function save(): Promise<void> {
  if (!isReadonly()) emit('save', await savePayload(setup.session))
}

const actions = useEditorActions(
  setup,
  {
    save,
    newDiagram: () => emit('new'),
    analysis: () => emit('analysis'),
    share: () => emit('share'),
    excel: () => emit('export-excel'),
    approve: async (info) => emit('approve', { xml: await editor.exportXml(), info }),
    message: (text) => (ui.message = text),
  },
  { profile: () => props.profile, roleAliases: () => props.roleAliases, exporter, t },
)

const roles = computed(() => rolesFor(props.profile))
const filterKeys = computed(() => (void editor.state.changes, keyIndex(setup.session, ui.filterOpen)))
const active = computed(() => activeActions(ui))
const chooseRole = (code: string) => choosePopoverRole(setup.session, props.profile, code)
const chooseColor = (color: PaletteColor | null) => choosePopoverColor(setup.session, color)

async function importFile(file: File): Promise<void> {
  const imported = await readImportFile(file)
  emit('update:xml', imported.xml)
  if (!props.name) emit('update:name', imported.name)
}

function onKeydown(event: KeyboardEvent): void {
  handleShortcut(event, { save, search: () => Object.assign(ui, dialogPatch(ui, 'search', true)), help: () => Object.assign(ui, dialogPatch(ui, 'shortcuts', true)) })
}

watch(() => selection.element.value, (element) => emit('selection-change', element?.id ?? null))
watch(() => editor.state.info, (info) => emit('info-change', info as DiagramInfo | null))
watch(() => props.theme, (theme) => theme && (actions.theme.value = theme), { immediate: true })

onMounted(async () => {
  setup.mount()
  await setup.load(props.xml)
  emit('ready')
})

defineExpose({ getXml: () => editor.exportXml(), getSvg: () => editor.exportSvg(), select: (id: string) => editor.select(id), editor, validation, highlightKey: (kind: typeof ui.filterKind, value: string) => Object.assign(ui, { filterOpen: true, filterKind: kind, filterValue: value }) })
</script>

<template>
  <div class="fa-root fa-editor" :data-fa-theme="actions.theme.value" :lang="locale" @keydown="onKeydown">
    <EditorToolbar
      :name="name"
      :dirty="editor.state.dirty"
      :saving="Boolean(saving)"
      :readonly="isReadonly()"
      :can-undo="editor.state.canUndo"
      :can-redo="editor.state.canRedo"
      :direction="ui.direction"
      :page-view="ui.pageView"
      :active="active"
      :hidden="hiddenActions"
      :palette="palette"
      @action="actions.run"
      @update:name="emit('update:name', $event)"
      @color="actions.color"
      @direction="setup.setDirection"
      @page-view="ui.pageView = $event"
      @import-file="importFile"
    />
    <div class="fa-editor__body">
      <ToolPalette v-if="ui.leftOpen" :items="setup.palette.value" :disabled="isReadonly()" @trigger="setup.trigger" />
      <main class="fa-editor__main">
        <KeyFilterBar v-if="ui.filterOpen" v-model:kind="ui.filterKind" v-model:value="ui.filterValue" :keys="filterKeys" :hits="ui.filterHits" @clear="(ui.filterValue = ''), (ui.filterOpen = false)" />
        <div ref="host" class="fa-canvas-host" tabindex="0" :aria-label="t('editor.label')" :class="{ 'fa-canvas-host--readonly': isReadonly() }">
          <PageGrid :view="ui.pageView" :viewbox="setup.viewbox.value" :width="setup.size.value.width" :height="setup.size.value.height" />
          <CanvasPopover v-if="setup.popover.value" :x="setup.popover.value.x" :y="setup.popover.value.y" :width="setup.size.value.width" :height="setup.size.value.height" :title="setup.popover.value.kind === 'color' ? t('color.title') : t('role.choose')" @close="setup.popover.value = null">
            <ColorSwatches v-if="setup.popover.value.kind === 'color'" :colors="palette ?? PALETTE_COLORS" @choose="chooseColor" />
            <template v-else>
              <button v-for="role in roles" :key="role.code" type="button" class="fa-menu-item" @click="chooseRole(role.code)">{{ role.short }} – {{ label(role.label, locale) }}</button>
            </template>
          </CanvasPopover>
        </div>
        <StatusBar :scale="editor.state.scale" :count="validation.count.value" :profile="profile ? profileReference(profile) : undefined" :message="t(ui.message)" @issues="(ui.side = 'issues'), (ui.rightOpen = true)" />
      </main>
      <EditorSidePanel
        v-if="ui.rightOpen"
        v-model:view="ui.side"
        :comments="comments"
        :author="author"
        :compare-sources="compareSources"
        :palette="palette"
        @update:comments="emit('update:comments', $event)"
        @jump="editor.select"
      />
    </div>
    <EditorDialogs :setup="setup" :actions="actions" :name="name" :diagram-id="diagramId" :profiles="profiles" :approvals="approvals" :ports="ports" @apply-xml="emit('update:xml', $event)" />
  </div>
</template>
