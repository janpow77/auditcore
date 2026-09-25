<script setup lang="ts">
import { computed, ref } from 'vue'
import { ScreeningReview, createScreeningRestPort } from '@flowaudit/ui'

// Nur Demo: Die Person kommt aus dem Kopf X-Demo-Actor; eine Anwendung nimmt ihre Sitzung.
const actors = [
  { id: 'pruefer-a', name: 'Prüferin A. Beispiel' },
  { id: 'pruefer-b', name: 'Prüfer B. Muster' },
] as const
const actor = ref<string>(actors[0].id)
const port = computed(() => createScreeningRestPort({ baseUrl: '/api/screening', headers: { 'X-Demo-Actor': actor.value } }))
const last = ref('')

function onDecided(detail: { hitId: string; status: string }): void {
  last.value = `Ereignis decided: ${detail.hitId} → ${detail.status}`
}
</script>

<template>
  <h1>Screening-Trefferprüfung</h1>
  <p>
    <code>&lt;ScreeningReview&gt;</code> bzw. <code>&lt;flowaudit-screening-review&gt;</code> mit dem REST-Port auf
    <code>auditcore_registry_sources.web</code> (Vertrag <code>screening_review/1</code>). Ausschließlich erfundene Personendaten.
  </p>
  <label class="demo-row">
    Angemeldet als
    <select v-model="actor" data-testid="screening-actor">
      <option v-for="entry in actors" :key="entry.id" :value="entry.id">{{ entry.name }}</option>
    </select>
  </label>
  <ScreeningReview :key="actor" :port="port" @decided="onDecided" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
