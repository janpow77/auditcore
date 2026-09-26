<script setup lang="ts">
import { computed, watch } from 'vue'
import { deliverExport, vvtFourEyes, type VvtExportFormat } from '@flowaudit/ui-core'
import { provideLocale, useI18n, type Locale } from '../i18n'
import VvtActivityDetail from './components/VvtActivityDetail.vue'
import VvtActivityList from './components/VvtActivityList.vue'
import VvtCover from './components/VvtCover.vue'
import VvtHistory from './components/VvtHistory.vue'
import VvtIssues from './components/VvtIssues.vue'
import VvtStatusBar from './components/VvtStatusBar.vue'
import { dataprotectionMessages, type DataProtectionError, type DataProtectionPort } from './core'
import { useVvt, type VvtExport } from './useVvt'

const props = withDefaults(defineProps<{
  /** Datenzugang (Vertrag dataprotection_ui/1), z. B. `createDataProtectionRestPort({ baseUrl: '/api/dataprotection' })`. */
  port?: DataProtectionPort | null
  /** Kennung der angemeldeten Person; nur für den Vier-Augen-Hinweis, geprüft wird auf dem Server. */
  actor?: string
  /** `false`: nur Ansicht, keine Bearbeitung und Freigabe. */
  editable?: boolean
  locale?: Locale
}>(), { port: null, actor: '', editable: true, locale: undefined })

const emit = defineEmits<{
  'draft-saved': [detail: { version: number; revision: number }]
  released: [detail: { version: number }]
  exported: [detail: VvtExport]
  error: [detail: DataProtectionError]
}>()

const { t, locale: active } = useI18n(dataprotectionMessages, () => props.locale)
provideLocale(active)
const { controller, state, view } = useVvt(() => props.port, () => t, {
  onSaved: (version) => emit('draft-saved', { version: version.version, revision: version.revision }),
  onReleased: (version) => emit('released', { version: version.version }),
  onError: (error) => emit('error', error),
})
const columns = computed(() => state.value.profile?.register.columns ?? [])
const content = computed(() => view.value.content)
const selected = computed(() => state.value.selected)
const activity = computed(() => (selected.value === null ? null : content.value.taetigkeiten[selected.value] ?? null))
const fourEyes = computed(() => vvtFourEyes(state.value, props.actor))

watch(() => props.port, async (port) => {
  if (port) await controller.load(props.editable)
}, { immediate: true })

function runExport(format: VvtExportFormat): void {
  const payload = controller.exportAs(format, active.value)
  deliverExport(payload)
  emit('exported', payload)
}
</script>

<template>
  <section class="fa-dataprotection fa-vvt" :aria-busy="!!state.busy" data-testid="vvt">
    <header class="fa-dataprotection__header">
      <h2>{{ t('vvtTitle') }} <span class="fa-dataprotection__muted">{{ t('vvtNorm') }}</span></h2>
      <span v-if="state.profile" class="fa-dataprotection__muted">{{ t('profile', { id: state.profile.profile.id, version: state.profile.profile.version }) }}</span>
    </header>
    <p v-if="!port" class="fa-dataprotection__alert" role="alert">{{ t('noPort') }}</p>
    <p v-if="state.error" class="fa-dataprotection__alert" role="alert">{{ state.error.message }}</p>
    <p class="fa-dataprotection__live" aria-live="polite">{{ state.busy === 'load' ? t('loading') : state.notice }}</p>
    <VvtStatusBar
      :state="state.register"
      :version="view.version"
      :showing="state.showing"
      :editing="view.editing"
      :editable="editable"
      :dirty="view.dirty"
      :four-eyes="fourEyes"
      :busy="state.busy"
      :history="state.history"
      @save="controller.save"
      @discard="controller.discard"
      @release="controller.release"
      @new-draft="controller.startDraft"
      @show="controller.show"
      @toggle-history="controller.toggleHistory"
      @export="runExport"
    />
    <VvtHistory v-if="state.history" :versions="state.register?.versions ?? []" />
    <VvtCover
      :content="content"
      :issues="view.issues"
      :editing="view.editing"
      @person-change="controller.changePerson"
      @departments-change="controller.changeDepartments"
    />
    <div class="fa-vvt__layout">
      <VvtActivityList :content="content" :issues="view.issues" :selected="selected" :editing="view.editing" @activity-select="controller.select" @add="controller.addActivity" />
      <VvtActivityDetail
        v-if="activity"
        :activity="activity"
        :columns="columns"
        :issues="view.issues"
        :departments="content.referate"
        :editing="view.editing"
        @field-change="controller.changeField"
        @remove="controller.removeActivity"
      />
      <p v-else class="fa-dataprotection__panel fa-dataprotection__muted">{{ t('selectActivity') }}</p>
    </div>
    <VvtIssues :issues="view.issues" />
  </section>
</template>
