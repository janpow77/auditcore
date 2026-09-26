<script setup lang="ts">
import { ref } from 'vue'
import { ReportExportPanel, createReportingRestPort, type ReportTableInput } from '@auditcore/ui'

const port = createReportingRestPort({ baseUrl: '/api/reporting' })
const tables: ReportTableInput[] = [
  {
    name: 'Vorhaben',
    columns: ['Vorhaben', 'Betrag', 'Quote %', 'Datum', 'Kennung'],
    rows: Array.from({ length: 30 }, (_, i) => [
      `V-${String(i + 1).padStart(3, '0')}`,
      Math.round(((i * 7919) % 250000) + 1000) / 100,
      ((i * 13) % 100) / 100,
      `2026-${String((i % 12) + 1).padStart(2, '0')}-15`,
      String(4711 + i).padStart(6, '0'),
    ]),
    types: { Datum: 'date', Kennung: 'text' },
    formats: { Kennung: '@' },
  },
  { name: 'Hinweise', columns: ['Nr.', 'Text'], rows: [[1, '=SUMME(A1:A3) bleibt Text'], [2, 'Synthetische Demodaten']] },
]
const last = ref('')
</script>

<template>
  <h1>Tabellenexport (Excel)</h1>
  <p>
    <code>&lt;ReportExportPanel&gt;</code> bzw. <code>&lt;flowaudit-report-export&gt;</code> mit dem REST-Port auf
    <code>auditcore_reporting.web</code> (Vertrag <code>reporting_ui/1</code>). Synthetische Vorhaben in zwei Blättern.
  </p>
  <ReportExportPanel :port="port" :tables="tables" filename="Vorhabenliste" @export-completed="(file) => (last = `Ereignis export-completed: ${file.filename}`)" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
