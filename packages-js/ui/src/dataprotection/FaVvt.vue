<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { provideLocale, useI18n, type Locale } from '../i18n'
import { downloadText, printHtml } from '../synopsis/useSynopsisExport'
import VvtActivityDetail from './components/VvtActivityDetail.vue'
import VvtActivityList from './components/VvtActivityList.vue'
import VvtCover from './components/VvtCover.vue'
import VvtHistory from './components/VvtHistory.vue'
import VvtIssues from './components/VvtIssues.vue'
import VvtStatusBar from './components/VvtStatusBar.vue'
import { dataprotectionMessages } from './messages'
import { editedBy, emptyActivity, withActivity, withDepartments, withField, withoutActivity, withPerson } from './registerView'
import { statusLabel, type DataProtectionError } from './requests'
import type { DataProtectionPort, FieldValue, Person, VersionView } from './types'
import { useVvt, type VvtExport, type VvtExportFormat } from './useVvt'

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
const state = useVvt(() => props.port, {
  onSaved: (version: VersionView) => {
    state.notice.value = t('saved', { version: version.version, revision: version.revision })
    emit('draft-saved', { version: version.version, revision: version.revision })
  },
  onReleased: (version: VersionView) => {
    state.notice.value = t('released', { version: version.version })
    emit('released', { version: version.version })
  },
  onError: (error) => emit('error', error),
  networkMessage: (message) => t('networkError', { message }),
})
const { profile, register, showing, version, content, issues, editing, dirty, busy, error, notice } = state
const selected = ref<number | null>(null)
const history = ref(false)
const columns = computed(() => profile.value?.register.columns ?? [])
const activity = computed(() => (selected.value === null ? null : content.value.taetigkeiten[selected.value] ?? null))
const fourEyes = computed(() => editedBy(register.value?.draft ?? null, props.actor))

watch(() => props.port, async (port) => {
  if (port) await state.load(props.editable)
  if (selected.value === null && content.value.taetigkeiten.length) selected.value = 0
}, { immediate: true })

function changeField(key: string, value: FieldValue): void {
  if (selected.value !== null) state.update(withField(content.value, selected.value, key, value))
}

function addActivity(department: string): void {
  state.update(withActivity(content.value, emptyActivity(columns.value, department)))
  selected.value = content.value.taetigkeiten.length - 1
}

function removeActivity(): void {
  if (selected.value === null) return
  state.update(withoutActivity(content.value, selected.value))
  selected.value = content.value.taetigkeiten.length ? 0 : null
}

function changePerson(part: 'verantwortlicher' | 'dsb', person: Person): void {
  state.update(withPerson(content.value, part, person))
}

function runExport(format: VvtExportFormat): void {
  const label = version.value ? t('versionLabel', { version: version.value.version, status: statusLabel(t, version.value.status) }) : t('noVersion')
  const texts = {
    yes: t('yes'), no: t('no'), empty: t('empty'), title: t('vvtTitle'), department: t('colDepartment'),
    withoutDepartment: t('withoutDepartment'), controller: t('controller'), dpo: t('dpo'), version: t('colVersion'),
    issues: t('issuesExport'), noIssues: t('noIssues'), required: t('blockingLabel'), hint: t('hintLabel'),
    field: t('field'), content: t('content'), generated: t('generated'),
  }
  const payload = state.build(format, texts, label, active.value)
  if (format === 'print') printHtml(payload.content)
  else downloadText(payload.content, payload.filename, payload.mimeType)
  notice.value = t('exported', { filename: payload.filename })
  emit('exported', payload)
}
</script>

<template>
  <section class="fa-dataprotection fa-vvt" :aria-busy="!!busy" data-testid="vvt">
    <header class="fa-dataprotection__header">
      <h2>{{ t('vvtTitle') }} <span class="fa-dataprotection__muted">{{ t('vvtNorm') }}</span></h2>
      <span v-if="profile" class="fa-dataprotection__muted">{{ t('profile', { id: profile.profile.id, version: profile.profile.version }) }}</span>
    </header>
    <p v-if="!port" class="fa-dataprotection__alert" role="alert">{{ t('noPort') }}</p>
    <p v-if="error" class="fa-dataprotection__alert" role="alert">{{ error.message }}</p>
    <p class="fa-dataprotection__live" aria-live="polite">{{ busy === 'load' ? t('loading') : notice }}</p>
    <VvtStatusBar
      :state="register"
      :version="version"
      :showing="showing"
      :editing="editing"
      :editable="editable"
      :dirty="dirty"
      :four-eyes="fourEyes"
      :busy="busy"
      :history="history"
      @save="state.save"
      @discard="state.discard"
      @release="state.release"
      @new-draft="state.startDraft"
      @show="state.show"
      @toggle-history="history = !history"
      @export="runExport"
    />
    <VvtHistory v-if="history" :versions="register?.versions ?? []" />
    <VvtCover
      :content="content"
      :issues="issues"
      :editing="editing"
      @person-change="changePerson"
      @departments-change="state.update(withDepartments(content, $event))"
    />
    <div class="fa-vvt__layout">
      <VvtActivityList :content="content" :issues="issues" :selected="selected" :editing="editing" @activity-select="selected = $event" @add="addActivity" />
      <VvtActivityDetail
        v-if="activity"
        :activity="activity"
        :columns="columns"
        :issues="issues"
        :departments="content.referate"
        :editing="editing"
        @field-change="changeField"
        @remove="removeActivity"
      />
      <p v-else class="fa-dataprotection__panel fa-dataprotection__muted">{{ t('selectActivity') }}</p>
    </div>
    <VvtIssues :issues="issues" />
  </section>
</template>
