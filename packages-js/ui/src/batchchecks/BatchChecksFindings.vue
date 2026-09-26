<script setup lang="ts">
import { computed } from 'vue'
import {
  batchchecksFilterOptions,
  batchchecksFindingRows,
  type BatchchecksAnswer,
  type BatchchecksController,
  type BatchchecksTranslate,
} from '@auditcore/ui-core'
import FaBadge from '../base/FaBadge.vue'

const props = defineProps<{
  id: string
  controller: BatchchecksController
  answer: BatchchecksAnswer
  ruleFilter: string | null
  t: BatchchecksTranslate
}>()

const options = computed(() => batchchecksFilterOptions(props.answer))
const rows = computed(() => batchchecksFindingRows(props.answer, props.ruleFilter, props.t))

function onFilter(event: Event): void {
  props.controller.setRuleFilter((event.target as HTMLSelectElement).value || null)
}
</script>

<template>
  <h4 class="fa-batchchecks__subheading">{{ t('findings') }}</h4>
  <p v-if="!answer.findings.length" class="fa-batchchecks__muted">{{ t('findingsNone') }}</p>
  <template v-else>
    <label class="fa-batchchecks__field">
      <span class="fa-batchchecks__label">{{ t('filterRule') }}</span>
      <select class="fa-batchchecks__input" :value="ruleFilter ?? ''" data-testid="batchchecks-filter" @change="onFilter">
        <option value="">{{ t('allRules') }}</option>
        <option v-for="option in options" :key="option.code" :value="option.code">{{ option.label }}</option>
      </select>
    </label>
    <div class="fa-batchchecks__scroll">
      <table class="fa-batchchecks__table" data-testid="batchchecks-findings">
        <thead>
          <tr>
            <th scope="col">{{ t('colId') }}</th>
            <th scope="col">{{ t('colCode') }}</th>
            <th scope="col">{{ t('colLevel') }}</th>
            <th scope="col">{{ t('colMessage') }}</th>
            <th scope="col">{{ t('colAffected') }}</th>
            <th scope="col">{{ t('colBasis') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" :data-finding="row.id" :data-rule="row.rule">
            <th scope="row">{{ row.id }}</th>
            <td>{{ row.rule }}</td>
            <td><FaBadge :tone="row.tone">{{ row.level }}</FaBadge></td>
            <td>{{ row.message }}</td>
            <td>{{ row.affected }}</td>
            <td>{{ row.basis }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
</template>
