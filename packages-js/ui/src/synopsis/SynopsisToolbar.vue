<script setup lang="ts">
import { computed } from 'vue'
import FaButton from '../base/FaButton.vue'
import FaTextField from '../base/FaTextField.vue'
import { useId } from '../composables/useId'
import { CHANGE_STATUSES, ROW_STATUSES, type ClientExportFormat, type SynopsisLayout } from './types'
import { statusLabel, type SynopsisTranslate } from './viewModel'

export interface ServerExportLink {
  label: string
  href: string
}

const props = defineProps<{
  layout: SynopsisLayout
  statuses: readonly string[]
  query: string
  onlySelected: boolean
  highlight: boolean
  editable: boolean
  position: string
  canPrev: boolean
  canNext: boolean
  serverExports: readonly ServerExportLink[]
  t: SynopsisTranslate
}>()

const emit = defineEmits<{
  'update:layout': [layout: SynopsisLayout]
  'update:query': [query: string]
  'update:onlySelected': [value: boolean]
  'update:highlight': [value: boolean]
  'toggle-status': [status: string, enabled: boolean]
  'all-changes': []
  navigate: [direction: 1 | -1]
  export: [format: ClientExportFormat]
}>()

const id = useId('fa-synopsis-toolbar')
const allChanges = computed(
  () => props.statuses.length === CHANGE_STATUSES.length && CHANGE_STATUSES.every((status) => props.statuses.includes(status)),
)
const query = computed({ get: () => props.query, set: (value: string) => emit('update:query', value) })
const exports: ReadonlyArray<[ClientExportFormat, 'exportHtml' | 'exportMarkdown' | 'exportPrint']> = [
  ['html', 'exportHtml'],
  ['markdown', 'exportMarkdown'],
  ['print', 'exportPrint'],
]

function checked(event: Event): boolean {
  return (event.target as HTMLInputElement).checked
}
</script>

<template>
  <div class="fa-synopsis-toolbar" role="region" :aria-label="t('toolbar')">
    <div class="fa-synopsis-toolbar__row">
      <div class="fa-synopsis-toolbar__group" role="group" :aria-label="t('layout')">
        <FaButton size="sm" variant="ghost" :pressed="layout === 'side-by-side'" @click="emit('update:layout', 'side-by-side')">{{ t('layoutSideBySide') }}</FaButton>
        <FaButton size="sm" variant="ghost" :pressed="layout === 'inline'" @click="emit('update:layout', 'inline')">{{ t('layoutInline') }}</FaButton>
      </div>
      <div class="fa-synopsis-toolbar__search">
        <FaTextField v-model="query" type="search" :label="t('search')" hide-label :placeholder="t('search')" />
      </div>
      <div class="fa-synopsis-toolbar__nav" role="group" :aria-label="t('keyboardHint')">
        <FaButton size="sm" icon="chevron-up" :disabled="!canPrev" :aria-keyshortcuts="'P K'" @click="emit('navigate', -1)">{{ t('prevChange') }}</FaButton>
        <FaButton size="sm" icon="chevron-down" :disabled="!canNext" :aria-keyshortcuts="'N J'" @click="emit('navigate', 1)">{{ t('nextChange') }}</FaButton>
        <span class="fa-synopsis-toolbar__position" role="status" aria-live="polite">{{ position }}</span>
      </div>
    </div>
    <div class="fa-synopsis-toolbar__row">
      <fieldset class="fa-synopsis-toolbar__filters">
        <legend>{{ t('filterLegend') }}</legend>
        <label><input type="checkbox" :checked="allChanges" @change="checked($event) && emit('all-changes')" /> {{ t('filterAll') }}</label>
        <label v-for="status in ROW_STATUSES" :key="status">
          <input type="checkbox" :checked="statuses.includes(status)" @change="emit('toggle-status', status, checked($event))" />
          {{ statusLabel(status, t) }}
        </label>
      </fieldset>
      <div class="fa-synopsis-toolbar__options">
        <label><input type="checkbox" :checked="highlight" @change="emit('update:highlight', checked($event))" /> {{ t('highlight') }}</label>
        <label v-if="editable"><input type="checkbox" :checked="onlySelected" @change="emit('update:onlySelected', checked($event))" /> {{ t('onlySelected') }}</label>
      </div>
      <div class="fa-synopsis-toolbar__export" role="group" :aria-labelledby="`${id}-export`">
        <span :id="`${id}-export`" class="fa-synopsis-toolbar__label">{{ t('exportLabel') }}</span>
        <FaButton v-for="[format, key] in exports" :key="format" size="sm" @click="emit('export', format)">{{ t(key) }}</FaButton>
        <a v-for="link in serverExports" :key="link.href" class="fa-button fa-button--secondary fa-button--sm" :href="link.href" download>{{ link.label }}</a>
      </div>
    </div>
  </div>
</template>

<style>
.fa-synopsis-toolbar { display: flex; flex-direction: column; gap: var(--fa-space-3); padding: var(--fa-space-3) var(--fa-space-4); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); background: var(--fa-color-surface-raised); font: var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans); }
.fa-synopsis-toolbar__row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--fa-space-3) var(--fa-space-5); }
.fa-synopsis-toolbar__group, .fa-synopsis-toolbar__nav, .fa-synopsis-toolbar__export { display: inline-flex; flex-wrap: wrap; align-items: center; gap: var(--fa-space-2); }
.fa-synopsis-toolbar__search { flex: 1 1 14rem; min-width: 12rem; }
.fa-synopsis-toolbar__position { display: inline-block; width: 16rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--fa-color-text-muted); font-variant-numeric: tabular-nums; }
.fa-synopsis-toolbar__filters { display: flex; flex-wrap: wrap; gap: var(--fa-space-2) var(--fa-space-4); margin: 0; padding: 0; border: 0; }
.fa-synopsis-toolbar__filters legend { float: left; margin-right: var(--fa-space-3); font-weight: 600; color: var(--fa-color-text-muted); }
.fa-synopsis-toolbar label { display: inline-flex; align-items: center; gap: var(--fa-space-1); cursor: pointer; }
.fa-synopsis-toolbar input[type='checkbox'] { accent-color: var(--fa-color-accent); width: 1rem; height: 1rem; }
.fa-synopsis-toolbar input[type='checkbox']:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); }
.fa-synopsis-toolbar__options { display: inline-flex; flex-wrap: wrap; gap: var(--fa-space-4); }
.fa-synopsis-toolbar__label { font-weight: 600; color: var(--fa-color-text-muted); }
.fa-synopsis-toolbar__export a { text-decoration: none; }
.fa-synopsis-toolbar__export a:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); }
</style>
