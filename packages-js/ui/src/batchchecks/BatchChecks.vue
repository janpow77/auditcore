<!-- BatchChecks: Liste mit Auswahl; Logik im Kern (createBatchchecksController). -->
<script setup lang="ts">
import { computed, watch } from 'vue'
import { createBatchchecksController, batchchecksMessages, batchchecksIsEmpty, batchchecksRows, type BatchchecksItem, type BatchchecksPort } from '@auditcore/ui-core'
import { useStore } from '../composables/useStore'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createBatchchecksMemoryPort([...])`. */
  port?: BatchchecksPort | null
  locale?: Locale
}>(), { port: null, locale: undefined })

const emit = defineEmits<{
  'item-select': [item: BatchchecksItem]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(batchchecksMessages, () => props.locale)
const controller = createBatchchecksController({
  port: () => props.port,
  callbacks: () => ({
    selected: (item) => emit('item-select', item),
    failed: (message) => emit('error', message),
  }),
})
const state = useStore(controller.store)
const rows = computed(() => batchchecksRows(state.value))
const empty = computed(() => batchchecksIsEmpty(state.value))

watch(() => props.port, () => void controller.load(), { immediate: true })
</script>

<template>
  <section class="fa-batchchecks" :lang="active" :aria-label="t('title')">
    <p v-if="state.busy === 'load'" class="fa-batchchecks__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-batchchecks__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <p v-if="empty" class="fa-batchchecks__muted">{{ t('empty') }}</p>
    <ul v-if="rows.length" class="fa-batchchecks__list">
      <li v-for="row in rows" :key="row.id">
        <button type="button" :class="['fa-batchchecks__item', row.selected && 'fa-batchchecks__item--selected']" :aria-pressed="row.selected" @click="controller.select(row.id)">{{ row.label }}</button>
      </li>
    </ul>
  </section>
</template>
