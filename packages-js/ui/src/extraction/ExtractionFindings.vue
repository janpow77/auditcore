<script setup lang="ts">
import { computed } from 'vue'
import {
  extractionOutcomeTone,
  extractionRuleLabel,
  splitExtractionFindings,
  type ExtractionFinding,
  type ExtractionTranslate,
} from '@flowaudit/ui-core'
import FaBadge from '../base/FaBadge.vue'

const props = defineProps<{
  findings: readonly ExtractionFinding[]
  flags: readonly string[]
  t: ExtractionTranslate
}>()

const split = computed(() => splitExtractionFindings(props.findings))
</script>

<template>
  <h4 class="fa-extraction__heading">{{ t('findings') }}</h4>
  <p v-if="!split.open.length" class="fa-extraction__muted">{{ t('findingsNone') }}</p>
  <div v-else class="fa-extraction__scroll">
    <table class="fa-extraction__table" data-testid="extraction-findings">
      <thead>
        <tr>
          <th scope="col">{{ t('colRule') }}</th>
          <th scope="col">{{ t('colSeverity') }}</th>
          <th scope="col">{{ t('colOutcome') }}</th>
          <th scope="col">{{ t('colMessage') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="finding in split.open" :key="finding.rule_id" :data-rule="finding.rule_id">
          <th scope="row">{{ extractionRuleLabel(finding, t) }}</th>
          <td>{{ t(`severity${finding.severity}`) }}</td>
          <td><FaBadge :tone="extractionOutcomeTone(finding)">{{ t(`outcome${finding.outcome}`) }}</FaBadge></td>
          <td>{{ finding.message }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <details v-if="split.passed.length" class="fa-extraction__passed">
    <summary>{{ t('passed', { count: split.passed.length }) }}</summary>
    <ul>
      <li v-for="finding in split.passed" :key="finding.rule_id">{{ `${extractionRuleLabel(finding, t)}: ${finding.message}` }}</li>
    </ul>
  </details>
  <template v-if="flags.length">
    <h4 class="fa-extraction__label">{{ t('flags') }}</h4>
    <ul class="fa-extraction__flags" data-testid="extraction-flags">
      <li v-for="flag in flags" :key="flag"><FaBadge>{{ flag }}</FaBadge></li>
    </ul>
  </template>
</template>
