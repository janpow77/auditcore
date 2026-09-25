<script setup lang="ts">
import { ref } from 'vue'
import { FaTable, formatNumber, useLocale, type SortState, type TableColumn } from '@flowaudit/ui'

const locale = useLocale()
const sort = ref<SortState | null>({ key: 'betrag', direction: 'desc' })
const selected = ref('')
const columns: TableColumn[] = [
  { key: 'vorhaben', label: 'Vorhaben', sortable: true },
  { key: 'begünstigte', label: 'Begünstigte', sortable: true },
  { key: 'betrag', label: 'Betrag', sortable: true, align: 'end', format: (value) => (typeof value === 'number' ? `${formatNumber(value, locale.value)} €` : '–') },
]
const rows = [
  { id: 'v1', vorhaben: 'Breitbandausbau Nordhessen', begünstigte: 'Landkreis Kassel', betrag: 1250000 },
  { id: 'v2', vorhaben: 'Innovationslabor Wasserstoff', begünstigte: 'Hochschule Darmstadt', betrag: 480500 },
  { id: 'v3', vorhaben: 'Gründerzentrum Fulda', begünstigte: 'Stadt Fulda', betrag: null },
  { id: 'v4', vorhaben: 'Energieeffizienz Mittelstand', begünstigte: 'Müller & Söhne GmbH', betrag: 92000 },
]
</script>

<template>
  <h1>Tabelle</h1>
  <FaTable v-model:sort="sort" :columns="columns" :rows="rows" caption="Vorhaben der Stichprobe" clickable @row-click="selected = String($event.vorhaben)" />
  <p aria-live="polite">{{ selected ? `Ausgewählt: ${selected}` : '' }}</p>
</template>
