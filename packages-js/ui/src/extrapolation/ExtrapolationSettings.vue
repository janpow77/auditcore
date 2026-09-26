<script setup lang="ts">
import { computed } from 'vue'
import {
  confidenceChoices,
  extrapolationConfidenceLabel,
  extrapolationIssueText,
  extrapolationMessages,
  extrapolationMethodGroups,
  type ExtrapolationController,
  type ExtrapolationData,
  type ExtrapolationMethod,
} from '@auditcore/ui-core'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{
  controller: ExtrapolationController
  state: ExtrapolationData
  method: ExtrapolationMethod | null
  locale?: Locale
}>(), { locale: undefined })
const { t, locale: active } = useI18n(extrapolationMessages, () => props.locale)
const id = useId('fa-extrapolation-settings')
const catalogue = computed(() => props.state.catalogue)
const groups = computed(() => (catalogue.value ? extrapolationMethodGroups(catalogue.value, t) : []))
const levels = computed(() => (catalogue.value ? confidenceChoices(catalogue.value, props.method) : []))
const issue = (key: string): string => extrapolationIssueText(props.state.issues, key, t)
const value = (event: Event): string => (event.target as HTMLInputElement | HTMLSelectElement).value
const level = (text: string): number | null => (text === '' ? null : Number(text))
</script>

<template>
  <section class="fa-extrapolation__card" :aria-labelledby="`${id}-title`">
    <h3 :id="`${id}-title`" class="fa-extrapolation__heading">{{ t('settings') }}</h3>
    <div class="fa-extrapolation__settings">
      <label class="fa-extrapolation__field">
        <span class="fa-extrapolation__label">{{ t('method') }}</span>
        <select class="fa-extrapolation__select" :value="state.form.methodId" data-testid="extrapolation-method" @change="controller.selectMethod(value($event))">
          <option value="">{{ t('choose') }}</option>
          <optgroup v-for="group in groups" :key="group.label" :label="group.label">
            <option v-for="entry in group.methods" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
          </optgroup>
        </select>
      </label>
      <template v-if="method?.statistical">
        <label class="fa-extrapolation__field">
          <span class="fa-extrapolation__label">{{ t('confidence') }}</span>
          <select class="fa-extrapolation__select" :value="state.form.confidence === null ? '' : String(state.form.confidence)" data-testid="extrapolation-confidence" @change="controller.setConfidence(level(value($event)))">
            <option value="">{{ t('choose') }}</option>
            <option v-for="entry in levels" :key="entry" :value="String(entry)">{{ extrapolationConfidenceLabel(entry, active) }}</option>
          </select>
        </label>
        <label class="fa-extrapolation__field">
          <span class="fa-extrapolation__label">{{ t('factorProfile') }}</span>
          <select class="fa-extrapolation__select" :value="state.form.profileId ?? ''" data-testid="extrapolation-profile" @change="controller.setProfile(value($event) || null)">
            <option value="">{{ t('choose') }}</option>
            <option v-for="entry in catalogue?.factor_profiles ?? []" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
          </select>
        </label>
      </template>
      <label v-if="method?.needs_sample_size" class="fa-extrapolation__field">
        <span class="fa-extrapolation__label">{{ t('sampleSize') }}</span>
        <input class="fa-extrapolation__input fa-extrapolation__input--number" inputmode="numeric" :value="state.form.sampleSize" :aria-invalid="issue('sampleSize') ? 'true' : undefined" data-testid="extrapolation-sample-size" @input="controller.setSampleSize(value($event))" />
        <span v-if="issue('sampleSize')" class="fa-extrapolation__error">{{ issue('sampleSize') }}</span>
        <span class="fa-extrapolation__hint">{{ t('sampleSizeHint') }}</span>
      </label>
      <label class="fa-extrapolation__field">
        <span class="fa-extrapolation__label">{{ t('materiality') }} (%)</span>
        <input class="fa-extrapolation__input fa-extrapolation__input--number" inputmode="decimal" :value="state.form.materiality" :aria-invalid="issue('materiality') ? 'true' : undefined" data-testid="extrapolation-materiality" @input="controller.setMateriality(value($event))" />
        <span v-if="issue('materiality')" class="fa-extrapolation__error">{{ issue('materiality') }}</span>
        <span class="fa-extrapolation__hint">{{ t('materialityHint') }}</span>
      </label>
    </div>
    <details v-if="method" class="fa-extrapolation__source">
      <summary>{{ t('methodSource') }}</summary>
      <p>{{ method.source }}</p>
      <code>{{ method.formula }}</code>
    </details>
  </section>
</template>
