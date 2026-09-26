<script setup lang="ts">
import { ref } from 'vue'
import { BenfordPanel, createBenfordRestPort, type BenfordAnalysis } from '@auditcore/ui'
import { demoBenfordValues } from '../sampling/demo-data'

const port = createBenfordRestPort({ baseUrl: '/api/benford' })
const values = demoBenfordValues()
const last = ref('')

function onAnalysis(result: BenfordAnalysis): void {
  last.value = `Ereignis analysis-completed: ${result.conformity.mad_label}`
}
</script>

<template>
  <h1>Benford-Analyse</h1>
  <p>
    <code>&lt;BenfordPanel&gt;</code> bzw. <code>&lt;flowaudit-benford&gt;</code> mit dem REST-Port auf
    <code>auditcore_statistics.web</code>. Beispielbeträge mit gehäufter Anfangsziffer 4.
  </p>
  <BenfordPanel :port="port" :values="values" @analysis-completed="onAnalysis" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
