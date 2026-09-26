<script setup lang="ts">
import { computed } from 'vue'
import { useId } from '../composables/useId'
import { derivationColumns, derivationRows, samplingMessages, sizeTexts, type SizeResult } from '@auditcore/ui-core'
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'

const props = withDefaults(defineProps<{ result: SizeResult; locale?: Locale }>(), { locale: undefined })
const { t, locale: active } = useI18n(samplingMessages, () => props.locale)
const id = useId('fa-sampling-result')
const columns = computed(() => derivationColumns(t, active.value))
const rows = computed(() => derivationRows(props.result))
const texts = computed(() => sizeTexts(props.result, t, active.value))
</script>

<template>
  <section class="fa-sampling__card fa-sampling__card--result" :aria-labelledby="`${id}-title`" aria-live="polite">
    <h3 :id="`${id}-title`" class="fa-sampling__heading">{{ t('result') }}</h3>
    <p class="fa-sampling__size" data-testid="sampling-size">{{ texts.size }}</p>
    <p v-if="result.kind === 'mus'" class="fa-sampling__muted">{{ texts.interval }}</p>
    <ul v-if="result.warnings.length" class="fa-sampling__warnings">
      <li v-for="warning in result.warnings" :key="warning">{{ warning }}</li>
    </ul>
    <FaTable v-if="rows.length" :columns="columns" :rows="rows" :caption="t('derivation')" :locale="locale" />
  </section>
</template>
