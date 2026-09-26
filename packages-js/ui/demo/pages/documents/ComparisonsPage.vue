<script setup lang="ts">
import { ref } from 'vue'
import { FaComparisons, createSynopsisRestClient } from '@auditcore/ui'

// Nur Demo: demo/api_server.py ordnet alle Anfragen einer Person zu (single_user).
const port = createSynopsisRestClient({ baseUrl: '/api/synopsis' })
const last = ref('')

function report(name: string, detail: unknown): void {
  last.value = `Ereignis ${name}: ${typeof detail === 'string' ? detail : JSON.stringify((detail as { id?: string }).id ?? detail)}`
}
</script>

<template>
  <h1>Dokumentvergleiche</h1>
  <p>
    <code>&lt;FaComparisons&gt;</code>/<code>&lt;flowaudit-comparisons&gt;</code> mit dem REST-Client auf
    <code>auditcore_documents.web</code> (<code>/api/synopsis</code>): neuen Vergleich hochladen (DOCX, DOCM, PDF),
    gespeicherte Vergleiche suchen, öffnen (eingebettete Synopse), löschen und Ergebnisse als JSON importieren.
    Vorbefüllt mit drei Vergleichen aus synthetischen Test-Dokumenten.
  </p>
  <FaComparisons
    :port="port"
    :max-upload-bytes="5 * 1024 * 1024"
    data-testid="comparisons"
    @comparison-created="report('comparison-created', $event)"
    @comparison-imported="report('comparison-imported', $event)"
    @comparison-removed="report('comparison-removed', $event)"
    @comparison-open="report('comparison-open', $event)"
  />
  <p data-testid="comparisons-event">{{ last }}</p>
</template>
