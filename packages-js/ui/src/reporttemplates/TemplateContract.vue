<!-- Datenvertrag und Textbausteine einer Vorlage (Teil von ReportTemplates). -->
<script setup lang="ts">
import { computed } from 'vue'
import { reporttemplatesMessages, schemaFields, textBlockRows, type TemplateDetail } from '@auditcore/ui-core'
import { useI18n, type Locale } from '../i18n'

const props = defineProps<{ detail: TemplateDetail; locale?: Locale }>()
const { t } = useI18n(reporttemplatesMessages, () => props.locale)
const fields = computed(() => schemaFields(props.detail))
const blocks = computed(() => textBlockRows(props.detail))
</script>

<template>
  <details class="fa-reporttemplates__card" data-testid="template-contract">
    <summary class="fa-reporttemplates__heading">{{ t('contract') }}</summary>
    <div class="fa-reporttemplates__scroll">
      <table class="fa-reporttemplates__table">
        <thead>
          <tr><th scope="col">{{ t('field') }}</th><th scope="col">{{ t('fieldType') }}</th><th scope="col">{{ t('fieldRequired') }}</th></tr>
        </thead>
        <tbody>
          <tr v-for="field in fields" :key="field.name">
            <td><code>{{ field.name }}</code><span v-if="field.title"> – {{ field.title }}</span></td>
            <td>{{ field.type }}</td>
            <td>{{ field.required ? t('yes') : t('no') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <template v-if="blocks.length">
      <h4 class="fa-reporttemplates__heading">{{ t('textBlocks') }}</h4>
      <ul class="fa-reporttemplates__blocks">
        <li v-for="block in blocks" :key="block.id">
          <strong>{{ block.title }}</strong>
          <span v-if="block.required"> · {{ t('required') }}</span>
          <span v-if="block.conditional"> · {{ t('conditional') }}</span>
          <span v-if="block.legalBasis" class="fa-reporttemplates__muted"> · {{ t('legalBasis', { basis: block.legalBasis }) }}</span>
        </li>
      </ul>
    </template>
  </details>
</template>
