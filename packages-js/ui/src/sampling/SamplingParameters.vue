<script setup lang="ts">
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import { confidenceText, parameterUnit as unit, samplingFieldError, samplingMessages, type FieldError, type MethodProfile } from '@flowaudit/ui-core'

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

function errorText(key: string): string {
  return samplingFieldError(props.errors[key], t, active.value)
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
              {{ confidenceText(level, t, active) }}
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
