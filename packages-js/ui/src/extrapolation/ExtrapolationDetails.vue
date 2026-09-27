<script setup lang="ts">
import { computed } from 'vue'
import {
  detailWarnings,
  extrapolationMessages,
  groupColumns,
  groupRows,
  periodColumns,
  periodRows,
  recalculationView,
  subsampleColumns,
  subsampleResultRows,
  type EvaluationResult,
  type ExtrapolationCatalogue,
} from '@auditcore/ui-core'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'

const props = withDefaults(defineProps<{ result: EvaluationResult; catalogue: ExtrapolationCatalogue | null; locale?: Locale }>(), { locale: undefined })
const { t, locale: active } = useI18n(extrapolationMessages, () => props.locale)
const id = useId('fa-extrapolation-details')
const periods = computed(() => periodRows(props.result))
const groups = computed(() => groupRows(props.result, props.catalogue))
const subsamples = computed(() => subsampleResultRows(props.result, t))
const recalculation = computed(() => recalculationView(props.result, t, active.value))
const warnings = computed(() => detailWarnings(props.result))
</script>

<template>
  <section class="fa-extrapolation__card" :aria-labelledby="`${id}-title`" data-testid="extrapolation-details">
    <h3 :id="`${id}-title`" class="fa-extrapolation__heading">{{ result.design === 'groups' ? t('detailsGroups') : result.design === 'periods' ? t('detailsPeriods') : t('recalcTitle') }}</h3>
    <FaTable v-if="periods.length" :columns="periodColumns(t, active)" :rows="periods" :caption="t('detailsPeriods')" :locale="locale" data-testid="extrapolation-periods" />
    <FaTable v-if="groups.length" :columns="groupColumns(t, active)" :rows="groups" :caption="t('detailsGroups')" :locale="locale" data-testid="extrapolation-groups" />
    <FaTable v-if="subsamples.length" :columns="subsampleColumns(t, active)" :rows="subsamples" :caption="t('detailsSubsamples')" :locale="locale" data-testid="extrapolation-subsamples" />
    <template v-if="recalculation">
      <h4 class="fa-extrapolation__heading">{{ t('recalcTitle') }}</h4>
      <dl class="fa-extrapolation__metrics" data-testid="extrapolation-recalculation">
        <div v-for="metric in recalculation.metrics" :key="metric.id" class="fa-extrapolation__metric" :data-metric="metric.id">
          <dt>{{ metric.label }}</dt>
          <dd class="fa-extrapolation__value">{{ metric.value }}</dd>
        </div>
      </dl>
      <p class="fa-extrapolation__hint">{{ recalculation.verdict }}</p>
    </template>
    <ul v-if="warnings.length" class="fa-extrapolation__warnings">
      <li v-for="line in warnings" :key="line">{{ line }}</li>
    </ul>
  </section>
</template>
