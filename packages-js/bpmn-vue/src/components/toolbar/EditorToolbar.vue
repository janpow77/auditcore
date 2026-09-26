<script setup lang="ts">
/**
 * Toolbar in one row with groups File · Edit · View · Check · Modes (legacy
 * `BpmnToolbar`): name, unsaved/readonly state, save, colour menu, flow
 * direction, page view and panel toggles. Actions are emitted as `action`.
 */
import { PALETTE_COLORS, type PaletteColor } from '@auditcore/bpmn-flowaudit'
import { actionDisabled, CHECK_ACTIONS, EDIT_ACTIONS, FILE_ACTIONS, MODE_ACTIONS, PAGE_OPTIONS as pageOptions, VIEW_ACTIONS, type ToolbarAction } from '@auditcore/bpmn-flowaudit/ui'
import ColorSwatches from '../base/ColorSwatches.vue'
import FaIcon from '../base/FaIcon.vue'
import ToolbarMenu from '../base/ToolbarMenu.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{
  name: string
  dirty: boolean
  saving: boolean
  readonly: boolean
  canUndo: boolean
  canRedo: boolean
  direction: 'waagerecht' | 'senkrecht'
  pageView: string
  active: Partial<Record<ToolbarAction, boolean>>
  hidden?: ToolbarAction[]
  palette?: readonly PaletteColor[]
}>()
const emit = defineEmits<{
  (e: 'action', action: ToolbarAction): void
  (e: 'update:name', value: string): void
  (e: 'color', color: PaletteColor | null): void
  (e: 'direction', value: 'waagerecht' | 'senkrecht'): void
  (e: 'page-view', value: string): void
  (e: 'import-file', file: File): void
}>()
const { t } = useI18n()


const visible = (id: ToolbarAction) => !props.hidden?.includes(id)
const disabled = (id: ToolbarAction, writes?: boolean) => actionDisabled(id, writes, props)

function onFile(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emit('import-file', file)
  input.value = ''
}
</script>

<template>
  <div class="fa-toolbar" role="toolbar" :aria-label="t('toolbar.label')">
    <button type="button" class="fa-icon-btn" :aria-pressed="active['left-panel']" :aria-label="t('toolbar.leftPanel')" :title="t('toolbar.leftPanel')" @click="emit('action', 'left-panel')">
      <FaIcon name="panel-left" />
    </button>
    <input class="fa-input fa-toolbar__name" :value="name" :aria-label="t('props.name')" :readonly="readonly" @change="emit('update:name', ($event.target as HTMLInputElement).value)" />
    <span v-if="dirty" class="fa-badge fa-badge--warning">{{ t('editor.unsaved') }}</span>
    <span v-if="readonly" class="fa-badge fa-badge--info"><FaIcon name="lock" :size="12" />{{ t('editor.readonly') }}</span>
    <button type="button" class="fa-btn fa-btn--primary" :disabled="saving || readonly" @click="emit('action', 'save')">
      <FaIcon name="save" :size="16" />{{ t('toolbar.save') }}
    </button>
    <span class="fa-toolbar__sep" />
    <template v-for="entry in FILE_ACTIONS" :key="entry.id">
      <label v-if="entry.id === 'import' && visible('import')" class="fa-icon-btn" :title="t(entry.label)" :aria-disabled="readonly">
        <FaIcon :name="entry.icon" /><span class="fa-sr-only">{{ t(entry.label) }}</span>
        <input type="file" accept=".bpmn,.xml" class="fa-sr-only" :disabled="readonly" @change="onFile" />
      </label>
      <button v-else-if="visible(entry.id)" type="button" class="fa-icon-btn" :aria-label="t(entry.label)" :title="t(entry.label)" @click="emit('action', entry.id)">
        <FaIcon :name="entry.icon" />
      </button>
    </template>
    <span class="fa-toolbar__sep" />
    <button v-for="entry in EDIT_ACTIONS" :key="entry.id" type="button" class="fa-icon-btn" :disabled="disabled(entry.id, entry.writes)" :aria-label="t(entry.label)" :title="t(entry.label)" @click="emit('action', entry.id)">
      <FaIcon :name="entry.icon" />
    </button>
    <ToolbarMenu v-slot="{ close }" :label="t('toolbar.color')" icon="color">
      <p class="fa-menu-hint">{{ t('toolbar.colorHint') }}</p>
      <ColorSwatches :colors="palette ?? PALETTE_COLORS" :disabled="readonly" @choose="(color) => (emit('color', color), close())" />
    </ToolbarMenu>
    <div class="fa-segmented" role="group" :aria-label="t('toolbar.direction')">
      <button type="button" class="fa-icon-btn" :aria-pressed="direction === 'waagerecht'" :title="t('toolbar.horizontal')" :aria-label="t('toolbar.horizontal')" :disabled="readonly" @click="emit('direction', 'waagerecht')"><FaIcon name="horizontal" /></button>
      <button type="button" class="fa-icon-btn" :aria-pressed="direction === 'senkrecht'" :title="t('toolbar.vertical')" :aria-label="t('toolbar.vertical')" :disabled="readonly" @click="emit('direction', 'senkrecht')"><FaIcon name="vertical" /></button>
    </div>
    <span class="fa-toolbar__sep" />
    <button v-for="entry in VIEW_ACTIONS" :key="entry.id" type="button" class="fa-icon-btn" :aria-label="t(entry.label)" :title="t(entry.label)" @click="emit('action', entry.id)">
      <FaIcon :name="entry.icon" />
    </button>
    <select class="fa-select fa-toolbar__page" :value="pageView" :aria-label="t('toolbar.pageView')" @change="emit('page-view', ($event.target as HTMLSelectElement).value)">
      <option value="aus">{{ t('toolbar.pageOff') }}</option>
      <option v-for="option in pageOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
    </select>
    <span class="fa-toolbar__sep" />
    <ToolbarMenu v-slot="{ close }" :label="t('toolbar.check')" icon="validate" show-label>
      <template v-for="entry in CHECK_ACTIONS" :key="entry.id">
        <button v-if="visible(entry.id)" type="button" role="menuitem" class="fa-menu-item" :disabled="disabled(entry.id, entry.writes)" @click="(emit('action', entry.id), close())">
          <FaIcon :name="entry.icon" />
          <span>{{ t(entry.label) }}<span v-if="entry.hint" class="fa-menu-hint">{{ t(entry.hint) }}</span></span>
        </button>
      </template>
    </ToolbarMenu>
    <div class="fa-toolbar__modes">
      <template v-for="entry in MODE_ACTIONS" :key="entry.id">
        <button v-if="visible(entry.id)" type="button" class="fa-icon-btn" :aria-pressed="Boolean(active[entry.id])" :aria-label="t(entry.label)" :title="t(entry.label)" @click="emit('action', entry.id)">
          <FaIcon :name="entry.icon" />
        </button>
      </template>
    </div>
    <span class="fa-toolbar__spacer" />
    <button type="button" class="fa-icon-btn" :aria-label="t('toolbar.theme')" :title="t('toolbar.theme')" @click="emit('action', 'theme')"><FaIcon name="moon" /></button>
    <button type="button" class="fa-icon-btn" :aria-pressed="active['right-panel']" :aria-label="t('toolbar.rightPanel')" :title="t('toolbar.rightPanel')" @click="emit('action', 'right-panel')">
      <FaIcon name="panel-right" />
    </button>
  </div>
</template>
