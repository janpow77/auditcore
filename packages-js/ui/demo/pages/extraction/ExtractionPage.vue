<script setup lang="ts">
import { ref } from 'vue'
import { FaExtraction, createExtractionRestPort, type ExtractionRun } from '@flowaudit/ui'

const port = createExtractionRestPort({ baseUrl: '/api/extraction' })
const last = ref('')

function onCompleted(result: ExtractionRun): void {
  last.value = `Ereignis extraction-completed: ${result.run.status}, ${result.fields.length} Felder`
}
</script>

<template>
  <h1>Belegerkennung</h1>
  <p>
    <code>&lt;FaExtraction&gt;</code> bzw. <code>&lt;flowaudit-extraction&gt;</code> mit dem REST-Port auf
    <code>auditcore_documents.web</code> (Vertrag <code>documents_extraction/1</code>). Texterkennung und Donut
    sind im Demo Attrappen; synthetische Rechnungsbilder liegen unter
    <code>packages/auditcore_documents/tests/fixtures/donut</code>.
  </p>
  <FaExtraction :port="port" @extraction-completed="onCompleted" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
