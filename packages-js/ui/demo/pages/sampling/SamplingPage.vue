<script setup lang="ts">
import { ref } from 'vue'
import { SamplingPanel, createSamplingRestPort, type SelectionResult } from '@flowaudit/ui'
import { demoPopulation } from './demo-data'

const port = createSamplingRestPort({ baseUrl: '/api/sampling' })
const items = demoPopulation()
const last = ref('')

function onSelection(result: SelectionResult): void {
  last.value = `Ereignis selection-drawn: ${result.selected} Elemente, Seed ${result.seed}`
}
</script>

<template>
  <h1>Stichprobe</h1>
  <p>
    <code>&lt;SamplingPanel&gt;</code> bzw. <code>&lt;flowaudit-sampling&gt;</code> mit dem REST-Port auf
    <code>auditcore_sampling.web</code>. Beispielbelegliste mit 240 Belegen in zwei Losen.
  </p>
  <SamplingPanel :port="port" :items="items" @selection-drawn="onSelection" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
