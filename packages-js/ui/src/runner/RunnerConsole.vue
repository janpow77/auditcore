<!-- RunnerConsole: Status, Einstellungen, Werkzeuge und Prioritäten eines Rechners mit auditcore_runner; Logik im Kern (createRunnerController). -->
<script setup lang="ts">
import { computed, watch } from 'vue'
import { createRunnerController, runnerHinweise, runnerMessages, runnerMeta, runnerNachbarTab, runnerTabs, type RunnerAnsicht, type RunnerPort } from '@auditcore/ui-core'
import { useId } from '../composables/useId'
import { useStore } from '../composables/useStore'
import { useI18n, type Locale } from '../i18n'
import RunnerProfileForm from './components/RunnerProfileForm.vue'
import RunnerStatusPanel from './components/RunnerStatusPanel.vue'
import RunnerToolsPanel from './components/RunnerToolsPanel.vue'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createRunnerRestPort({ baseUrl: '/api' })`; hat Vorrang vor `api`. */
  port?: RunnerPort | null
  /** Basis-URL der JSON-API von `auditcore-runner ui` (Web Component: Attribut `api`). */
  api?: string
  /** Bereich beim Öffnen. */
  ansicht?: RunnerAnsicht
  locale?: Locale
}>(), { port: null, api: '', ansicht: 'status', locale: undefined })

const emit = defineEmits<{
  applied: [version: number]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(runnerMessages, () => props.locale)
const uid = useId('fa-runner')
const controller = createRunnerController({
  port: () => props.port,
  api: () => props.api,
  callbacks: () => ({
    applied: (version) => emit('applied', version),
    failed: (message) => emit('error', message),
  }),
})
controller.zeige(props.ansicht)
const state = useStore(controller.store)
const tabs = computed(() => runnerTabs(state.value, t))
const meta = computed(() => runnerMeta(state.value, t))
const hinweise = computed(() => runnerHinweise(state.value, t))

watch(() => [props.port, props.api], () => void controller.load(), { immediate: true })

function tabTaste(event: KeyboardEvent): void {
  const richtung = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0
  if (!richtung) return
  event.preventDefault()
  const next = runnerNachbarTab(state.value.ansicht, richtung)
  controller.zeige(next)
  document.getElementById(`${uid}-tab-${next}`)?.focus()
}
</script>

<template>
  <section class="fa-runner" :lang="active" :aria-label="t('title')">
    <header class="fa-runner__kopf">
      <h2 class="fa-runner__titel">{{ t('title') }}</h2>
      <p v-if="meta" class="fa-runner__meta">{{ meta }}</p>
    </header>
    <div class="fa-runner__reiter" role="tablist" :aria-label="t('tabs')" @keydown="tabTaste">
      <button
        v-for="tab in tabs"
        :id="`${uid}-tab-${tab.id}`"
        :key="tab.id"
        type="button"
        role="tab"
        class="fa-runner__tab"
        :aria-selected="tab.selected ? 'true' : 'false'"
        :aria-controls="`${uid}-panel`"
        :tabindex="tab.selected ? 0 : -1"
        @click="controller.zeige(tab.id)"
      >{{ tab.label }}</button>
    </div>
    <p v-if="state.busy" class="fa-runner__muted" role="status">{{ state.busy === 'load' ? t('loading') : t('working') }}</p>
    <p v-if="state.error" class="fa-runner__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <p v-if="state.meldung" :class="['fa-runner__meldung', `fa-runner__meldung--${state.meldung.ton}`]" role="status">{{ t(state.meldung.key, state.meldung.params) }}</p>
    <div :id="`${uid}-panel`" class="fa-runner__panel" role="tabpanel" :aria-labelledby="`${uid}-tab-${state.ansicht}`" tabindex="0">
      <ul v-if="hinweise.length" class="fa-runner__hinweise">
        <li v-for="hinweis in hinweise" :key="hinweis.text" :class="['fa-runner__hinweis', `fa-runner__hinweis--${hinweis.ton}`]">{{ hinweis.text }}</li>
      </ul>
      <RunnerStatusPanel v-if="state.ansicht === 'status'" :state="state" :controller="controller" :t="t" />
      <RunnerToolsPanel v-else-if="state.ansicht === 'werkzeuge'" :state="state" :controller="controller" :t="t" />
      <RunnerProfileForm v-else :state="state" :controller="controller" :t="t" :uid="uid" />
    </div>
  </section>
</template>
