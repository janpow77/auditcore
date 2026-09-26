<script setup lang="ts">
import { ref } from 'vue'
import type { SummaryView } from '@auditcore/ui-core'
import { comparisonsMessages } from '@auditcore/ui-core'
import FaBadge from '../base/FaBadge.vue'
import FaButton from '../base/FaButton.vue'
import FaTextField from '../base/FaTextField.vue'
import { useId } from '../composables/useId'
import { useI18n } from '../i18n'

withDefaults(defineProps<{
  rows?: SummaryView[]
  query?: string
  countText?: string
  emptyText?: string | null
  busy?: boolean
  /** Löschen und Import anbieten. */
  editable?: boolean
  canImport?: boolean
}>(), { rows: () => [], query: '', countText: '', emptyText: null, busy: false, editable: true, canImport: false })

const emit = defineEmits<{
  'update:query': [query: string]
  'comparison-open': [id: string]
  'comparison-remove': [id: string]
  'result-import': [text: string]
}>()

const { t } = useI18n(comparisonsMessages)
const headingId = useId('fa-comparisons-list')
const picker = ref<HTMLInputElement | null>(null)

async function onImport(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const chosen = input.files?.[0]
  input.value = ''
  if (chosen) emit('result-import', await chosen.text())
}
</script>

<template>
  <section class="fa-comparisons-list" :aria-labelledby="headingId">
    <div class="fa-comparisons-list__head">
      <h3 :id="headingId" class="fa-comparisons__subheading">{{ t('listHeading') }}</h3>
      <template v-if="editable && canImport">
        <FaButton size="sm" icon="paperclip" :disabled="busy" @click="picker?.click()">{{ t('importLabel') }}</FaButton>
        <input ref="picker" class="fa-sr-only" type="file" accept=".json,application/json" tabindex="-1" aria-hidden="true" data-testid="comparisons-import" @change="onImport" />
      </template>
    </div>
    <FaTextField :model-value="query" type="search" :label="t('searchLabel')" @update:model-value="emit('update:query', $event)" />
    <p class="fa-comparisons-list__count">{{ countText }}</p>
    <p v-if="emptyText" class="fa-comparisons__state">{{ emptyText }}</p>
    <ul v-else class="fa-comparisons-list__items">
      <li v-for="row in rows" :key="row.id" class="fa-comparisons-list__item" :data-id="row.id">
        <div class="fa-comparisons-list__main">
          <p class="fa-comparisons-list__title">{{ row.title }}</p>
          <p class="fa-comparisons-list__meta">
            <FaBadge :tone="row.kind === 'article_law' ? 'accent' : 'neutral'">{{ row.kindLabel }}</FaBadge>
            <time :datetime="row.createdIso">{{ row.created }}</time>
          </p>
          <p class="fa-comparisons-list__files">{{ row.files }}</p>
          <p class="fa-comparisons-list__counts">{{ row.counts }}</p>
        </div>
        <div class="fa-comparisons-list__actions">
          <FaButton size="sm" variant="primary" :aria-label="t('openLabel', { title: row.title })" @click="emit('comparison-open', row.id)">{{ t('open') }}</FaButton>
          <FaButton v-if="editable" size="sm" variant="ghost" icon="trash" icon-only :label="t('removeLabel', { title: row.title })" :disabled="busy" @click="emit('comparison-remove', row.id)" />
        </div>
      </li>
    </ul>
  </section>
</template>
