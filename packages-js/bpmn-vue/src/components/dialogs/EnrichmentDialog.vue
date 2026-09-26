<script setup lang="ts">
/**
 * Import enrichment: suggestions from documentation, labels and colours,
 * grouped by element; each can be accepted or rejected.
 */
import { computed, ref, watch } from 'vue'
import type { Suggestion } from '@flowaudit/bpmn-flowaudit'
import { describeSuggestion as describe, groupSuggestions, toggleInSet } from '@flowaudit/bpmn-flowaudit/ui'
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

const groups = computed(() => groupSuggestions(props.suggestions))
const toggle = (id: string) => (accepted.value = toggleInSet(accepted.value, id))

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
