<!-- Neue Runner-Klasse anlegen (Art cpu, neutrale Werte; Prüfung wie im Backend). -->
<script setup lang="ts">
import { computed } from 'vue'
import { runnerNeueKlasse, runnerNurLesen, type RunnerController, type RunnerData, type RunnerMessageKey, type Translate } from '@auditcore/ui-core'
import FaButton from '../../base/FaButton.vue'

const props = defineProps<{ state: RunnerData; controller: RunnerController; t: Translate<RunnerMessageKey>; uid: string }>()
const neu = computed(() => runnerNeueKlasse(props.state, props.t))
const nurLesen = computed(() => runnerNurLesen(props.state))
const id = `${props.uid}-neue-klasse`
</script>

<template>
  <fieldset class="fa-runner__abschnitt">
    <legend>{{ t('neueKlasse') }}</legend>
    <div class="fa-runner__feld fa-runner__klassenname">
      <label :for="id">{{ t('klasseName') }}</label>
      <span class="fa-runner__aktionen">
        <input
          :id="id"
          class="fa-runner__eingabe"
          type="text"
          maxlength="31"
          :value="neu.wert"
          :disabled="nurLesen"
          :aria-invalid="neu.fehler ? 'true' : undefined"
          :aria-describedby="neu.fehler ? `${id}-fehler` : undefined"
          @input="controller.neueKlasseEingabe(($event.target as HTMLInputElement).value)"
        >
        <FaButton size="sm" icon="plus" :disabled="nurLesen || !neu.moeglich" @click="controller.klasseHinzufuegen()">{{ t('hinzufuegen') }}</FaButton>
      </span>
      <p v-if="neu.fehler" :id="`${id}-fehler`" class="fa-runner__feldfehler">{{ neu.fehler }}</p>
    </div>
  </fieldset>
</template>
