<script setup lang="ts">
import { computed, watch } from 'vue'
import { dsfaReadonly, dsfaTabs } from '@auditcore/ui-core'
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
import { dataprotectionMessages, statusLabel, statusTone, type DataProtectionError, type DataProtectionPort } from './core'
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
const { controller, state, derived } = useDsfa(() => props.port, () => t, {
  onChanged: (step, view) => emit('assessment-change', { step, id: view.id, version: view.version, status: view.status }),
  onError: (error) => emit('error', error),
})
const view = computed(() => state.value.view)
const profile = computed(() => state.value.profile)
const survey = computed(() => state.value.survey)
const proposal = computed(() => derived.value.proposal)
const readonly = computed(() => dsfaReadonly(state.value, props.editable))
const tabs = computed(() => dsfaTabs(t))

watch(() => props.port, async (port) => {
  if (port) await controller.connect(props.activityId)
}, { immediate: true })
</script>

<template>
  <section class="fa-dataprotection fa-dsfa" :aria-busy="!!state.busy" data-testid="dsfa">
    <header class="fa-dataprotection__header">
      <h2>{{ t('dsfaTitle') }} <span class="fa-dataprotection__muted">{{ t('dsfaNorm') }}</span></h2>
      <span v-if="profile" class="fa-dataprotection__muted">{{ t('profile', { id: profile.profile.id, version: profile.profile.version }) }}</span>
    </header>
    <p v-if="!port" class="fa-dataprotection__alert" role="alert">{{ t('noPort') }}</p>
    <p v-if="state.error" class="fa-dataprotection__alert" role="alert">{{ state.error.message }}</p>
    <p class="fa-dataprotection__live" aria-live="polite">{{ state.busy === 'load' ? t('loading') : state.notice }}</p>
    <DsfaOverview :rows="state.rows" :profile="profile" :selected="view?.id ?? null" :editable="editable" :busy="!!state.busy" @open="controller.open" @start="controller.start" />
    <template v-if="view && profile && survey && proposal">
      <div class="fa-dataprotection__panel fa-dataprotection__bar" data-testid="dsfa-head">
        <h3>{{ view.activity_name }}</h3>
        <FaBadge :tone="statusTone(view.status)">{{ t('versionLabel', { version: view.version, status: statusLabel(t, view.status) }) }}</FaBadge>
        <FaBadge v-if="derived.dirty" tone="accent">{{ t('unsaved') }}</FaBadge>
        <div class="fa-dataprotection__actions">
          <FaButton v-if="!readonly" variant="primary" size="sm" :disabled="!derived.dirty" :loading="state.busy === 'saved'" :label="t('save')" @click="controller.save" />
          <FaButton v-if="editable && view.locked && view.status === 'freigegeben'" size="sm" :label="t('reassess')" @click="controller.reassess" />
          <FaButton variant="ghost" size="sm" :label="t('reportHtml')" @click="controller.exportReport('html')" />
          <FaButton variant="ghost" size="sm" :label="t('reportMarkdown')" @click="controller.exportReport('markdown')" />
        </div>
        <p v-if="view.locked" class="fa-dataprotection__muted">{{ t('lockedNotice') }}</p>
      </div>
      <DsfaTabs :tabs="tabs" :active="state.tab" :label="t('steps')" @tab-change="controller.setTab">
        <DsfaScreening v-if="state.tab === 'screening'" :profile="profile" :survey="survey" :proposal="proposal" :preview="derived.showPreview" :readonly="readonly" @survey-change="controller.edit" />
        <DsfaRisk v-else-if="state.tab === 'risk'" :profile="profile" :survey="survey" :proposal="proposal" :preview="derived.showPreview" :readonly="readonly" @survey-change="controller.edit" />
        <template v-else>
          <DsfaProposal :profile="profile" :proposal="proposal" :preview="derived.showPreview" :open-points="view.locked ? [] : view.open_points" />
          <DsfaDecision
            :profile="profile"
            :view="view"
            :proposal="proposal"
            :dirty="derived.dirty"
            :actor="actor"
            :busy="state.busy"
            @decide="controller.decide"
            @dpo-request="controller.requestDpo"
            @release="controller.release"
          />
        </template>
      </DsfaTabs>
      <DsfaVersions :versions="view.versions" :profile="profile" :current="view.id" @open="controller.open" />
    </template>
  </section>
</template>
