<!-- Name einer Runner-Klasse ändern (Prüfung wie im Backend: a–z, 0–9, Bindestrich, höchstens 31 Zeichen). -->
<script setup lang="ts">
import type { RunnerController, RunnerKlassenName, RunnerMessageKey, Translate } from '@auditcore/ui-core'
import FaButton from '../../base/FaButton.vue'

const props = defineProps<{ klasse: RunnerKlassenName; controller: RunnerController; t: Translate<RunnerMessageKey>; uid: string; nurLesen: boolean }>()
const id = `${props.uid}-klasse-${props.klasse.alt}-name`

function eingabe(event: Event): void {
  props.controller.klassenNameEingabe(props.klasse.alt, (event.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="fa-runner__feld fa-runner__klassenname">
    <label :for="id">{{ t('klasseName') }}</label>
    <span class="fa-runner__aktionen">
      <input
        :id="id"
        class="fa-runner__eingabe"
        type="text"
        maxlength="31"
        :value="klasse.wert"
        :disabled="nurLesen"
        :aria-invalid="klasse.fehler ? 'true' : undefined"
        :aria-describedby="klasse.fehler ? `${id}-fehler` : undefined"
        @input="eingabe"
      >
      <FaButton size="sm" :disabled="nurLesen || !klasse.geaendert" @click="controller.klasseUmbenennen(klasse.alt)">{{ t('umbenennen') }}</FaButton>
    </span>
    <p v-if="klasse.fehler" :id="`${id}-fehler`" class="fa-runner__feldfehler">{{ klasse.fehler }}</p>
  </div>
</template>
