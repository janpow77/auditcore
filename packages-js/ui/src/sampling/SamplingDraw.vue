<script setup lang="ts">
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import { samplingMessages, type SamplingMessageKey } from './messages'
import type { SelectionError } from './useSampling'
import type { AllocationMethod, MethodProfile, NamedOption, SelectionVariant } from './types'

const props = withDefaults(defineProps<{
  profile: MethodProfile
  variants: readonly NamedOption<SelectionVariant>[]
  allocations: readonly NamedOption<AllocationMethod>[]
  stratified: boolean
  error: SelectionError | null
  busy?: boolean
  canRedraw?: boolean
  locale?: Locale
}>(), { busy: false, canRedraw: false, locale: undefined })

const sampleSize = defineModel<string>('sampleSize', { required: true })
const seed = defineModel<string>('seed', { required: true })
const variant = defineModel<SelectionVariant | null>('variant', { required: true })
const allocation = defineModel<AllocationMethod | null>('allocation', { required: true })
const emit = defineEmits<{ draw: [fresh: boolean] }>()
const { t } = useI18n(samplingMessages, () => props.locale)
const id = useId('fa-sampling-draw')

function errorKey(error: SelectionError): SamplingMessageKey {
  return `selectionError${error}`
}

function onAllocation(event: Event): void {
  const value = (event.target as HTMLSelectElement).value
  allocation.value = value === '' ? null : (value as AllocationMethod)
}
</script>

<template>
  <form class="fa-sampling__form" novalidate :aria-labelledby="`${id}-title`" @submit.prevent="emit('draw', false)">
    <h3 :id="`${id}-title`" class="fa-sampling__heading">{{ t('selection') }}</h3>
    <div class="fa-sampling__draw-fields">
      <label class="fa-sampling__field">
        <span class="fa-sampling__label">{{ t('sampleSize') }}</span>
        <input v-model="sampleSize" class="fa-sampling__input" inputmode="numeric" data-testid="sampling-sample-size" />
      </label>
      <label v-if="profile.kind === 'mus'" class="fa-sampling__field">
        <span class="fa-sampling__label">{{ t('variant') }}</span>
        <select v-model="variant" class="fa-sampling__select" data-testid="sampling-variant">
          <option v-for="option in variants" :key="option.id" :value="option.id" :title="option.description">{{ option.label }}</option>
        </select>
      </label>
      <label v-if="stratified" class="fa-sampling__field">
        <span class="fa-sampling__label">{{ t('allocation') }}</span>
        <select class="fa-sampling__select" data-testid="sampling-allocation" :value="allocation ?? ''" @change="onAllocation">
          <option value="">{{ t('choose') }}</option>
          <option v-for="option in allocations" :key="option.id" :value="option.id">{{ option.label }} ({{ option.formula }})</option>
        </select>
      </label>
      <label class="fa-sampling__field">
        <span class="fa-sampling__label">{{ t('seed') }}</span>
        <input v-model="seed" class="fa-sampling__input fa-sampling__input--mono" inputmode="numeric" data-testid="sampling-seed" :aria-describedby="`${id}-seed-hint`" />
        <span :id="`${id}-seed-hint`" class="fa-sampling__hint">{{ t('seedHint') }}</span>
      </label>
    </div>
    <p v-if="error" class="fa-sampling__error" role="alert">{{ t(errorKey(error)) }}</p>
    <div class="fa-sampling__actions">
      <FaButton variant="primary" type="submit" :loading="busy" data-testid="sampling-draw">{{ t('draw') }}</FaButton>
      <FaButton v-if="canRedraw" variant="secondary" :disabled="busy" data-testid="sampling-redraw" @click="emit('draw', true)">{{ t('redraw') }}</FaButton>
    </div>
  </form>
</template>
