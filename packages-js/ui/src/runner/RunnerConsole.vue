<!-- RunnerConsole: Liste mit Auswahl; Logik im Kern (createRunnerController). -->
<script setup lang="ts">
import { computed, watch } from 'vue'
import { createRunnerController, runnerMessages, runnerIsEmpty, runnerRows, type RunnerItem, type RunnerPort } from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createRunnerMemoryPort([...])`. */
  port?: RunnerPort | null
  locale?: Locale
}>(), { port: null, locale: undefined })

const emit = defineEmits<{
  'item-select': [item: RunnerItem]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(runnerMessages, () => props.locale)
const controller = createRunnerController({
  port: () => props.port,
  callbacks: () => ({
    selected: (item) => emit('item-select', item),
    failed: (message) => emit('error', message),
  }),
})
const state = useStore(controller.store)
const rows = computed(() => runnerRows(state.value))
const empty = computed(() => runnerIsEmpty(state.value))

watch(() => props.port, () => void controller.load(), { immediate: true })
</script>

<template>
  <section class="fa-runner" :lang="active" :aria-label="t('title')">
    <p v-if="state.busy === 'load'" class="fa-runner__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-runner__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <p v-if="empty" class="fa-runner__muted">{{ t('empty') }}</p>
    <ul v-if="rows.length" class="fa-runner__list">
      <li v-for="row in rows" :key="row.id">
        <button type="button" :class="['fa-runner__item', row.selected && 'fa-runner__item--selected']" :aria-pressed="row.selected" @click="controller.select(row.id)">{{ row.label }}</button>
      </li>
    </ul>
  </section>
</template>
