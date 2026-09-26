<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import FaButton from '../base/FaButton.vue'
import { provideLocale, useI18n, type Locale } from '../i18n'
import DsfaDecision from './components/DsfaDecision.vue'
import DsfaOverview from './components/DsfaOverview.vue'
import DsfaProposal from './components/DsfaProposal.vue'
import DsfaRisk from './components/DsfaRisk.vue'
import DsfaScreening from './components/DsfaScreening.vue'
import DsfaTabs from './components/DsfaTabs.vue'
import DsfaVersions from './components/DsfaVersions.vue'
import { dataprotectionMessages, type DataProtectionKey } from './messages'
import { statusTone } from './registerView'
import { statusLabel, type DataProtectionError } from './requests'
import type { AssessmentView, DataProtectionPort } from './types'
import { useDsfa, type DsfaStep } from './useDsfa'

const props = withDefaults(defineProps<{
  /** Datenzugang (Vertrag dataprotection_ui/1), z. B. `createDataProtectionRestPort({ baseUrl: '/api/dataprotection' })`. */
  port?: DataProtectionPort | null
  /** Beim Laden zu öffnende Tätigkeit (Kennung aus dem Verzeichnis). */
  activityId?: string
  /** Kennung der angemeldeten Person; nur für den Vier-Augen-Hinweis, geprüft wird auf dem Server. */
  actor?: string
  editable?: boolean
  locale?: Locale
}>(), { port: null, activityId: '', actor: '', editable: true, locale: undefined })

const emit = defineEmits<{
  'assessment-change': [detail: { step: DsfaStep; id: string; version: number; status: string }]
  error: [detail: DataProtectionError]
}>()

const { t, locale: active } = useI18n(dataprotectionMessages, () => props.locale)
provideLocale(active)
const NOTICES: Readonly<Record<DsfaStep, DataProtectionKey>> = {
  saved: 'assessmentSaved', decided: 'decisionSaved', dpo: 'dpoSaved', released: 'assessmentReleased', started: 'assessmentSaved',
}
const state = useDsfa(() => props.port, {
  onChanged: (step: DsfaStep, view: AssessmentView) => {
    state.notice.value = t(NOTICES[step], { revision: view.revision, version: view.version })
    emit('assessment-change', { step, id: view.id, version: view.version, status: view.status })
  },
  onError: (error) => emit('error', error),
  networkMessage: (message) => t('networkError', { message }),
})
const { profile, rows, view, survey, dirty, proposal, preview, busy, error, notice } = state
const tab = ref('screening')
const readonly = computed(() => !props.editable || !!view.value?.locked)
const showPreview = computed(() => dirty.value && !!preview.value)
const tabs = computed(() => [
  { key: 'screening', label: t('stepScreening') },
  { key: 'risk', label: t('stepRisk') },
  { key: 'result', label: t('stepResult') },
])

watch(() => props.port, async (port) => {
  if (!port) return
  await state.load()
  if (props.activityId) await state.openActivity(props.activityId)
}, { immediate: true })
</script>

<template>
  <section class="fa-dataprotection fa-dsfa" :aria-busy="!!busy" data-testid="dsfa">
    <header class="fa-dataprotection__header">
      <h2>{{ t('dsfaTitle') }} <span class="fa-dataprotection__muted">{{ t('dsfaNorm') }}</span></h2>
      <span v-if="profile" class="fa-dataprotection__muted">{{ t('profile', { id: profile.profile.id, version: profile.profile.version }) }}</span>
    </header>
    <p v-if="!port" class="fa-dataprotection__alert" role="alert">{{ t('noPort') }}</p>
    <p v-if="error" class="fa-dataprotection__alert" role="alert">{{ error.message }}</p>
    <p class="fa-dataprotection__live" aria-live="polite">{{ busy === 'load' ? t('loading') : notice }}</p>
    <DsfaOverview :rows="rows" :profile="profile" :selected="view?.id ?? null" :editable="editable" :busy="!!busy" @open="state.open" @start="state.start" />
    <template v-if="view && profile && survey && proposal">
      <div class="fa-dataprotection__panel fa-dataprotection__bar" data-testid="dsfa-head">
        <h3>{{ view.activity_name }}</h3>
        <FaBadge :tone="statusTone(view.status)">{{ t('versionLabel', { version: view.version, status: statusLabel(t, view.status) }) }}</FaBadge>
        <FaBadge v-if="dirty" tone="accent">{{ t('unsaved') }}</FaBadge>
        <div class="fa-dataprotection__actions">
          <FaButton v-if="!readonly" variant="primary" size="sm" :disabled="!dirty" :loading="busy === 'saved'" :label="t('save')" @click="state.save" />
          <FaButton v-if="editable && view.locked && view.status === 'freigegeben'" size="sm" :label="t('reassess')" @click="state.reassess" />
          <FaButton variant="ghost" size="sm" :label="t('reportHtml')" @click="state.exportReport('html')" />
          <FaButton variant="ghost" size="sm" :label="t('reportMarkdown')" @click="state.exportReport('markdown')" />
        </div>
        <p v-if="view.locked" class="fa-dataprotection__muted">{{ t('lockedNotice') }}</p>
      </div>
      <DsfaTabs :tabs="tabs" :active="tab" :label="t('steps')" @tab-change="tab = $event">
        <DsfaScreening v-if="tab === 'screening'" :profile="profile" :survey="survey" :proposal="proposal" :preview="showPreview" :readonly="readonly" @survey-change="state.edit" />
        <DsfaRisk v-else-if="tab === 'risk'" :profile="profile" :survey="survey" :proposal="proposal" :preview="showPreview" :readonly="readonly" @survey-change="state.edit" />
        <template v-else>
          <DsfaProposal :profile="profile" :proposal="proposal" :preview="showPreview" :open-points="view.locked ? [] : view.open_points" />
          <DsfaDecision
            :profile="profile"
            :view="view"
            :proposal="proposal"
            :dirty="dirty"
            :actor="actor"
            :busy="busy"
            @decide="state.decide"
            @dpo-request="state.requestDpo"
            @release="state.release"
          />
        </template>
      </DsfaTabs>
      <DsfaVersions :versions="view.versions" :profile="profile" :current="view.id" @open="state.open" />
    </template>
  </section>
</template>
