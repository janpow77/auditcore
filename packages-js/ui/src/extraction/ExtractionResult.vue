<script setup lang="ts">
import { computed } from 'vue'
import {
  extractionDocumentText,
  extractionFieldThreshold,
  extractionOcrText,
  extractionStatusText,
  extractionStatusTone,
  type ExtractionCatalogue,
  type ExtractionRun,
  type ExtractionTranslate,
  type Locale,
} from '@auditcore/ui-core'
import FaBadge from '../base/FaBadge.vue'
import ExtractionFields from './ExtractionFields.vue'
import ExtractionFindings from './ExtractionFindings.vue'

const props = defineProps<{
  id: string
  result: ExtractionRun
  catalogue: ExtractionCatalogue | null
  t: ExtractionTranslate
  locale: Locale
}>()

const threshold = computed(() => extractionFieldThreshold(props.catalogue, props.result))
const errorText = computed(() => {
  const run = props.result.run
  return run.error_code ? props.t('runError', { code: run.error_code, message: run.error ?? '' }) : ''
})
</script>

<template>
  <section class="fa-extraction__card" :aria-labelledby="`${id}-result`" aria-live="polite" data-testid="extraction-result">
    <h3 :id="`${id}-result`" class="fa-extraction__heading">{{ `${t('result')} ` }}<FaBadge :tone="extractionStatusTone(result)" data-testid="extraction-status">{{ extractionStatusText(result, t) }}</FaBadge></h3>
    <p class="fa-extraction__notice">{{ t('notice') }}</p>
    <p v-if="errorText" class="fa-extraction__failure" role="alert">{{ errorText }}</p>
    <p v-if="result.run.retryable" class="fa-extraction__muted">{{ t('retryable') }}</p>
    <dl class="fa-extraction__summary">
      <dt>{{ t('document') }}</dt>
      <dd>{{ extractionDocumentText(result, t) }}</dd>
      <dt>{{ t('ocr') }}</dt>
      <dd data-testid="extraction-ocr">{{ extractionOcrText(result, t, locale) }}</dd>
      <dt>{{ t('profile') }}</dt>
      <dd>{{ `${result.profile.id} ${result.profile.version}` }}</dd>
    </dl>
    <ExtractionFields :fields="result.fields" :threshold="threshold" :t="t" :locale="locale" />
    <ExtractionFindings :findings="result.findings" :flags="result.flags" :t="t" />
    <details v-if="result.pages.length" class="fa-extraction__pages">
      <summary>{{ t('pagesText') }}</summary>
      <template v-for="page in result.pages" :key="page.page">
        <h4 class="fa-extraction__label">{{ t('pageLabel', { page: page.page }) }}</h4>
        <pre class="fa-extraction__text">{{ page.text }}</pre>
      </template>
    </details>
  </section>
</template>
