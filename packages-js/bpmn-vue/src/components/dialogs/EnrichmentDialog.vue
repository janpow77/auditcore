<script setup lang="ts">
/**
 * Import enrichment: suggestions from documentation, labels and colours,
 * grouped by element; each can be accepted or rejected.
 */
import { computed, ref, watch } from 'vue'
import { citation, shortCitation, type LegalBasis, type Suggestion } from '@flowaudit/bpmn-flowaudit'
import BaseDialog from '../base/BaseDialog.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ open: boolean; suggestions: Suggestion[]; names: Record<string, string> }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'apply', accepted: Suggestion[], removePrefixes: boolean): void }>()
const { t } = useI18n()
const accepted = ref(new Set<string>())
const removePrefixes = ref(true)

watch(
  () => props.open,
  (open) => {
    if (open) accepted.value = new Set(props.suggestions.map((s) => s.id))
  },
  { immediate: true },
)

const groups = computed(() => {
  const map = new Map<string, Suggestion[]>()
  for (const item of props.suggestions) map.set(item.elementId, [...(map.get(item.elementId) ?? []), item])
  return [...map.entries()]
})

function describe(item: Suggestion): string {
  const value = item.value
  if (typeof value === 'string') return value
  if (item.kind === 'legalBasis') return `${shortCitation(value as LegalBasis)} – ${citation(value as LegalBasis)}`
  return Object.values(value).filter(Boolean).join(' · ')
}

function toggle(id: string): void {
  const next = new Set(accepted.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  accepted.value = next
}

function apply(): void {
  emit('apply', props.suggestions.filter((s) => accepted.value.has(s.id)), removePrefixes.value)
  emit('update:open', false)
}
</script>

<template>
  <BaseDialog :open="open" :title="t('enrich.title')" :subtitle="t('enrich.subtitle')" width="820px" @update:open="emit('update:open', $event)">
    <p v-if="!suggestions.length" class="fa-help">{{ t('enrich.none') }}</p>
    <div v-else class="fa-enrich__bar">
      <button type="button" class="fa-btn fa-btn--ghost" @click="accepted = new Set(suggestions.map((s) => s.id))">{{ t('enrich.selectAll') }}</button>
      <button type="button" class="fa-btn fa-btn--ghost" @click="accepted = new Set()">{{ t('enrich.selectNone') }}</button>
      <label class="fa-check"><input v-model="removePrefixes" type="checkbox" />{{ t('enrich.removePrefixes') }}</label>
    </div>
    <section v-for="[elementId, items] in groups" :key="elementId" class="fa-enrich__group">
      <h3 class="fa-section__title">{{ names[elementId] || elementId }}</h3>
      <ul class="fa-enrich__list">
        <li v-for="item in items" :key="item.id">
          <label class="fa-enrich__item">
            <input type="checkbox" :checked="accepted.has(item.id)" @change="toggle(item.id)" />
            <span class="fa-badge fa-badge--info">{{ t(`enrich.kind.${item.kind}`) }}</span>
            <span class="fa-enrich__value">{{ describe(item) }}</span>
            <span class="fa-help">{{ t(`enrich.origin.${item.origin}`) }}: „{{ item.excerpt }}“</span>
          </label>
        </li>
      </ul>
    </section>
    <template #footer>
      <button type="button" class="fa-btn" @click="emit('update:open', false)">{{ t('common.cancel') }}</button>
      <button type="button" class="fa-btn fa-btn--primary" :disabled="!accepted.size" @click="apply">{{ t('enrich.apply', { count: accepted.size }) }}</button>
    </template>
  </BaseDialog>
</template>

<style>
.fa-enrich__bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.fa-enrich__group + .fa-enrich__group {
  margin-top: 12px;
}

.fa-enrich__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.fa-enrich__item {
  display: grid;
  grid-template-columns: auto auto 1fr;
  gap: 4px 8px;
  align-items: center;
  padding: 6px 4px;
  border-bottom: 1px solid var(--fa-border);
}

.fa-enrich__item .fa-help {
  grid-column: 2 / -1;
}

.fa-enrich__value {
  overflow-wrap: anywhere;
}
</style>
