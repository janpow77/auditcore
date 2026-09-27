<!-- Formularabschnitte der Einstellungen (Felder aus dem Profil-Entwurf). -->
<script setup lang="ts">
import { computed } from 'vue'
import { runnerAbschnitte, runnerNurLesen, type RunnerController, type RunnerData, type RunnerFeld, type RunnerMessageKey, type Translate } from '@auditcore/ui-core'

const props = defineProps<{ state: RunnerData; controller: RunnerController; t: Translate<RunnerMessageKey>; uid: string }>()
const abschnitte = computed(() => runnerAbschnitte(props.state, props.t))
const nurLesen = computed(() => runnerNurLesen(props.state))

function eingabe(feld: RunnerFeld, event: Event): void {
  const target = event.target as HTMLInputElement | HTMLSelectElement
  props.controller.eingabe(feld.pfad, feld.art, feld.art === 'schalter' ? (target as HTMLInputElement).checked : target.value)
}
import RunnerClassName from './RunnerClassName.vue'
import RunnerNewClass from './RunnerNewClass.vue'
</script>

<template>
  <fieldset v-for="abschnitt in abschnitte" :key="abschnitt.id" class="fa-runner__abschnitt">
    <legend>{{ abschnitt.titel }}</legend>
    <RunnerClassName v-if="abschnitt.klasse" :klasse="abschnitt.klasse" :controller="controller" :t="t" :uid="uid" :nur-lesen="nurLesen" />
    <div v-for="feld in abschnitt.felder" :key="feld.id" :class="['fa-runner__feld', feld.art === 'schalter' && 'fa-runner__feld--schalter']">
      <template v-if="feld.art === 'schalter'">
        <input
          :id="`${uid}-${feld.id}`"
          type="checkbox"
          :checked="feld.an"
          :disabled="nurLesen"
          :aria-invalid="feld.fehler ? 'true' : undefined"
          :aria-describedby="feld.fehler ? `${uid}-${feld.id}-fehler` : undefined"
          @change="eingabe(feld, $event)"
        >
        <label :for="`${uid}-${feld.id}`">{{ feld.label }}</label>
      </template>
      <template v-else>
        <label :for="`${uid}-${feld.id}`">{{ feld.label }}</label>
        <select
          v-if="feld.art === 'auswahl'"
          :id="`${uid}-${feld.id}`"
          class="fa-runner__eingabe"
          :value="feld.wert"
          :disabled="nurLesen"
          :aria-invalid="feld.fehler ? 'true' : undefined"
          :aria-describedby="feld.fehler ? `${uid}-${feld.id}-fehler` : undefined"
          @change="eingabe(feld, $event)"
        >
          <option v-for="option in feld.optionen" :key="option.wert" :value="option.wert">{{ option.label }}</option>
        </select>
        <input
          v-else
          :id="`${uid}-${feld.id}`"
          class="fa-runner__eingabe"
          :type="feld.art === 'zahl' ? 'number' : 'text'"
          :step="feld.art === 'zahl' ? feld.schritt : undefined"
          :value="feld.wert"
          :disabled="nurLesen"
          :aria-invalid="feld.fehler ? 'true' : undefined"
          :aria-describedby="feld.fehler ? `${uid}-${feld.id}-fehler` : undefined"
          @input="eingabe(feld, $event)"
        >
      </template>
      <p v-if="feld.fehler" :id="`${uid}-${feld.id}-fehler`" class="fa-runner__feldfehler">{{ feld.fehler }}</p>
    </div>
  </fieldset>
  <RunnerNewClass :state="state" :controller="controller" :t="t" :uid="uid" />
</template>
