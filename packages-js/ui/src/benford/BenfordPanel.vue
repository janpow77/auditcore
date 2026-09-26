<script setup lang="ts">
import { watch } from 'vue'
import {
  analyseErrorKey,
  benfordMessages,
  benfordValuesText,
  needsShortValues,
  type BenfordAnalysis,
  type BenfordPort,
  type BenfordTest,
  type ImportedColumns,
  type ShortValues,
} from '@flowaudit/ui-core'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import TableImport from '../tabular/TableImport.vue'
import BenfordChart from './BenfordChart.vue'
import BenfordDigits from './BenfordDigits.vue'
import BenfordMetrics from './BenfordMetrics.vue'
import { useBenford } from './useBenford'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createBenfordRestPort({ baseUrl: '/api/benford' })`. */
  port?: BenfordPort | null
  /** Zu prüfende Beträge; alternativ Datei-Import in der Komponente. */
  values?: readonly (number | null)[]
  locale?: Locale
}>(), { port: null, values: () => [], locale: undefined })

const emit = defineEmits<{ 'analysis-completed': [result: BenfordAnalysis]; error: [message: string] }>()
const { t, locale: active } = useI18n(benfordMessages, () => props.locale)
const id = useId('fa-benford')
const { controller, state, values, profile } = useBenford(() => props.port, () => props.values, {
  analysed: (result) => emit('analysis-completed', result),
  failed: (message) => emit('error', message),
})

watch(() => props.port, () => void controller.load(), { immediate: true })
watch(() => props.values, () => controller.useValues(null))

function onImport(columns: ImportedColumns): void {
  controller.useValues(columns.values)
}

const selected = (event: Event): string => (event.target as HTMLSelectElement).value
</script>

<template>
  <div class="fa-benford" :lang="active">
    <p v-if="state.busy === 'load'" class="fa-benford__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-benford__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <template v-if="state.catalogue">
      <div class="fa-benford__inputs">
        <section class="fa-benford__card" :aria-labelledby="`${id}-data`">
          <h3 :id="`${id}-data`" class="fa-benford__heading">{{ t('data') }}</h3>
          <p class="fa-benford__muted" data-testid="benford-count">
            {{ benfordValuesText(values.length, t, active) }}
          </p>
          <TableImport mode="values" :locale="locale" @import="onImport" />
        </section>
        <form class="fa-benford__card fa-benford__form" novalidate @submit.prevent="controller.analyse">
          <label class="fa-benford__field">
            <span class="fa-benford__label">{{ t('test') }}</span>
            <select :value="state.test" class="fa-benford__select" data-testid="benford-test" @change="controller.setTest(selected($event) as BenfordTest)">
              <option v-for="entry in state.catalogue.tests" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
            </select>
          </label>
          <fieldset v-if="needsShortValues(state.catalogue, state.test)" class="fa-benford__fieldset">
            <legend class="fa-benford__label">{{ t('shortValues') }}</legend>
            <label v-for="option in state.catalogue.short_values" :key="option.id" class="fa-benford__radio">
              <input type="radio" :checked="state.shortValues === option.id" :name="`${id}-short`" :value="option.id" :data-testid="`benford-short-${option.id}`" @change="controller.setShortValues(option.id as ShortValues)" />
              {{ option.label }}
            </label>
          </fieldset>
          <label class="fa-benford__field">
            <span class="fa-benford__label">{{ t('profile') }}</span>
            <select :value="state.profileId ?? ''" class="fa-benford__select" data-testid="benford-profile" @change="controller.setProfile(selected($event) || null)">
              <option value="">{{ t('choose') }}</option>
              <option v-for="entry in state.catalogue.profiles" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
            </select>
          </label>
          <details v-if="profile" class="fa-benford__source">
            <summary>{{ t('profileSource') }}</summary>
            <p>{{ profile.source }}</p>
            <p>{{ profile.note }}</p>
          </details>
          <p v-if="state.validation" class="fa-benford__error" role="alert">{{ t(analyseErrorKey(state.validation)) }}</p>
          <FaButton variant="primary" type="submit" :loading="state.busy === 'analyse'" data-testid="benford-analyse">{{ t('analyse') }}</FaButton>
        </form>
      </div>
      <section v-if="state.result" class="fa-benford__card" :aria-labelledby="`${id}-result`" aria-live="polite">
        <h3 :id="`${id}-result`" class="fa-benford__heading">{{ state.result.test_label }}</h3>
        <p class="fa-benford__notice">{{ t('notice') }}</p>
        <BenfordMetrics :analysis="state.result" :profile="profile" :locale="locale" />
        <BenfordChart :conformity="state.result.conformity" :test-label="state.result.test_label" :locale="locale" />
        <BenfordDigits :conformity="state.result.conformity" :locale="locale" />
      </section>
    </template>
  </div>
</template>
