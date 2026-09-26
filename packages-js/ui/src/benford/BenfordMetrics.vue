<script setup lang="ts">
import { computed } from 'vue'
import { benfordMessages, benfordMetricTexts, levelTone, type BenfordAnalysis, type ConformityProfile } from '@flowaudit/ui-core'
import FaBadge from '../base/FaBadge.vue'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{ analysis: BenfordAnalysis; profile: ConformityProfile | null; locale?: Locale }>(), {
  locale: undefined,
})
const { t, locale: active } = useI18n(benfordMessages, () => props.locale)
const conformity = computed(() => props.analysis.conformity)
const texts = computed(() => benfordMetricTexts(props.analysis, props.profile, t, active.value))
</script>

<template>
  <dl class="fa-benford__metrics" data-testid="benford-metrics">
    <div class="fa-benford__metric">
      <dt>{{ t('analysed') }}</dt>
      <dd class="fa-benford__value">{{ texts.analysed }}</dd>
    </div>
    <div class="fa-benford__metric">
      <dt>{{ t('excluded') }}</dt>
      <dd class="fa-benford__value">{{ texts.excluded }}</dd>
      <dd class="fa-benford__detail">{{ texts.excludedDetail }}</dd>
    </div>
    <div class="fa-benford__metric">
      <dt>{{ t('mad') }}</dt>
      <dd class="fa-benford__value">{{ texts.mad }}</dd>
      <dd><FaBadge :tone="levelTone(conformity.mad_level)" data-testid="benford-level">{{ conformity.mad_label }}</FaBadge></dd>
      <dd class="fa-benford__detail">{{ texts.madBounds }}</dd>
    </div>
    <div class="fa-benford__metric">
      <dt>{{ t('chi2') }}</dt>
      <dd class="fa-benford__value">{{ texts.chi2 }}</dd>
      <dd class="fa-benford__detail">{{ texts.chi2Detail }}</dd>
      <dd>
        <FaBadge :tone="conformity.chi2_exceeds ? 'warning' : 'success'">{{ texts.chi2Verdict }}</FaBadge>
      </dd>
    </div>
    <div class="fa-benford__metric">
      <dt>{{ texts.zDigits }}</dt>
      <dd class="fa-benford__value" data-testid="benford-exceeding">{{ texts.exceeding }}</dd>
    </div>
  </dl>
</template>
