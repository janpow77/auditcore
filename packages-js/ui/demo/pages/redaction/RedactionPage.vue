<script setup lang="ts">
import { ref } from 'vue'
import { PdfRedaction, createRedactionRestPort, type RedactionResult } from '@auditcore/ui'

const port = createRedactionRestPort({ baseUrl: '/api/redaction' })
const last = ref('')

function onCompleted(result: RedactionResult): void {
  last.value = `Ereignis redaction-completed: ${result.filename}, ${result.report.redactions} Schwärzungen, nachgeprüft: ${result.report.verified ? 'ja' : 'nein'}`
}
</script>

<template>
  <h1>PDF schwärzen</h1>
  <p>
    <code>&lt;PdfRedaction&gt;</code> bzw. <code>&lt;flowaudit-pdf-redaction&gt;</code> mit dem REST-Port auf
    <code>auditcore_pdf.web</code> (Vertrag <code>pdf_redaction/1</code>). Die
    <a href="/api/redaction-demo/beispiel.pdf" download="beispiel.pdf" data-testid="redaction-sample">synthetische Beispiel-PDF</a>
    enthält nur erfundene Namen und Adressen; die KI-Namenserkennung ist eine Attrappe.
  </p>
  <PdfRedaction :port="port" @redaction-completed="onCompleted" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
