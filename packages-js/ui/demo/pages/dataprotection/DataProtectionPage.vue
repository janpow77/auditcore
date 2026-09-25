<script setup lang="ts">
import { computed, ref } from 'vue'
import { FaDsfa, FaVvt, createDataProtectionRestPort } from '@flowaudit/ui'

// Nur Demo: Die Person kommt aus dem Kopf X-Demo-Actor; eine Anwendung nimmt Mandant und Person aus ihrer Sitzung.
const actors = [
  { id: 'daten-a', name: 'Dana A. Beispiel (bearbeitet)' },
  { id: 'daten-b', name: 'Bernd B. Muster (gibt frei)' },
] as const
const actor = ref<string>(actors[0].id)
const view = ref<'vvt' | 'dsfa'>('vvt')
const port = computed(() => createDataProtectionRestPort({ baseUrl: '/api/dataprotection', headers: { 'X-Demo-Actor': actor.value } }))
const last = ref('')

function report(name: string, detail: unknown): void {
  last.value = `Ereignis ${name}: ${JSON.stringify(detail)}`
}
</script>

<template>
  <h1>Datenschutz: VVT und DSFA</h1>
  <p>
    <code>&lt;FaVvt&gt;</code>/<code>&lt;flowaudit-vvt&gt;</code> und <code>&lt;FaDsfa&gt;</code>/<code>&lt;flowaudit-dsfa&gt;</code>
    mit dem REST-Port auf <code>auditcore_dataprotection.web</code> (Vertrag <code>dataprotection_ui/1</code>).
    Erfundene Behörde, Profil <code>auditcore.dsgvo 2026.10.3</code>.
  </p>
  <div class="demo-row">
    <label>
      Angemeldet als
      <select v-model="actor" data-testid="dp-actor">
        <option v-for="entry in actors" :key="entry.id" :value="entry.id">{{ entry.name }}</option>
      </select>
    </label>
    <label>
      Ansicht
      <select v-model="view" data-testid="dp-view">
        <option value="vvt">Verzeichnis (Art. 30)</option>
        <option value="dsfa">Folgenabschätzung (Art. 35)</option>
      </select>
    </label>
  </div>
  <FaVvt
    v-if="view === 'vvt'"
    :key="`vvt-${actor}`"
    :port="port"
    :actor="actor"
    @draft-saved="report('draft-saved', $event)"
    @released="report('released', $event)"
  />
  <FaDsfa v-else :key="`dsfa-${actor}`" :port="port" :actor="actor" @assessment-change="report('assessment-change', $event)" />
  <p class="demo-event" aria-live="polite">{{ last }}</p>
</template>
