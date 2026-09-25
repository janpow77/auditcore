<script setup lang="ts">
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { formatNumber, formatPercent, useI18n, type Locale } from '../i18n'
import { samplingMessages } from './messages'
import { isPercent, type FieldError } from './model'
import type { MethodProfile, ParameterSpec } from './types'

const props = withDefaults(defineProps<{
  profile: MethodProfile
  errors: Readonly<Record<string, FieldError>>
  busy?: boolean
  hasPopulation?: boolean
  locale?: Locale
}>(), { busy: false, hasPopulation: false, locale: undefined })

const texts = defineModel<Record<string, string>>('texts', { required: true })
const confidence = defineModel<number | null>('confidence', { required: true })
const emit = defineEmits<{ calculate: []; suggest: [] }>()
const { t, locale: active } = useI18n(samplingMessages, () => props.locale)
const id = useId('fa-sampling-param')

function unit(spec: ParameterSpec): string {
  if (isPercent(spec)) return '%'
  return spec.unit === 'EUR' ? '€' : ''
}

function rangeText(error: FieldError): string {
  const fmt = (value: number): string => formatNumber(value, active.value, { maximumFractionDigits: 4 })
  if (error.min !== undefined && error.max !== undefined) return t('rangeBetween', { min: fmt(error.min), max: fmt(error.max) })
  if (error.min !== undefined) return t('rangeFrom', { min: fmt(error.min) })
  return t('rangeTo', { max: fmt(error.max ?? 0) })
}

function errorText(key: string): string {
  const error = props.errors[key]
  if (!error) return ''
  if (error.code === 'range') return t('errorRange', { range: rangeText(error) })
  return error.code === 'required' ? t('errorRequired') : t('errorInvalid')
}

function setText(key: string, value: string): void {
  texts.value = { ...texts.value, [key]: value }
}

function onConfidence(event: Event): void {
  const value = (event.target as HTMLSelectElement).value
  confidence.value = value === '' ? null : Number(value)
}
</script>

<template>
  <section class="fa-sampling__card" :aria-labelledby="`${id}-title`">
    <h3 :id="`${id}-title`" class="fa-sampling__heading">{{ t('parameters') }}</h3>
    <form class="fa-sampling__form" novalidate @submit.prevent="emit('calculate')">
      <template v-for="spec in profile.parameters" :key="spec.key">
        <label v-if="spec.type === 'choice'" class="fa-sampling__field" :class="{ 'fa-sampling__field--error': errorText('confidence_level') }">
          <span class="fa-sampling__label">{{ t('confidence') }}</span>
          <select class="fa-sampling__select" data-testid="sampling-confidence" :value="confidence ?? ''" :aria-invalid="errorText('confidence_level') ? 'true' : undefined" @change="onConfidence">
            <option value="">{{ t('choose') }}</option>
            <option v-for="level in profile.confidence_levels" :key="level.level" :value="level.level">
              {{ t('confidenceOption', { level: formatPercent(level.level, active, 0), factor: formatNumber(level.factor, active, { maximumFractionDigits: 3 }) }) }}
            </option>
          </select>
          <span v-if="errorText('confidence_level')" class="fa-sampling__error" role="alert">{{ errorText('confidence_level') }}</span>
        </label>
        <label v-else class="fa-sampling__field" :class="{ 'fa-sampling__field--error': errorText(spec.key) }">
          <span class="fa-sampling__label">{{ spec.label }}</span>
          <span class="fa-sampling__input-wrap">
            <input
              class="fa-sampling__input"
              inputmode="decimal"
              :data-testid="`sampling-${spec.key}`"
              :value="texts[spec.key] ?? ''"
              :aria-invalid="errorText(spec.key) ? 'true' : undefined"
              :aria-describedby="errorText(spec.key) ? `${id}-${spec.key}-error` : undefined"
              @input="setText(spec.key, ($event.target as HTMLInputElement).value)"
            />
            <span class="fa-sampling__unit" aria-hidden="true">{{ unit(spec) }}</span>
          </span>
          <span v-if="errorText(spec.key)" :id="`${id}-${spec.key}-error`" class="fa-sampling__error" role="alert">{{ errorText(spec.key) }}</span>
        </label>
      </template>
      <div class="fa-sampling__actions">
        <FaButton variant="primary" type="submit" :loading="busy" data-testid="sampling-calculate">{{ t('calculate') }}</FaButton>
        <FaButton v-if="hasPopulation" variant="ghost" @click="emit('suggest')">{{ t('fromPopulation') }}</FaButton>
      </div>
    </form>
  </section>
</template>
