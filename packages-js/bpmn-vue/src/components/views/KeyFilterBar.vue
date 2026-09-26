<script setup lang="ts">
/**
 * Key filter „all elements for key X“ (KA, BK, checklist item, finding
 * reference, register, role, marker). Values come from the diagram's own
 * key index; the application can also set a key through `FlowauditEditor`.
 */
import { computed } from 'vue'
import { KEY_KINDS, type KeyKind } from '@auditcore/bpmn-flowaudit'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ keys: Partial<Record<KeyKind, Record<string, string[]>>>; kind: KeyKind; value: string; hits: number }>()
const emit = defineEmits<{ (e: 'update:kind', value: KeyKind): void; (e: 'update:value', value: string): void; (e: 'clear'): void }>()
const { t } = useI18n()

const values = computed(() => Object.keys(props.keys[props.kind] ?? {}).sort((a, b) => a.localeCompare(b, 'de', { numeric: true })))
</script>

<template>
  <div class="fa-keyfilter" role="search" :aria-label="t('filter.title')">
    <FaIcon name="filter" />
    <label class="fa-keyfilter__field">
      <span class="fa-sr-only">{{ t('filter.kind') }}</span>
      <select class="fa-select" :value="kind" @change="emit('update:kind', ($event.target as HTMLSelectElement).value as KeyKind)">
        <option v-for="option in KEY_KINDS" :key="option" :value="option">{{ t(`filter.kind.${option}`) }}</option>
      </select>
    </label>
    <label class="fa-keyfilter__field">
      <span class="fa-sr-only">{{ t('filter.value') }}</span>
      <input class="fa-input" list="fa-keyfilter-values" :value="value" :placeholder="t('filter.value')" @input="emit('update:value', ($event.target as HTMLInputElement).value)" />
      <datalist id="fa-keyfilter-values">
        <option v-for="option in values" :key="option" :value="option" />
      </datalist>
    </label>
    <span class="fa-badge" :class="hits ? 'fa-badge--info' : ''" role="status">{{ t('filter.hits', { count: hits }) }}</span>
    <button type="button" class="fa-btn fa-btn--ghost" @click="emit('clear')"><FaIcon name="close" :size="16" />{{ t('filter.clear') }}</button>
  </div>
</template>
