<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import type { BadgeTone } from '@auditcore/ui-core'
import { useId } from '../composables/useId'
import SynopsisText from './SynopsisText.vue'
import type { RowUpdate, SynopsisLayout } from '@auditcore/ui-core'
import type { RowView, SynopsisTranslate } from '@auditcore/ui-core'

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
