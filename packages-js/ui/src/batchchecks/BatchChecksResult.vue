<script setup lang="ts">
import { computed } from 'vue'
import {
  batchchecksLevelText,
  batchchecksLevelTone,
  batchchecksMetricRows,
  batchchecksRuleRows,
  batchchecksSummaryText,
  type BatchchecksAnswer,
  type BatchchecksController,
  type BatchchecksData,
  type BatchchecksExportFormat,
  type BatchchecksTranslate,
  type Locale,
} from '@auditcore/ui-core'
import FaBadge from '../base/FaBadge.vue'
import FaButton from '../base/FaButton.vue'
import { saveFile } from '../rest/download'
import BatchChecksFindings from './BatchChecksFindings.vue'

const props = defineProps<{
  id: string
  controller: BatchchecksController
  state: BatchchecksData
  answer: BatchchecksAnswer
  t: BatchchecksTranslate
  locale: Locale
}>()

const level = computed(() => props.answer.summary.escalation_level)
const rules = computed(() => batchchecksRuleRows(props.answer, props.t))
const metrics = computed(() => batchchecksMetricRows(props.answer, props.t, props.locale))

async function download(format: BatchchecksExportFormat): Promise<void> {
  const file = await props.controller.exportRun(format)
  if (file && typeof URL.createObjectURL === 'function') saveFile(file)
}
</script>

<template>
  <section class="fa-batchchecks__card" :aria-labelledby="`${id}-result`" aria-live="polite" data-testid="batchchecks-result">
    <h3 :id="`${id}-result`" class="fa-batchchecks__heading">{{ `${t('result')} ` }}<FaBadge :tone="batchchecksLevelTone(level)" data-testid="batchchecks-level">{{ batchchecksLevelText(level, t) }}</FaBadge></h3>
    <p class="fa-batchchecks__notice">{{ t('notice') }}</p>
    <p data-testid="batchchecks-summary">{{ batchchecksSummaryText(answer, t) }}</p>
    <p v-if="answer.summary.report_blocked" class="fa-batchchecks__failure" role="alert">{{ t('blocked', { reason: answer.summary.block_reason ?? '' }) }}</p>
    <h4 class="fa-batchchecks__subheading">{{ t('metrics') }}</h4>
    <dl class="fa-batchchecks__summary" data-testid="batchchecks-metrics">
      <template v-for="row in metrics" :key="row.label">
        <dt>{{ row.label }}</dt>
        <dd>{{ row.value }}</dd>
      </template>
    </dl>
    <div v-if="state.request" class="fa-batchchecks__actions">
      <FaButton :loading="state.busy === 'export'" data-testid="batchchecks-export-json" @click="download('json')">{{ t('exportJson') }}</FaButton>
      <FaButton :loading="state.busy === 'export'" data-testid="batchchecks-export-csv" @click="download('csv')">{{ t('exportCsv') }}</FaButton>
    </div>
    <h4 class="fa-batchchecks__subheading">{{ t('rules') }}</h4>
    <div class="fa-batchchecks__scroll">
      <table class="fa-batchchecks__table" data-testid="batchchecks-rules">
        <thead>
          <tr>
            <th scope="col">{{ t('colCode') }}</th>
            <th scope="col">{{ t('colTitle') }}</th>
            <th scope="col">{{ t('colChecks') }}</th>
            <th scope="col">{{ t('colStatus') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rule in rules" :key="rule.code" :data-rule="rule.code">
            <th scope="row">{{ rule.code }}</th>
            <td>{{ rule.title }}<span v-if="rule.supplement" class="fa-batchchecks__note">{{ t('supplement') }}</span></td>
            <td>{{ rule.checks }}<span v-if="rule.basis" class="fa-batchchecks__note">{{ rule.basis }}</span></td>
            <td><FaBadge :tone="rule.tone">{{ rule.status }}</FaBadge><span v-if="rule.note" class="fa-batchchecks__note">{{ rule.note }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    <BatchChecksFindings :id="id" :controller="controller" :answer="answer" :rule-filter="state.ruleFilter" :t="t" />
  </section>
</template>
