<script setup lang="ts">
import { computed } from 'vue'
import {
  extrapolationIssueText,
  extrapolationMessages,
  RESIDUAL_FIELDS,
  residualColumns,
  residualMetrics,
  residualRows,
  type ExtrapolationController,
  type ExtrapolationData,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'

const props = withDefaults(defineProps<{ controller: ExtrapolationController; state: ExtrapolationData; locale?: Locale }>(), { locale: undefined })
const { t, locale: active } = useI18n(extrapolationMessages, () => props.locale)
const id = useId('fa-extrapolation-residual')
const rer = computed(() => props.state.residual?.residual_error_rate ?? null)
const metrics = computed(() => (rer.value ? residualMetrics(rer.value, t, active.value) : []))
const columns = computed(() => residualColumns(t, active.value))
const rows = computed(() => (rer.value ? residualRows(rer.value) : []))
const issue = (key: string): string => extrapolationIssueText(props.state.residualIssues, key, t)
const value = (event: Event): string => (event.target as HTMLInputElement).value
</script>

<template>
  <section class="fa-extrapolation__card fa-extrapolation__card--residual" :aria-labelledby="`${id}-title`">
    <h3 :id="`${id}-title`" class="fa-extrapolation__heading">{{ t('residualTitle') }}</h3>
    <p class="fa-extrapolation__hint">{{ t('residualNotice') }}</p>
    <div class="fa-extrapolation__settings">
      <label v-for="field in RESIDUAL_FIELDS" :key="field.key" class="fa-extrapolation__field">
        <span class="fa-extrapolation__label">{{ t(field.label) }}{{ field.key === 'terRate' ? ' (%)' : '' }}</span>
        <input
          class="fa-extrapolation__input fa-extrapolation__input--number"
          inputmode="decimal"
          :value="state.residualForm[field.key]"
          :aria-invalid="issue(field.key) ? 'true' : undefined"
          :data-testid="`extrapolation-rer-${field.key}`"
          @input="controller.setResidual({ [field.key]: value($event) })"
        />
        <span v-if="issue(field.key)" class="fa-extrapolation__error">{{ issue(field.key) }}</span>
      </label>
    </div>
    <div class="fa-extrapolation__actions">
      <FaButton variant="primary" :loading="state.busy === 'residual'" data-testid="extrapolation-residual" @click="controller.computeResidual">{{ t('computeResidual') }}</FaButton>
    </div>
    <template v-if="rer">
      <dl class="fa-extrapolation__metrics" data-testid="extrapolation-rer">
        <div v-for="metric in metrics" :key="metric.id" class="fa-extrapolation__metric" :data-metric="metric.id">
          <dt>{{ metric.label }}</dt>
          <dd class="fa-extrapolation__value">{{ metric.value }}</dd>
          <dd v-if="metric.detail" class="fa-extrapolation__muted">{{ metric.detail }}</dd>
        </div>
      </dl>
      <FaTable :columns="columns" :rows="rows" :caption="t('residualTitle')" :locale="locale" data-testid="extrapolation-rer-rows" />
    </template>
  </section>
</template>
