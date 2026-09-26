<script setup lang="ts">
import { computed, ref } from 'vue'
import { FaDbKanban, type Locale, type RecordTable } from '@auditcore/ui'
import { demoLocale } from '../../locale'

// Erfundene Prüfliste in der Form der audit_designer-Datenbank (Eigenschaften und Zeilen).
const table = ref<RecordTable>({
  properties: [
    { id: 'titel', name: 'Vorhaben', type: 'text' },
    { id: 'status', name: 'Status', type: 'select', options: ['offen', 'in Prüfung', 'Feststellungen', 'abgeschlossen'] },
    { id: 'fonds', name: 'Fonds', type: 'select', options: ['EFRE', 'ESF+', 'JTF'] },
    { id: 'betrag', name: 'Förderfähige Ausgaben (€)', type: 'number' },
    { id: 'vor_ort', name: 'Vor-Ort-Prüfung', type: 'checkbox' },
  ],
  rows: [
    { id: 'v1', cells: { titel: 'Breitbandausbau Nord', status: 'offen', fonds: 'EFRE', betrag: 1250000, vor_ort: true } },
    { id: 'v2', cells: { titel: 'Weiterbildung Pflege', status: 'in Prüfung', fonds: 'ESF+', betrag: 84000, vor_ort: false } },
    { id: 'v3', cells: { titel: 'Innovationszentrum', status: 'Feststellungen', fonds: 'EFRE', betrag: 2300000, vor_ort: true } },
    { id: 'v4', cells: { titel: 'Strukturwandel Revier', status: null, fonds: 'JTF', betrag: 510000 } },
    { id: 'v5', cells: { titel: 'Energieberatung KMU', status: 'abgeschlossen', fonds: 'EFRE', betrag: 96000, vor_ort: false } },
  ],
})
const groupBy = ref('status')
const editable = ref(true)
const last = ref('')
const locale = computed<Locale>(() => demoLocale.value)

function report(name: string, detail: unknown): void {
  last.value = `Ereignis ${name}: ${JSON.stringify(detail)}`
}
</script>

<template>
  <h1>Datenbankansicht als Kanban</h1>
  <p>
    <code>&lt;FaDbKanban&gt;</code>/<code>&lt;flowaudit-db-kanban&gt;</code>: Datensätze einer Tabelle nach einer
    Auswahl-Eigenschaft gruppiert (<code>useDbKanban</code> aus audit_designer). Ablegen oder Strg+Pfeil setzt den Wert,
    die Spalte „Ohne Wert“ nimmt leere und unbekannte Werte auf. Hier ohne Server über die Eigenschaft
    <code>table</code> und das Ereignis <code>table-change</code>; Anwendungen übergeben ihre Datenbank als <code>RecordPort</code>.
  </p>
  <div class="demo-row">
    <label><input v-model="editable" type="checkbox" data-testid="dbk-editable" /> bearbeitbar</label>
    <span data-testid="dbk-group">Gruppierung: {{ groupBy }}</span>
  </div>
  <FaDbKanban
    v-model:group-by="groupBy"
    :table="table"
    :editable="editable"
    :locale="locale"
    @table-change="table = $event"
    @record-move="report('record-move', $event)"
    @record-add="report('record-add', $event.id)"
  />
  <p data-testid="dbk-event">{{ last }}</p>
</template>
