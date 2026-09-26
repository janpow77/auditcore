<script setup lang="ts">
import FaButton from '../../base/FaButton.vue'
import { formatDate, useI18n } from '../../i18n'
import { decisionTitle } from '../core'
import { dataprotectionMessages } from '../core'
import { statusLabel } from '../core'
import type { AssessmentSummary, DataProtectionProfile } from '../core'

withDefaults(defineProps<{ versions?: AssessmentSummary[]; profile: DataProtectionProfile; current?: string }>(), { versions: () => [], current: '' })
const emit = defineEmits<{ open: [id: string] }>()
const { t, locale } = useI18n(dataprotectionMessages)
const when = (value: string | null): string => formatDate(value, locale.value, true) || t('empty')
</script>

<template>
  <section class="fa-dataprotection__panel" data-testid="dsfa-versions" :aria-label="t('versions')">
    <h3>{{ t('versions') }}</h3>
    <table class="fa-dataprotection__table">
      <thead>
        <tr>
          <th scope="col">{{ t('colVersion') }}</th>
          <th scope="col">{{ t('colStatus') }}</th>
          <th scope="col">{{ t('colDecision') }}</th>
          <th scope="col">{{ t('colCreated') }}</th>
          <th scope="col">{{ t('colReleased') }}</th>
          <th scope="col"><span class="fa-sr-only">{{ t('colAction') }}</span></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="entry in versions" :key="entry.id" :aria-current="entry.id === current ? 'true' : undefined">
          <td>{{ entry.version }}</td>
          <td>{{ statusLabel(t, entry.status) }}</td>
          <td>{{ decisionTitle(profile, entry.decision) || t('empty') }}</td>
          <td>{{ when(entry.created_at) }}</td>
          <td>{{ entry.released_by ? `${entry.released_by}, ${when(entry.released_at)}` : t('empty') }}</td>
          <td>
            <FaButton v-if="entry.id !== current" size="sm" variant="ghost" :label="t('openAssessment')" :aria-label="`${t('openAssessment')}: ${t('colVersion')} ${entry.version}`" @click="emit('open', entry.id)" />
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
