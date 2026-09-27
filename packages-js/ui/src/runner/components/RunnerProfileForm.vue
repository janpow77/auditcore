<!-- Formular der Bereiche „Einstellungen“ und „Prioritäten“: Fehler, Felder bzw. Rangfolge, Aktionen, Ergebnis. -->
<script setup lang="ts">
import { computed } from 'vue'
import { runnerIstGeaendert, runnerNurLesen, runnerProbleme, type RunnerController, type RunnerData, type RunnerMessageKey, type Translate } from '@auditcore/ui-core'
import FaBadge from '../../base/FaBadge.vue'
import FaButton from '../../base/FaButton.vue'
import RunnerFields from './RunnerFields.vue'
import RunnerPriorityList from './RunnerPriorityList.vue'
import RunnerReview from './RunnerReview.vue'

const props = defineProps<{ state: RunnerData; controller: RunnerController; t: Translate<RunnerMessageKey>; uid: string }>()
const probleme = computed(() => runnerProbleme(props.state))
const nurLesen = computed(() => runnerNurLesen(props.state))
const geaendert = computed(() => runnerIstGeaendert(props.state))
</script>

<template>
  <form class="fa-runner__formular" novalidate @submit.prevent="controller.pruefen()">
    <ul v-if="probleme.length" class="fa-runner__probleme" :aria-label="t('probleme')">
      <li v-for="problem in probleme" :key="`${problem.feld}-${problem.meldung}`">{{ problem.feld }}: {{ problem.meldung }}</li>
    </ul>
    <RunnerFields v-if="state.ansicht === 'einstellungen'" :state="state" :controller="controller" :t="t" :uid="uid" />
    <RunnerPriorityList v-else :state="state" :controller="controller" :t="t" :uid="uid" />
    <div class="fa-runner__aktionen">
      <FaButton type="submit" :disabled="nurLesen" :loading="state.busy === 'pruefen'">{{ t('pruefen') }}</FaButton>
      <FaButton variant="primary" :disabled="nurLesen || !geaendert" :loading="state.busy === 'anwenden'" @click="controller.anwenden()">{{ t('anwenden') }}</FaButton>
      <FaButton :disabled="!geaendert" @click="controller.verwerfen()">{{ t('verwerfen') }}</FaButton>
      <FaBadge v-if="geaendert" tone="warning">{{ t('ungespeichert') }}</FaBadge>
    </div>
    <RunnerReview :state="state" :controller="controller" :t="t" />
  </form>
</template>
