<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import { formatNumber, useI18n, type Locale } from '../i18n'
import { benfordMessages } from './messages'
import { levelTone } from './model'
import type { BenfordAnalysis, ConformityProfile } from './types'

const props = withDefaults(defineProps<{ analysis: BenfordAnalysis; profile: ConformityProfile | null; locale?: Locale }>(), {
  locale: undefined,
})
const { t, locale: active } = useI18n(benfordMessages, () => props.locale)
const number = (value: number, digits = 4): string => formatNumber(value, active.value, { maximumFractionDigits: digits })
const conformity = computed(() => props.analysis.conformity)
const distribution = computed(() => props.analysis.distribution)
const excludedTotal = computed(() => {
  const excluded = distribution.value.excluded
  return excluded.zero + excluded.missing + excluded.short
})
const bounds = computed(() => (props.profile?.mad_bounds[conformity.value.test] ?? []).map((bound) => number(bound)).join(' / '))
</script>

<template>
  <dl class="fa-benford__metrics" data-testid="benford-metrics">
    <div class="fa-benford__metric">
      <dt>{{ t('analysed') }}</dt>
      <dd class="fa-benford__value">{{ formatNumber(conformity.analysed, active) }}</dd>
    </div>
    <div class="fa-benford__metric">
      <dt>{{ t('excluded') }}</dt>
      <dd class="fa-benford__value">{{ formatNumber(excludedTotal, active) }}</dd>
      <dd class="fa-benford__detail">
        {{ t('excludedDetail', { zero: distribution.excluded.zero, missing: distribution.excluded.missing, short: distribution.excluded.short, negative: distribution.negative_absolute }) }}
      </dd>
    </div>
    <div class="fa-benford__metric">
      <dt>{{ t('mad') }}</dt>
      <dd class="fa-benford__value">{{ number(conformity.mad, 5) }}</dd>
      <dd><FaBadge :tone="levelTone(conformity.mad_level)" data-testid="benford-level">{{ conformity.mad_label }}</FaBadge></dd>
      <dd class="fa-benford__detail">{{ t('madBounds', { bounds }) }}</dd>
    </div>
    <div class="fa-benford__metric">
      <dt>{{ t('chi2') }}</dt>
      <dd class="fa-benford__value">{{ number(conformity.chi2_statistic, 2) }}</dd>
      <dd class="fa-benford__detail">{{ t('chi2Detail', { dof: conformity.degrees_of_freedom, p: conformity.p_value < 0.0001 ? `< ${number(0.0001)}` : `= ${number(conformity.p_value, 4)}` }) }}</dd>
      <dd>
        <FaBadge :tone="conformity.chi2_exceeds ? 'warning' : 'success'">
          {{ t(conformity.chi2_exceeds ? 'chi2Exceeds' : 'chi2Within', { alpha: number(conformity.significance_level, 3) }) }}
        </FaBadge>
      </dd>
    </div>
    <div class="fa-benford__metric">
      <dt>{{ t('zDigits', { critical: number(conformity.z_critical, 2) }) }}</dt>
      <dd class="fa-benford__value" data-testid="benford-exceeding">{{ conformity.exceeding_digits.length ? conformity.exceeding_digits.join(', ') : t('zNone') }}</dd>
    </div>
  </dl>
</template>
