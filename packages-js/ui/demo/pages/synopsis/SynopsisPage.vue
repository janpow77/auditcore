<script setup lang="ts">
import { computed, ref } from 'vue'
import { FaSynopsis, type Comparison, type ExportPayload, type RowUpdate, type SynopsisLayout } from '@auditcore/ui'
import article from '../../../../ui-core/test/fixtures/synopsis-article.json'
import checklist from '../../../../ui-core/test/fixtures/synopsis-checklist.json'
import standard from '../../../../ui-core/test/fixtures/synopsis-standard.json'

// Echte Ergebnisse von auditcore_documents.web (synthetische Dokumente, keine Echtdaten).
const samples = {
  standard: { label: 'Förderrichtlinie (Fließtext)', data: standard as unknown as Comparison },
  checklist: { label: 'Prüfcheckliste (Antworten, Bemerkungen)', data: checklist as unknown as Comparison },
  article: { label: 'Artikelgesetz auf Stammgesetz', data: article as unknown as Comparison },
} as const
type SampleKey = keyof typeof samples

const selected = ref<SampleKey>('standard')
const layout = ref<SynopsisLayout>('side-by-side')
const editable = ref(false)
const asElement = ref(false)
const log = ref('')
const comparison = computed(() => samples[selected.value].data)

function onRowUpdate(update: RowUpdate): void {
  log.value = `Zeile ${update.row_id} geändert: ${JSON.stringify({ selected: update.selected, reason: update.reason })}`
}

function onExport(payload: ExportPayload): void {
  log.value = `Export ${payload.format}: ${payload.filename} (${payload.content.length} Zeichen)`
}

function onElementEvent(name: string, event: Event): void {
  const detail = (event as CustomEvent<unknown[]>).detail
  log.value = `Ereignis ${name}: ${JSON.stringify(detail?.[0])}`
}
</script>

<template>
  <h1>Synopse / Versionsvergleich</h1>
  <p class="synopsis-demo__intro">
    Zwei Fassungen seitenweise oder im Text vergleichen, zwischen Änderungen springen (Tasten N/J und P/K),
    filtern und als HTML, Markdown oder Druckansicht ausgeben. Daten: <code>ComparisonResult</code> aus
    <code>auditcore_documents.web</code>.
  </p>
  <div class="synopsis-demo__controls">
    <fieldset>
      <legend>Beispiel</legend>
      <label v-for="(sample, key) in samples" :key="key">
        <input v-model="selected" type="radio" name="synopsis-sample" :value="key" :data-testid="`sample-${key}`" /> {{ sample.label }}
      </label>
    </fieldset>
    <label><input v-model="editable" type="checkbox" data-testid="editable" /> Vorschau bearbeiten (Auswahl und Grund)</label>
    <label><input v-model="asElement" type="checkbox" data-testid="as-element" /> Als Web Component &lt;flowaudit-synopsis&gt;</label>
  </div>
  <FaSynopsis
    v-if="!asElement"
    v-model:layout="layout"
    :comparison="comparison"
    :editable="editable"
    @row-update="onRowUpdate"
    @export="onExport"
  />
  <flowaudit-synopsis
    v-else
    :comparison.prop="comparison"
    :editable.prop="editable"
    @navigate="onElementEvent('navigate', $event)"
    @export="onElementEvent('export', $event)"
  ></flowaudit-synopsis>
  <p class="synopsis-demo__log" aria-live="polite" data-testid="event-log">{{ log }}</p>
</template>

<style>
.synopsis-demo__intro { max-width: 60rem; color: var(--fa-color-text-muted); }
.synopsis-demo__controls { display: flex; flex-wrap: wrap; gap: var(--fa-space-3) var(--fa-space-5); align-items: center; margin-bottom: var(--fa-space-4); font-size: var(--fa-font-size-sm); }
.synopsis-demo__controls fieldset { display: flex; flex-wrap: wrap; gap: var(--fa-space-3); margin: 0; padding: var(--fa-space-2) var(--fa-space-3); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); }
.synopsis-demo__controls label { display: inline-flex; gap: var(--fa-space-1); align-items: center; }
.synopsis-demo__log { min-height: 1.5em; font-family: var(--fa-font-mono); font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
</style>
