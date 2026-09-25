<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import type { BadgeTone } from '../base/types'
import { useId } from '../composables/useId'
import SynopsisText from './SynopsisText.vue'
import type { RowUpdate, SynopsisLayout } from './types'
import type { RowView, SynopsisTranslate } from './viewModel'

const props = defineProps<{
  row: RowView
  layout: SynopsisLayout
  oldLabel: string
  newLabel: string
  reasonLabel: string
  editable: boolean
  active: boolean
  t: SynopsisTranslate
}>()

const emit = defineEmits<{ update: [patch: Omit<RowUpdate, 'row_id'>]; activate: [] }>()
const id = useId('fa-synopsis-row')

const TONES: Record<string, BadgeTone> = { changed: 'accent', added: 'success', removed: 'danger', moved: 'warning' }
const tone = computed<BadgeTone>(() => TONES[props.row.status] ?? 'neutral')
const sr = computed(() => ({ srRemoved: props.t('srRemoved'), srAdded: props.t('srAdded'), srEnd: props.t('srEnd') }))
const showReason = computed(() => props.editable || !!props.row.reason)

function onSelected(event: Event): void {
  emit('update', { selected: (event.target as HTMLInputElement).checked })
}

function onReason(event: Event): void {
  emit('update', { reason: (event.target as HTMLTextAreaElement).value })
}
</script>

<template>
  <article
    class="fa-synopsis-row"
    :class="[`fa-synopsis-row--${row.status}`, { 'fa-synopsis-row--active': active, 'fa-synopsis-row--muted': !row.selected }]"
    :data-row-id="row.id"
    :aria-labelledby="`${id}-title`"
    :aria-current="active ? 'true' : undefined"
    tabindex="-1"
    @focusin="emit('activate')"
  >
    <header class="fa-synopsis-row__head">
      <FaBadge :tone="tone">{{ row.statusLabel }}</FaBadge>
      <h3 :id="`${id}-title`" class="fa-synopsis-row__title">
        {{ row.location || '—' }}<span class="fa-sr-only">, {{ row.statusLabel }}</span>
      </h3>
      <label v-if="editable" class="fa-synopsis-row__include">
        <input type="checkbox" :checked="row.selected" @change="onSelected" />
        {{ t('include') }}
      </label>
    </header>

    <div v-if="layout === 'side-by-side'" class="fa-synopsis-row__sides">
      <section v-for="side in (['old', 'new'] as const)" :key="side" class="fa-synopsis-row__side" :aria-label="side === 'old' ? oldLabel : newLabel">
        <h4 class="fa-synopsis-row__side-title">{{ side === 'old' ? oldLabel : newLabel }}</h4>
        <SynopsisText :segments="row[side]" :empty="side === 'old' ? t('emptyOld') : t('emptyNew')" v-bind="sr" />
        <div v-for="field in row.fields.filter((entry) => entry[side].length > 0)" :key="field.field" class="fa-synopsis-row__field">
          <strong>{{ field.label }}</strong>
          <SynopsisText :segments="field[side]" v-bind="sr" />
        </div>
      </section>
    </div>
    <div v-else class="fa-synopsis-row__inline">
      <SynopsisText :segments="row.inline" v-bind="sr" />
      <div v-for="field in row.fields" :key="field.field" class="fa-synopsis-row__field">
        <strong>{{ field.label }}</strong>
        <SynopsisText :segments="field.inline" v-bind="sr" />
      </div>
    </div>

    <footer v-if="showReason" class="fa-synopsis-row__reason">
      <label v-if="editable" class="fa-synopsis-row__reason-edit">
        <span>{{ reasonLabel }}</span>
        <textarea :value="row.reason" rows="2" maxlength="4000" :placeholder="t('reasonPlaceholder')" @change="onReason"></textarea>
      </label>
      <p v-else><strong>{{ reasonLabel }}:</strong> {{ row.reason }}</p>
      <p v-if="row.reasonSource === 'flowagent'" class="fa-synopsis-row__hint" :class="{ 'fa-synopsis-row__hint--ok': row.reasonVerified }">
        {{ t('flowagent') }} · {{ row.reasonVerified ? t('flowagentVerified') : t('flowagentCheck') }}
      </p>
      <p v-if="row.reasonWarning" class="fa-synopsis-row__hint">{{ row.reasonWarning }}</p>
    </footer>
  </article>
</template>

<style>
.fa-synopsis-row { border: 1px solid var(--fa-color-border); border-left: 4px solid var(--fa-color-border-strong); border-radius: var(--fa-radius); background: var(--fa-color-surface); scroll-margin: var(--fa-space-6); }
.fa-synopsis-row:focus-visible, .fa-synopsis-row--active { outline: none; box-shadow: var(--fa-focus-ring); }
.fa-synopsis-row--changed { border-left-color: var(--fa-color-accent); }
.fa-synopsis-row--added { border-left-color: var(--fa-color-success); }
.fa-synopsis-row--removed { border-left-color: var(--fa-color-danger); }
.fa-synopsis-row--moved { border-left-color: var(--fa-color-warning); }
.fa-synopsis-row--muted { opacity: 0.6; }
.fa-synopsis-row__head { display: flex; flex-wrap: wrap; align-items: center; gap: var(--fa-space-3); padding: var(--fa-space-2) var(--fa-space-4); border-bottom: 1px solid var(--fa-color-border); background: var(--fa-color-surface-raised); border-radius: var(--fa-radius) var(--fa-radius) 0 0; }
.fa-synopsis-row__title { flex: 1; margin: 0; font-size: var(--fa-font-size-sm); font-weight: 600; }
.fa-synopsis-row__include { display: inline-flex; align-items: center; gap: var(--fa-space-2); font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-synopsis-row__sides { display: grid; grid-template-columns: 1fr 1fr; }
.fa-synopsis-row__side, .fa-synopsis-row__inline { padding: var(--fa-space-3) var(--fa-space-4); min-width: 0; }
.fa-synopsis-row__side + .fa-synopsis-row__side { border-left: 1px solid var(--fa-color-border); }
.fa-synopsis-row__side-title { margin: 0 0 var(--fa-space-2); font-size: var(--fa-font-size-xs); font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: var(--fa-color-text-muted); }
.fa-synopsis-row__field { margin-top: var(--fa-space-3); font-size: var(--fa-font-size-sm); }
.fa-synopsis-row__field strong { display: block; font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-synopsis-row__reason { padding: var(--fa-space-2) var(--fa-space-4) var(--fa-space-3); border-top: 1px dashed var(--fa-color-border); font-size: var(--fa-font-size-sm); }
.fa-synopsis-row__reason p { margin: 0; white-space: pre-wrap; }
.fa-synopsis-row__reason-edit { display: flex; flex-direction: column; gap: var(--fa-space-1); font-size: var(--fa-font-size-xs); font-weight: 600; color: var(--fa-color-text-muted); }
.fa-synopsis-row__reason-edit textarea { font: var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans); color: var(--fa-color-text); background: var(--fa-color-surface); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius-sm); padding: var(--fa-space-2); resize: vertical; }
.fa-synopsis-row__reason-edit textarea:focus-visible, .fa-synopsis-row__include input:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); }
.fa-synopsis-row__hint { margin-top: var(--fa-space-1) !important; font-size: var(--fa-font-size-xs); color: var(--fa-color-warning); }
.fa-synopsis-row__hint--ok { color: var(--fa-color-success); }
@media (max-width: 720px) {
  .fa-synopsis-row__sides { grid-template-columns: 1fr; }
  .fa-synopsis-row__side + .fa-synopsis-row__side { border-left: 0; border-top: 1px solid var(--fa-color-border); }
}
</style>
