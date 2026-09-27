<!-- Rangfolge der Klassen und Prüfprofile (tastaturbedienbar), mit Vorschau „weicht zuerst“. -->
<script setup lang="ts">
import { computed } from 'vue'
import { runnerNurLesen, runnerPrioritaetZeilen, runnerWeichtZuerstText, type RunnerController, type RunnerData, type RunnerMessageKey, type Translate } from '@auditcore/ui-core'
import FaButton from '../../base/FaButton.vue'

const props = defineProps<{ state: RunnerData; controller: RunnerController; t: Translate<RunnerMessageKey>; uid: string }>()
const zeilen = computed(() => runnerPrioritaetZeilen(props.state, props.t))
const weichtZuerst = computed(() => runnerWeichtZuerstText(props.state, props.t))
const nurLesen = computed(() => runnerNurLesen(props.state))

function verdraengbar(index: number, event: Event): void {
  props.controller.prioritaet(index, { verdraengbar: (event.target as HTMLInputElement).checked })
}

function minimum(index: number, event: Event): void {
  props.controller.prioritaet(index, { min: Number((event.target as HTMLInputElement).value) || 0 })
}
</script>

<template>
  <p class="fa-runner__muted">{{ t('prioritaetenHinweis') }}</p>
  <p v-if="!zeilen.length" class="fa-runner__muted">{{ t('keinePrioritaeten') }}</p>
  <ol v-else class="fa-runner__prioritaeten">
    <li v-for="zeile in zeilen" :key="zeile.klasse" class="fa-runner__prioritaet">
      <span class="fa-runner__rang">{{ zeile.rangText }}</span>
      <strong class="fa-runner__klasse">{{ zeile.klasse }}</strong>
      <FaButton size="sm" icon="chevron-up" icon-only :label="zeile.hoch" :disabled="nurLesen || zeile.ersteZeile" @click="controller.verschiebe(zeile.index, -1)" />
      <FaButton size="sm" icon="chevron-down" icon-only :label="zeile.runter" :disabled="nurLesen || zeile.letzteZeile" @click="controller.verschiebe(zeile.index, 1)" />
      <span class="fa-runner__feld fa-runner__feld--schalter">
        <input :id="`${uid}-prio-${zeile.index}-verdraengbar`" type="checkbox" :checked="zeile.verdraengbar" :disabled="nurLesen" @change="verdraengbar(zeile.index, $event)">
        <label :for="`${uid}-prio-${zeile.index}-verdraengbar`">{{ t('verdraengbar') }}</label>
      </span>
      <span class="fa-runner__feld fa-runner__feld--schalter">
        <label :for="`${uid}-prio-${zeile.index}-min`">{{ t('mindestens') }}</label>
        <input :id="`${uid}-prio-${zeile.index}-min`" class="fa-runner__eingabe fa-runner__schmal" type="number" min="0" :value="String(zeile.min)" :disabled="nurLesen" @input="minimum(zeile.index, $event)">
      </span>
    </li>
  </ol>
  <p v-if="weichtZuerst" class="fa-runner__muted">{{ weichtZuerst }}</p>
</template>
