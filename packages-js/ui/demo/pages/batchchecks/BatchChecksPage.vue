<script setup lang="ts">
import { ref } from 'vue'
import { BatchChecks, createBatchchecksRestPort, type BatchchecksAnswer } from '@auditcore/ui'

const port = createBatchchecksRestPort({ baseUrl: '/api/batch-checks' })
const last = ref('')

function onCompleted(answer: BatchchecksAnswer): void {
  last.value = `Ereignis checks-completed: ${answer.summary.findings} Befunde, Stufe ${answer.summary.escalation_level}`
}
</script>

<template>
  <h1>Bestandsprüfung</h1>
  <p>
    <code>&lt;BatchChecks&gt;</code> bzw. <code>&lt;flowaudit-batch-checks&gt;</code> mit dem REST-Port auf
    <code>auditcore_documents.web</code> (Vertrag <code>documents_batch_checks/1</code>): Regeln C-01 bis C-13,
    A-07, B-12 und die Ergänzungen ERG-01/ERG-02 über einen Bestand vieler Belege. Beispielbestand mit
    synthetischen Belegen: <code>packages/auditcore_documents/tests/fixtures/batch/bestand.csv</code>.
  </p>
  <BatchChecks :port="port" @checks-completed="onCompleted" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
