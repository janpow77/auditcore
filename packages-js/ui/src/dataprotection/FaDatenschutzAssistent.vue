<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { draftOf, questionFieldId, type AssistantMode, type AssistantPort, type AssistantTab, type WorkspaceOverview } from '@auditcore/ui-core'
import { provideLocale, useI18n, type Locale } from '../i18n'
import AssistantChecklist from './components/AssistantChecklist.vue'
import AssistantQuestion from './components/AssistantQuestion.vue'
import AssistantStatus from './components/AssistantStatus.vue'
import AssistantSteps from './components/AssistantSteps.vue'
import { dataprotectionMessages, prefixedLabel, type DataProtectionError } from './core'
import { useAssistant } from './useAssistant'

const props = withDefaults(defineProps<{
  /** Datenzugang, z. B. `createAssistantRestPort({ baseUrl: '/api/dataprotection' })`. */
  port?: AssistantPort | null
  /** Kennung der Verarbeitungstätigkeit im Verzeichnis. */
  activityId?: string
  locale?: Locale
}>(), { port: null, activityId: '', locale: undefined })

const emit = defineEmits<{ change: [detail: WorkspaceOverview]; error: [detail: DataProtectionError] }>()
const { t, locale: active } = useI18n(dataprotectionMessages, () => props.locale)
provideLocale(active)
const { controller, state, view } = useAssistant(() => props.port, () => props.activityId, () => t, {
  onChange: (overview) => emit('change', overview),
  onError: (error) => emit('error', error),
})
const heading = ref<HTMLElement | null>(null)
const overview = computed(() => state.value.overview)
const busy = computed(() => !!state.value.busy)
const errors = computed(() => Object.entries(state.value.fieldErrors))
const TABS: AssistantTab[] = ['assistent', 'checkliste', 'status']
const TAB_TEXT = { assistent: 'tabAssistant', checkliste: 'tabChecklist', status: 'tabStatus' } as const

watch(() => [props.port, props.activityId], async () => {
  if (props.port && props.activityId) await controller.load()
}, { immediate: true })

// Fokus auf die Schrittüberschrift, wenn der Schritt wechselt (Tastatur, Screenreader).
watch(() => view.value.step?.id, async (now, before) => {
  if (before && now !== before) { await nextTick(); heading.value?.focus() }
})

function setMode(event: Event): void {
  void controller.setMode((event.target as HTMLSelectElement).value as AssistantMode)
}
</script>

<template>
  <section class="fa-dataprotection fa-assistant" :aria-busy="busy" data-testid="assistant">
    <header class="fa-dataprotection__header">
      <h2>{{ t('assistantTitle') }}</h2>
      <span v-if="overview" class="fa-dataprotection__muted">{{ t('profile', { id: overview.profil.id, version: overview.profil.version }) }}</span>
    </header>
    <p v-if="!port" class="fa-dataprotection__alert" role="alert">{{ t('noPort') }}</p>
    <p v-else-if="!activityId" class="fa-dataprotection__alert" role="alert">{{ t('noActivity') }}</p>
    <p v-if="state.error && !errors.length" class="fa-dataprotection__alert" role="alert">{{ state.error.message }}</p>
    <p class="fa-dataprotection__live" aria-live="polite">{{ state.busy === 'load' ? t('loading') : state.notice }}</p>
    <template v-if="overview">
      <p class="fa-dataprotection__muted">{{ t('assistantIntro') }}</p>
      <div class="fa-assistant__tabs" role="tablist" :aria-label="t('tabsLabel')">
        <button v-for="tab in TABS" :key="tab" type="button" role="tab" :aria-selected="state.tab === tab" @click="controller.setTab(tab)">{{ t(TAB_TEXT[tab]) }}</button>
      </div>
      <div v-if="errors.length" class="fa-dataprotection__alert" role="alert">
        {{ t('errorSummary') }}
        <ul><li v-for="[id, message] in errors" :key="id"><a :href="`#${questionFieldId({ id })}`">{{ t('goToField', { id }) }}</a>: {{ message }}</li></ul>
      </div>
      <div v-if="state.tab === 'assistent'" class="fa-assistant__layout" role="tabpanel">
        <div>
          <label>{{ t('modeLabel') }}
            <select :value="view.mode" :disabled="busy" @change="setMode">
              <option value="gefuehrt">{{ t('mode_gefuehrt') }}</option>
              <option value="frei">{{ t('mode_frei') }}</option>
            </select>
          </label>
          <p class="fa-dataprotection__muted">{{ t('stepsDone', { done: view.completed, total: view.steps.length }) }}</p>
          <AssistantSteps :view="view" :busy="busy" @select="controller.goTo" />
        </div>
        <div v-if="view.step">
          <h3 ref="heading" tabindex="-1">{{ t('stepOf', { position: view.position, total: view.steps.length }) }}: {{ view.step.title }}</h3>
          <p class="fa-dataprotection__muted">{{ view.step.goal }} <span class="fa-assistant__badge">{{ prefixedLabel(t, 'stepStatus', view.step.status) }}</span></p>
          <p v-if="overview.assistent.hidden_answers.length" class="fa-dataprotection__alert fa-dataprotection__alert--info">{{ t('hiddenAnswers', { ids: overview.assistent.hidden_answers.join(', ') }) }}</p>
          <AssistantQuestion
            v-for="question in view.step.questions"
            :key="question.id"
            :question="question"
            :draft="draftOf(state, question)"
            :error="state.fieldErrors[question.id]"
            :busy="busy"
            @change="(draft) => controller.setDraft(question.id, draft)"
            @save="controller.answer(question.id)"
            @confirm="controller.confirm(question.id)"
          />
          <div class="fa-assistant__nav">
            <button type="button" :disabled="busy || !view.previous" @click="controller.previous()">{{ t('previousStep') }}</button>
            <button type="button" :disabled="busy || !view.next" @click="controller.next()">{{ t('nextStep') }}</button>
          </div>
        </div>
      </div>
      <AssistantChecklist v-else-if="state.tab === 'checkliste'" role="tabpanel" :items="overview.pruefpunkte" :busy="busy" @change="controller.changeItem" />
      <AssistantStatus v-else role="tabpanel" :axes="overview.status" :gates="overview.sperren" />
      <section class="fa-dataprotection__panel" :aria-label="t('tasksTitle', { count: overview.assistent.tasks.length })">
        <h3>{{ t('tasksTitle', { count: overview.assistent.tasks.length }) }}</h3>
        <ul>
          <li v-for="task in overview.assistent.tasks" :key="task.question">{{ task.number || task.question }} – {{ prefixedLabel(t, 'task', task.kind) }}</li>
        </ul>
      </section>
    </template>
  </section>
</template>
