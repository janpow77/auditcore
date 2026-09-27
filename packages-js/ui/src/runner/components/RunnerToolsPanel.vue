<!-- Bereich „Werkzeuge“: je Prüfprofil Werkzeuge an/aus, Zeitlimit, Priorität, installierte Version. -->
<script setup lang="ts">
import { computed } from 'vue'
import { runnerNurLesen, runnerWerkzeugeGeaendert, runnerWerkzeugGruppen, type RunnerController, type RunnerData, type RunnerMessageKey, type Translate } from '@auditcore/ui-core'
import FaButton from '../../base/FaButton.vue'

const props = defineProps<{ state: RunnerData; controller: RunnerController; t: Translate<RunnerMessageKey> }>()
const gruppen = computed(() => runnerWerkzeugGruppen(props.state, props.t))
const nurLesen = computed(() => runnerNurLesen(props.state))
const geaendert = computed(() => runnerWerkzeugeGeaendert(props.state))

function aktiv(profil: string, werkzeug: string, event: Event): void {
  props.controller.werkzeug(profil, werkzeug, { aktiv: (event.target as HTMLInputElement).checked })
}

function zahl(profil: string, werkzeug: string, feld: 'zeitlimit_s' | 'prioritaet', event: Event): void {
  props.controller.werkzeugZahl(profil, werkzeug, feld, (event.target as HTMLInputElement).value)
}
</script>

<template>
  <p v-if="!gruppen.length" class="fa-runner__muted">{{ t('keineWerkzeuge') }}</p>
  <table v-for="gruppe in gruppen" :key="gruppe.profil" class="fa-runner__tabelle">
    <caption>{{ gruppe.titel }}</caption>
    <thead>
      <tr>
        <th scope="col">{{ t('spalteWerkzeug') }}</th>
        <th scope="col">{{ t('spalteBereich') }}</th>
        <th scope="col">{{ t('spalteImage') }}</th>
        <th scope="col">{{ t('spalteAktiv') }}</th>
        <th scope="col">{{ t('spalteZeitlimit') }}</th>
        <th scope="col">{{ t('spaltePrioritaet') }}</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="zeile in gruppe.zeilen" :key="zeile.id">
        <th scope="row">{{ zeile.werkzeug }}</th>
        <td>{{ zeile.bereich }}</td>
        <td>{{ zeile.imImage }}</td>
        <td><input type="checkbox" :checked="zeile.aktiv" :disabled="nurLesen" :aria-label="`${t('spalteAktiv')}: ${zeile.werkzeug}`" @change="aktiv(gruppe.profil, zeile.werkzeug, $event)"></td>
        <td><input class="fa-runner__eingabe fa-runner__schmal" type="number" min="1" :value="zeile.zeitlimit" :disabled="nurLesen" :aria-label="`${t('spalteZeitlimit')}: ${zeile.werkzeug}`" @input="zahl(gruppe.profil, zeile.werkzeug, 'zeitlimit_s', $event)"></td>
        <td><input class="fa-runner__eingabe fa-runner__schmal" type="number" min="0" :value="zeile.prioritaet" :disabled="nurLesen" :aria-label="`${t('spaltePrioritaet')}: ${zeile.werkzeug}`" @input="zahl(gruppe.profil, zeile.werkzeug, 'prioritaet', $event)"></td>
      </tr>
    </tbody>
  </table>
  <div class="fa-runner__aktionen">
    <FaButton variant="primary" :disabled="nurLesen || !geaendert" :loading="state.busy === 'werkzeuge'" @click="controller.werkzeugeSpeichern()">{{ t('speichern') }}</FaButton>
  </div>
</template>
