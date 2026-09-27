<!-- Ergebnis nach Prüfen/Anwenden: Konflikt mit beiden Ständen oder Vorschau (Diffs, Schritte, root-Befehl). -->
<script setup lang="ts">
import { computed } from 'vue'
import { runnerVorschau, runnerWert, type RunnerController, type RunnerData, type RunnerMessageKey, type Translate } from '@auditcore/ui-core'
import FaBadge from '../../base/FaBadge.vue'
import FaButton from '../../base/FaButton.vue'

const props = defineProps<{ state: RunnerData; controller: RunnerController; t: Translate<RunnerMessageKey> }>()
const vorschau = computed(() => runnerVorschau(props.state))
const konfliktQuelle = computed(() => String(runnerWert(props.state.konflikt?.gespeichert.profil, ['aenderung', 'quelle']) ?? '–'))
</script>

<template>
  <section v-if="state.konflikt" class="fa-runner__konflikt" role="alert">
    <p>{{ t('konflikt', { meldung: state.konflikt.meldung }) }}</p>
    <table class="fa-runner__tabelle">
      <thead>
        <tr>
          <th scope="col">{{ t('konfliktFeld') }}</th>
          <th scope="col">{{ t('konfliktEntwurf') }}</th>
          <th scope="col">{{ t('konfliktGespeichert', { quelle: konfliktQuelle }) }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="unterschied in state.konflikt.unterschiede" :key="unterschied.pfad">
          <th scope="row"><code>{{ unterschied.pfad }}</code></th>
          <td><code>{{ unterschied.entwurf }}</code></td>
          <td><code>{{ unterschied.gespeichert }}</code></td>
        </tr>
      </tbody>
    </table>
    <div class="fa-runner__aktionen">
      <FaButton @click="controller.gespeichertUebernehmen()">{{ t('gespeichertUebernehmen') }}</FaButton>
      <FaButton variant="primary" @click="controller.entwurfTrotzdemAnwenden()">{{ t('entwurfAnwenden') }}</FaButton>
    </div>
  </section>
  <section v-if="vorschau" class="fa-runner__vorschau" :aria-label="t('vorschau')">
    <h3 class="fa-runner__zwischen">{{ t('vorschau') }} <FaBadge :tone="vorschau.gueltig ? 'success' : 'danger'">{{ vorschau.gueltig ? t('gueltig') : t('ungueltig') }}</FaBadge></h3>
    <p v-if="!vorschau.aenderungen.length" class="fa-runner__muted">{{ t('keineAenderung') }}</p>
    <details v-for="aenderung in vorschau.aenderungen" :key="aenderung.datei" class="fa-runner__diff">
      <summary>{{ aenderung.datei }}</summary>
      <pre>{{ aenderung.diff }}</pre>
    </details>
    <template v-if="vorschau.schritte.length">
      <h4 class="fa-runner__zwischen">{{ t('schritte') }}</h4>
      <ol class="fa-runner__schritte">
        <li v-for="schritt in vorschau.schritte" :key="schritt">{{ schritt }}</li>
      </ol>
    </template>
    <template v-if="vorschau.rootBefehl">
      <p class="fa-runner__muted">{{ t('rootBefehl') }}</p>
      <pre class="fa-runner__befehl"><code>{{ vorschau.rootBefehl }}</code></pre>
    </template>
  </section>
</template>
