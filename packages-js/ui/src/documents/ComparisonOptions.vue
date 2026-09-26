<script setup lang="ts">
import { computed } from 'vue'
import {
  COMPARISON_MODES,
  comparisonsMessages,
  MAX_THRESHOLD,
  MIN_THRESHOLD,
  ROW_STATUSES,
  type CompareForm,
  type ComparisonsMessageKey,
  type ProfileOption,
  type RowStatus,
} from '@auditcore/ui-core'
import { useId } from '../composables/useId'
import { useI18n } from '../i18n'

const props = withDefaults(defineProps<{
  form: CompareForm
  profileOptions?: ProfileOption[]
  thresholdError?: string
  sectionsError?: string
}>(), { profileOptions: () => [], thresholdError: '', sectionsError: '' })

const emit = defineEmits<{ 'form-update': [patch: Partial<CompareForm>]; 'section-toggle': [status: RowStatus, enabled: boolean] }>()
const { t } = useI18n(comparisonsMessages)
const id = useId('fa-comparisons-options')
const standard = computed(() => props.form.kind === 'standard')
const FLAGS = ['includeAnswers', 'includeNotes', 'includeEditorial'] as const

function checked(event: Event): boolean {
  return (event.target as HTMLInputElement).checked
}

function onThreshold(event: Event): void {
  const value = (event.target as HTMLInputElement).valueAsNumber
  emit('form-update', { threshold: Number.isNaN(value) ? 0 : value })
}
</script>

<template>
  <div class="fa-comparisons-form__options">
    <div v-if="standard" class="fa-comparisons-form__row">
      <div class="fa-comparisons-form__field">
        <label :for="`${id}-mode`">{{ t('modeLabel') }}</label>
        <select :id="`${id}-mode`" :value="form.mode" @change="emit('form-update', { mode: ($event.target as HTMLSelectElement).value as CompareForm['mode'] })">
          <option v-for="mode in COMPARISON_MODES" :key="mode" :value="mode">{{ t(`mode_${mode}` as ComparisonsMessageKey) }}</option>
        </select>
      </div>
      <div class="fa-comparisons-form__field" :class="{ 'fa-comparisons-form__field--error': thresholdError }">
        <label :for="`${id}-threshold`">{{ t('thresholdLabel') }}</label>
        <input
          :id="`${id}-threshold`" type="number" :min="MIN_THRESHOLD" :max="MAX_THRESHOLD" step="1" :value="form.threshold"
          :aria-invalid="thresholdError ? 'true' : undefined" :aria-describedby="thresholdError ? `${id}-threshold-error` : undefined" @input="onThreshold"
        />
        <p v-if="thresholdError" :id="`${id}-threshold-error`" class="fa-comparisons-form__error">{{ thresholdError }}</p>
      </div>
    </div>
    <fieldset class="fa-comparisons-form__group">
      <legend>{{ t('optionsLegend') }}</legend>
      <template v-if="standard">
        <label v-for="flag in FLAGS" :key="flag"><input type="checkbox" :checked="form[flag]" @change="emit('form-update', { [flag]: checked($event) })" /> {{ t(flag) }}</label>
      </template>
      <label><input type="checkbox" :checked="form.highlightWords" @change="emit('form-update', { highlightWords: checked($event) })" /> {{ t('highlightWords') }}</label>
    </fieldset>
    <fieldset class="fa-comparisons-form__group" :aria-invalid="sectionsError ? 'true' : undefined" :aria-describedby="sectionsError ? `${id}-sections-error` : undefined">
      <legend>{{ t('sectionsLegend') }}</legend>
      <label v-for="status in ROW_STATUSES" :key="status">
        <input type="checkbox" :checked="form.sections.includes(status)" @change="emit('section-toggle', status, checked($event))" /> {{ t(`section_${status}` as ComparisonsMessageKey) }}
      </label>
      <p v-if="sectionsError" :id="`${id}-sections-error`" class="fa-comparisons-form__error">{{ sectionsError }}</p>
    </fieldset>
    <div v-if="profileOptions.length > 1" class="fa-comparisons-form__field">
      <label :for="`${id}-profile`">{{ t('profileLabel') }}</label>
      <select :id="`${id}-profile`" :value="form.profile" @change="emit('form-update', { profile: ($event.target as HTMLSelectElement).value })">
        <option v-for="option in profileOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
      </select>
    </div>
  </div>
</template>
