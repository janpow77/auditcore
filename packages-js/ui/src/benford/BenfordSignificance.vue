<script setup lang="ts">
import { computed } from 'vue'
import { benfordChiTexts, benfordDigitZTexts, benfordMessages, type BenfordAnalysis } from '@auditcore/ui-core'
import FaBadge from '../base/FaBadge.vue'
import { useI18n, type Locale } from '../i18n'

type Metrics = NonNullable<BenfordAnalysis['metrics']>

const props = withDefaults(defineProps<{ metrics: Metrics; locale?: Locale }>(), { locale: undefined })
const { t, locale: active } = useI18n(benfordMessages, () => props.locale)
const chi = computed(() => (props.metrics.chi_square ? benfordChiTexts(props.metrics.chi_square, t, active.value) : null))
const z = computed(() => (props.metrics.digit_z ? benfordDigitZTexts(props.metrics.digit_z, t, active.value) : null))
</script>

<template>
  <dl class="fa-benford__metrics" data-testid="benford-significance" :aria-label="t('significance')">
    <div v-if="chi" class="fa-benford__metric">
      <dt>{{ t('chiTest') }}</dt>
      <dd class="fa-benford__value">{{ chi.statistic }}</dd>
      <dd class="fa-benford__detail">{{ chi.detail }}</dd>
      <dd class="fa-benford__detail" data-testid="benford-critical">{{ chi.critical }}</dd>
      <dd><FaBadge :tone="chi.tone">{{ chi.verdict }}</FaBadge></dd>
    </div>
    <div v-if="z" class="fa-benford__metric">
      <dt>{{ t('digitZ') }}</dt>
      <dd class="fa-benford__value" data-testid="benford-conspicuous">{{ z.digits }}</dd>
      <dd class="fa-benford__detail">{{ z.detail }}</dd>
      <dd class="fa-benford__detail">{{ z.largest }}</dd>
    </div>
  </dl>
</template>
