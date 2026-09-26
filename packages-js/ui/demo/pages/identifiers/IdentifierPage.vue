<script setup lang="ts">
import { ref } from 'vue'
import { IdentifierCheck, createIdentifiersRestPort, type IdentifierBatchAnswer, type IdentifierResult } from '@auditcore/ui'

const port = createIdentifiersRestPort({ baseUrl: '/api/identifiers' })
const last = ref('')

function onChecked(result: IdentifierResult): void {
  last.value = `Ereignis identifier-checked: ${result.kind_label} ${result.status}`
}

function onBatch(answer: IdentifierBatchAnswer): void {
  last.value = `Ereignis batch-checked: ${answer.summary.total} Zeilen`
}
</script>

<template>
  <h1>Kennung prüfen</h1>
  <p>
    <code>&lt;IdentifierCheck&gt;</code> bzw. <code>&lt;flowaudit-identifier-check&gt;</code> mit dem REST-Port auf
    <code>auditcore_identifiers.web</code> (Vertrag <code>identifiers_ui/1</code>). Synthetische Beispielwerte:
    IBAN <code>DE89 3704 0044 0532 0130 00</code>, USt-IdNr. <code>DE136695976</code>, LEI <code>7LTWFZYICNSX8D621K86</code>.
  </p>
  <IdentifierCheck :port="port" @identifier-checked="onChecked" @batch-checked="onBatch" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
