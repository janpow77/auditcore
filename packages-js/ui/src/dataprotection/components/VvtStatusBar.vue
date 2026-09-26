<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import FaButton from '../../base/FaButton.vue'
import { formatDate, useI18n } from '../../i18n'
import { dataprotectionMessages } from '../messages'
import { statusTone } from '../registerView'
import { statusLabel } from '../requests'
import type { RegisterState, VersionView } from '../types'
import type { VvtExportFormat } from '../useVvt'

const props = withDefaults(defineProps<{
  state: RegisterState | null
  version: VersionView | null
  showing: 'draft' | 'released'
  editing?: boolean
  editable?: boolean
  dirty?: boolean
  fourEyes?: boolean
  busy?: string | null
  history?: boolean
}>(), { editing: false, editable: true, dirty: false, fourEyes: false, busy: null, history: false })

const emit = defineEmits<{
  save: []
  discard: []
  release: []
  'new-draft': []
  show: [which: 'draft' | 'released']
  'toggle-history': []
  export: [format: VvtExportFormat]
}>()
const { t, locale } = useI18n(dataprotectionMessages)
const draft = computed(() => props.state?.draft ?? null)
const released = computed(() => props.state?.released ?? null)
const canRelease = computed(() => props.editable && props.showing === 'draft' && !!draft.value && !props.dirty && !props.fourEyes)
const releaseHint = computed(() => (props.dirty ? t('saveFirst') : props.fourEyes ? t('fourEyesHint') : ''))
const when = (value: string | null): string => formatDate(value, locale.value, true)
</script>

<template>
  <div class="fa-dataprotection__panel fa-dataprotection__bar" data-testid="vvt-status">
    <template v-if="version && !(editing && !draft)">
      <FaBadge :tone="statusTone(version.status)">{{ t('versionLabel', { version: version.version, status: statusLabel(t, version.status) }) }}</FaBadge>
      <span class="fa-dataprotection__muted">{{ t('createdBy', { person: version.created_by, date: when(version.created_at) }) }}</span>
      <span v-if="version.released_by" class="fa-dataprotection__muted">{{ t('releasedBy', { person: version.released_by, date: when(version.released_at) }) }}</span>
      <span class="fa-dataprotection__muted">{{ t('revision', { revision: version.revision }) }}</span>
    </template>
    <FaBadge v-else-if="editing" tone="warning">{{ t('newDraft') }}</FaBadge>
    <span v-else class="fa-dataprotection__muted">{{ t('noVersion') }}</span>
    <FaBadge v-if="dirty" tone="accent">{{ t('unsaved') }}</FaBadge>
    <div class="fa-dataprotection__actions">
      <FaButton v-if="draft && released" variant="ghost" size="sm" :label="showing === 'draft' ? t('showReleased') : t('showDraft')" @click="emit('show', showing === 'draft' ? 'released' : 'draft')" />
      <FaButton v-if="editable && !draft && !editing" size="sm" icon="plus" :label="t('newDraft')" @click="emit('new-draft')" />
      <FaButton v-if="editing && dirty" size="sm" :label="t('discard')" @click="emit('discard')" />
      <FaButton v-if="editing" variant="primary" size="sm" :loading="busy === 'save'" :disabled="!dirty" :label="busy === 'save' ? t('saving') : t('save')" @click="emit('save')" />
      <FaButton
        v-if="editable && draft"
        size="sm"
        icon="lock"
        :label="t('release')"
        :disabled="!canRelease"
        :loading="busy === 'release'"
        :title="releaseHint || undefined"
        @click="emit('release')"
      />
      <FaButton variant="ghost" size="sm" icon="clock" :pressed="history" :label="history ? t('hideHistory') : t('history')" @click="emit('toggle-history')" />
      <FaButton variant="ghost" size="sm" :label="t('exportPrint')" @click="emit('export', 'print')" />
      <FaButton variant="ghost" size="sm" :label="t('exportMarkdown')" @click="emit('export', 'markdown')" />
      <FaButton variant="ghost" size="sm" :label="t('exportCsv')" @click="emit('export', 'csv')" />
    </div>
    <p v-if="editable && draft && releaseHint" class="fa-dataprotection__muted" data-testid="vvt-release-hint">{{ releaseHint }}</p>
  </div>
</template>
