<script setup lang="ts">
import { computed } from 'vue'
import { redactionReportRows, type Locale, type RedactionController, type RedactionData, type RedactionTranslate } from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'

const props = defineProps<{ id: string; controller: RedactionController; state: RedactionData; t: RedactionTranslate; locale: Locale }>()
const rows = computed(() => redactionReportRows(props.state, props.t, props.locale))
</script>

<template>
  <section v-if="state.result" class="fa-redaction__card" :aria-labelledby="`${id}-result`" aria-live="polite" data-testid="redaction-result">
    <h3 :id="`${id}-result`" class="fa-redaction__heading">{{ t('resultHeading') }}</h3>
    <p v-if="state.result.report.verified" class="fa-redaction__success">{{ t('verified') }}</p>
    <dl class="fa-redaction__report">
      <template v-for="row in rows" :key="row.key">
        <dt>{{ row.label }}</dt>
        <dd :data-report="row.key">{{ row.value }}</dd>
      </template>
    </dl>
    <div class="fa-redaction__actions">
      <a v-if="state.resultUrl" class="fa-button fa-button--primary fa-button--md" :href="state.resultUrl" :download="state.result.filename" data-testid="redaction-download"><span class="fa-button__label">{{ t('download', { filename: state.result.filename }) }}</span></a>
      <FaButton data-testid="redaction-edit" @click="controller.editAgain">{{ t('editAgain') }}</FaButton>
      <FaButton variant="ghost" data-testid="redaction-reset" @click="controller.reset">{{ t('another') }}</FaButton>
    </div>
  </section>
</template>
