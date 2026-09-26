<script setup lang="ts">
import { ref } from 'vue'
import { FaButton, FaTable, formatNumber, useTheme, type SortState, type TableColumn, type TableRow } from '@auditcore/ui'
import { locale } from './locale'

const columns: TableColumn[] = [
  { key: 'beleg', label: 'Beleg', sortable: true },
  { key: 'datum', label: 'Datum', sortable: true },
  { key: 'betrag', label: 'Betrag (EUR)', align: 'end', sortable: true, format: (value) => formatNumber(Number(value), locale.value) },
]
const rows: TableRow[] = [
  { id: 'r1', beleg: 'R-2026-001', datum: '2026-03-02', betrag: 1250.5 },
  { id: 'r2', beleg: 'R-2026-002', datum: '2026-03-09', betrag: 980 },
  { id: 'r3', beleg: 'R-2026-003', datum: '2026-04-01', betrag: 12400 },
]

const sort = ref<SortState | null>(null)
const selected = ref<TableRow | null>(null)
// Hell/Dunkel: setzt data-fa-theme am <html>; ohne Wahl gilt prefers-color-scheme.
const theme = useTheme()

function toggleLocale(): void {
  locale.value = locale.value === 'de' ? 'en' : 'de'
}
</script>

<template>
  <main class="beispiel">
    <h1>Belege</h1>
    <p class="aktionen">
      <FaButton variant="secondary" @click="theme.toggle()">Hell/Dunkel</FaButton>
      <FaButton variant="secondary" @click="toggleLocale">Sprache: {{ locale }}</FaButton>
    </p>
    <FaTable v-model:sort="sort" :columns="columns" :rows="rows" caption="Belege" clickable @row-click="selected = $event" />
    <p v-if="selected" role="status">Ausgewählt: {{ selected.beleg }}</p>
  </main>
</template>

<style>
html {
  background: var(--fa-color-bg);
}
.beispiel {
  max-width: 48rem;
  margin: 2rem auto;
  padding: 0 1rem;
  font-family: var(--fa-font-sans);
  color: var(--fa-color-text);
}
.aktionen {
  display: flex;
  gap: 0.5rem;
}
</style>
