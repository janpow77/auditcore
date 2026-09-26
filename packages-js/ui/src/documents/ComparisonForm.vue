<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  ACCEPTED_EXTENSIONS,
  COMPARISON_KINDS,
  comparisonsMessages,
  type CompareForm,
  type ComparisonsMessageKey,
  type ComparisonsView,
  type RowStatus,
  type UploadFile,
} from '@flowaudit/ui-core'
import FaButton from '../base/FaButton.vue'
import FaTextField from '../base/FaTextField.vue'
import { useId } from '../composables/useId'
import { useI18n } from '../i18n'
import ComparisonOptions from './ComparisonOptions.vue'

const props = withDefaults(defineProps<{
  form: CompareForm
  view: ComparisonsView
  busy?: boolean
}>(), { busy: false })

const emit = defineEmits<{
  'form-update': [patch: Partial<CompareForm>]
  'section-toggle': [status: RowStatus, enabled: boolean]
  'form-submit': []
  'form-reset': []
}>()

const { t } = useI18n(comparisonsMessages)
const id = useId('fa-comparisons-form')
const accept = ACCEPTED_EXTENSIONS.join(',')
const errorOf = (field: string): string => props.view.problems.filter((problem) => problem.field === field).map((problem) => problem.text).join(' ')
const files = computed(() => [
  { side: 'oldFile' as const, label: props.view.oldFileLabel, chosen: props.view.oldFileText, error: errorOf('oldFile') },
  { side: 'newFile' as const, label: props.view.newFileLabel, chosen: props.view.newFileText, error: errorOf('newFile') },
])

const root = ref<HTMLFormElement | null>(null)
// Nach Anlegen oder Zurücksetzen auch die Dateiauswahl der Eingabefelder leeren.
watch(() => [props.form.oldFile, props.form.newFile] as const, (chosen) => {
  chosen.forEach((file, index) => {
    const input = root.value?.querySelector<HTMLInputElement>(`[data-testid="comparisons-${index === 0 ? 'oldFile' : 'newFile'}"]`)
    if (!file && input) input.value = ''
  })
})

function onFile(side: 'oldFile' | 'newFile', event: Event): void {
  const chosen: UploadFile | null = (event.target as HTMLInputElement).files?.[0] ?? null
  emit('form-update', { [side]: chosen })
}
</script>

<template>
  <form ref="root" class="fa-comparisons-form" :aria-labelledby="`${id}-heading`" novalidate @submit.prevent="emit('form-submit')">
    <h3 :id="`${id}-heading`" class="fa-comparisons__subheading">{{ t('formHeading') }}</h3>
    <fieldset class="fa-comparisons-form__group fa-comparisons-form__group--kind">
      <legend>{{ t('typeLabel') }}</legend>
      <label v-for="kind in COMPARISON_KINDS" :key="kind">
        <input type="radio" :name="`${id}-kind`" :value="kind" :checked="form.kind === kind" @change="emit('form-update', { kind })" /> {{ t(`kind_${kind}` as ComparisonsMessageKey) }}
      </label>
    </fieldset>
    <div class="fa-comparisons-form__row">
      <div v-for="entry in files" :key="entry.side" class="fa-comparisons-form__field fa-comparisons-form__file" :class="{ 'fa-comparisons-form__field--error': entry.error }">
        <label :for="`${id}-${entry.side}`">{{ entry.label }}</label>
        <input
          :id="`${id}-${entry.side}`" type="file" :accept="accept" :data-testid="`comparisons-${entry.side}`"
          :aria-invalid="entry.error ? 'true' : undefined" :aria-describedby="`${id}-${entry.side}-note`" @change="onFile(entry.side, $event)"
        />
        <p :id="`${id}-${entry.side}-note`" :class="entry.error ? 'fa-comparisons-form__error' : 'fa-comparisons-form__hint'">{{ entry.error || entry.chosen || view.sizeHint }}</p>
      </div>
    </div>
    <p v-if="view.pdfHint" class="fa-comparisons-form__hint">{{ t('pdfHint') }}</p>
    <FaTextField :model-value="form.title" :label="t('titleLabel')" :placeholder="t('titlePlaceholder')" :error="errorOf('title')" @update:model-value="emit('form-update', { title: $event })" />
    <ComparisonOptions
      :form="form" :profile-options="view.profileOptions" :threshold-error="errorOf('threshold')" :sections-error="errorOf('sections')"
      @form-update="emit('form-update', $event)" @section-toggle="(status, enabled) => emit('section-toggle', status, enabled)"
    />
    <div v-if="view.problems.length" class="fa-comparisons-form__problems" role="alert">
      <p>{{ t('problemsHeading') }}</p>
      <ul><li v-for="problem in view.problems" :key="problem.text">{{ problem.text }}</li></ul>
    </div>
    <div class="fa-comparisons-form__actions">
      <FaButton type="submit" variant="primary" icon="check" :loading="busy">{{ t('submit') }}</FaButton>
      <FaButton variant="ghost" :disabled="busy" @click="emit('form-reset')">{{ t('reset') }}</FaButton>
    </div>
  </form>
</template>
