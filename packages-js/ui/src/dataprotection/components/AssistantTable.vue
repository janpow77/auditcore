<script setup lang="ts">
import { computed } from 'vue'
import { tableRows, tableValue, type AssistantQuestion, type TableRow } from '@auditcore/ui-core'
import { useI18n } from '../../i18n'
import { dataprotectionMessages } from '../core'

const props = defineProps<{ question: AssistantQuestion; value: string }>()
const emit = defineEmits<{ change: [value: string] }>()
const { t } = useI18n(dataprotectionMessages)
const rows = computed(() => tableRows(props.question, props.value))

function update(next: TableRow[]): void {
  emit('change', tableValue(next) || JSON.stringify(next))
}
function setCell(index: number, key: string, cell: string): void {
  update(rows.value.map((row, i) => (i === index ? { ...row, [key]: cell } : row)))
}
function addRow(): void {
  update([...rows.value, Object.fromEntries(props.question.columns.map((c) => [c.key, '']))])
}
function removeRow(index: number): void {
  update(rows.value.filter((_, i) => i !== index))
}
</script>

<template>
  <table class="fa-assistant__table">
    <caption>{{ t('tableCaption', { question: question.text }) }}</caption>
    <thead>
      <tr>
        <th v-for="column in question.columns" :key="column.key" scope="col">{{ column.title }}{{ column.required ? ' *' : '' }}</th>
        <th scope="col"><span class="fa-dataprotection__muted">–</span></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(row, index) in rows" :key="index">
        <td v-for="column in question.columns" :key="column.key">
          <input :value="row[column.key]" type="text" :aria-label="`${column.title} ${index + 1}`" @input="setCell(index, column.key, ($event.target as HTMLInputElement).value)" />
        </td>
        <td><button type="button" @click="removeRow(index)">{{ t('removeRow', { row: index + 1 }) }}</button></td>
      </tr>
    </tbody>
  </table>
  <button type="button" @click="addRow">{{ t('addRow') }}</button>
</template>
