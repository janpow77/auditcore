<!-- Bereich „Status“ der Runner-Konsole: Überblick, Klassen, Hardware. -->
<script setup lang="ts">
import { computed } from 'vue'
import { runnerHardware, runnerHatWarteschlange, runnerKlassenZeilen, runnerUeberblick, type RunnerController, type RunnerData, type RunnerMessageKey, type Translate } from '@auditcore/ui-core'
import FaBadge from '../../base/FaBadge.vue'
import FaButton from '../../base/FaButton.vue'

const props = defineProps<{ state: RunnerData; controller: RunnerController; t: Translate<RunnerMessageKey> }>()
const ueberblick = computed(() => runnerUeberblick(props.state.status, props.t))
const klassen = computed(() => runnerKlassenZeilen(props.state.status))
const warteschlange = computed(() => runnerHatWarteschlange(props.state.status))
const hardware = computed(() => runnerHardware(props.state.status?.hardware))
</script>

<template>
  <template v-if="state.status">
    <h3 class="fa-runner__zwischen">{{ t('ueberblick') }}</h3>
    <dl class="fa-runner__daten">
      <div v-for="eintrag in ueberblick" :key="eintrag.label" class="fa-runner__datum"><dt>{{ eintrag.label }}</dt><dd>{{ eintrag.wert }}</dd></div>
    </dl>
    <table v-if="klassen.length" class="fa-runner__tabelle">
      <caption>{{ t('klassen') }}</caption>
      <thead>
        <tr>
          <th scope="col">{{ t('spalteKlasse') }}</th>
          <th scope="col">{{ t('spalteSoll') }}</th>
          <th scope="col">{{ t('spalteMax') }}</th>
          <th scope="col">{{ t('spalteInstanzen') }}</th>
          <th scope="col">{{ t('spalteRegistriert') }}</th>
          <th scope="col">{{ t('spalteBelegt') }}</th>
          <th v-if="warteschlange" scope="col">{{ t('spalteWarteschlange') }}</th>
          <th scope="col">{{ t('spalteGruende') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="zeile in klassen" :key="zeile.name">
          <th scope="row">{{ zeile.name }} <FaBadge v-if="!zeile.aktiv">{{ t('inaktiv') }}</FaBadge></th>
          <td>{{ zeile.soll }}</td>
          <td>{{ zeile.max }}</td>
          <td>{{ zeile.instanzen }}</td>
          <td>{{ zeile.registriert }}</td>
          <td>{{ zeile.belegt }}</td>
          <td v-if="warteschlange">{{ zeile.warteschlange }}</td>
          <td>{{ zeile.gruende }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else class="fa-runner__muted">{{ t('keineKlassen') }}</p>
    <h3 class="fa-runner__zwischen">{{ t('hardware') }}</h3>
    <dl class="fa-runner__daten">
      <div v-for="eintrag in hardware" :key="eintrag.label" class="fa-runner__datum"><dt>{{ eintrag.label }}</dt><dd>{{ eintrag.wert }}</dd></div>
    </dl>
  </template>
  <div class="fa-runner__aktionen">
    <FaButton icon="clock" :loading="state.busy === 'load'" @click="controller.load()">{{ t('refresh') }}</FaButton>
  </div>
</template>
