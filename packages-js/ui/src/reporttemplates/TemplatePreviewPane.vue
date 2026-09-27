<!-- Ergebnis der Vorlagenvorschau: Prüfung des Datenvertrags und abgeschottete HTML-Ansicht. -->
<script setup lang="ts">
import { reporttemplatesMessages, type TemplatePreview } from '@auditcore/ui-core'
import { useI18n, type Locale } from '../i18n'

const props = defineProps<{ preview: TemplatePreview; stale: boolean; locale?: Locale }>()
const { t } = useI18n(reporttemplatesMessages, () => props.locale)
</script>

<template>
  <section class="fa-reporttemplates__card" aria-live="polite" data-testid="template-preview">
    <h3 class="fa-reporttemplates__heading">{{ t('preview') }}</h3>
    <p v-if="stale" class="fa-reporttemplates__notice">{{ t('previewStale') }}</p>
    <template v-if="preview.valid">
      <p class="fa-reporttemplates__muted">{{ t('valid') }}</p>
      <p class="fa-reporttemplates__muted">{{ preview.text_blocks.length ? t('usedBlocks', { blocks: preview.text_blocks.join(', ') }) : t('noBlocks') }}</p>
      <iframe v-if="preview.html" class="fa-reporttemplates__frame" sandbox="" referrerpolicy="no-referrer" :title="t('previewFrame')" :srcdoc="preview.html" />
    </template>
    <template v-else>
      <p class="fa-reporttemplates__failure" role="alert">{{ t('invalid', { count: preview.issues.length }) }}</p>
      <ul class="fa-reporttemplates__issues">
        <li v-for="issue in preview.issues" :key="issue.path + issue.message"><code>{{ issue.path }}</code>: {{ issue.message }}</li>
      </ul>
    </template>
    <p class="fa-reporttemplates__muted">{{ t('notice') }}</p>
  </section>
</template>
