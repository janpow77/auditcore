<script setup lang="ts">
import {
  reportCellText,
  reportingMessages,
  reportingSampleNote,
  reportingSheetHeading,
  type TablePreview,
} from '@flowaudit/ui-core'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{ table: TablePreview; index: number; locale?: Locale }>(), { locale: undefined })
const { t, locale: active } = useI18n(reportingMessages, () => props.locale)
</script>

<template>
  <section class="fa-report__sheet" :data-testid="`report-sheet-${index}`">
    <h4 class="fa-report__heading">{{ reportingSheetHeading(table, t, active) }}</h4>
    <div class="fa-report__scroll">
      <table class="fa-report__table" data-testid="report-columns">
        <caption>{{ t('columns') }}</caption>
        <thead>
          <tr><th scope="col">{{ t('colName') }}</th><th scope="col">{{ t('colType') }}</th><th scope="col">{{ t('colFormat') }}</th><th scope="col">{{ t('colSource') }}</th></tr>
        </thead>
        <tbody>
          <tr v-for="column in table.columns" :key="column.name">
            <th scope="row">{{ column.name }}</th>
            <td>{{ column.type }}</td>
            <td><code>{{ column.format }}</code></td>
            <td>{{ t(column.source === 'override' ? 'sourceoverride' : 'sourceprofile') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="fa-report__scroll">
      <table class="fa-report__table" data-testid="report-sample">
        <caption>{{ t('sample') }}</caption>
        <thead>
          <tr><th v-for="column in table.columns" :key="column.name" scope="col">{{ column.name }}</th></tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in table.sample" :key="rowIndex">
            <td v-for="(cell, cellIndex) in row" :key="cellIndex">{{ reportCellText(cell, active) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="reportingSampleNote(table, t, active)" class="fa-report__muted">{{ reportingSampleNote(table, t, active) }}</p>
  </section>
</template>
