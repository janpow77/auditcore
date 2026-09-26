<script setup lang="ts">
import FaBadge from '../../base/FaBadge.vue'
import FaButton from '../../base/FaButton.vue'
import { useI18n } from '../../i18n'
import { recommendationTone } from '../core'
import { dataprotectionMessages } from '../core'
import { statusTone } from '../core'
import { statusLabel } from '../core'
import type { OverviewRow, DataProtectionProfile } from '../core'

withDefaults(defineProps<{
  rows?: OverviewRow[]
  profile?: DataProtectionProfile | null
  selected?: string | null
  editable?: boolean
  busy?: boolean
}>(), { rows: () => [], profile: null, selected: null, editable: true, busy: false })

const emit = defineEmits<{ open: [assessmentId: string]; start: [activityId: string] }>()
const { t } = useI18n(dataprotectionMessages)

function decision(profile: DataProtectionProfile | null, key: string | null): string {
  if (!key) return t('empty')
  return profile?.decisions.find((entry) => entry.key === key)?.title ?? key
}
</script>

<template>
  <section class="fa-dataprotection__panel" data-testid="dsfa-overview" :aria-label="t('overview')">
    <h3>{{ t('overview') }}</h3>
    <p v-if="!rows.length" class="fa-dataprotection__muted">{{ t('noRegister') }}</p>
    <table v-else class="fa-dataprotection__table">
      <thead>
        <tr>
          <th scope="col">{{ t('colActivity') }}</th>
          <th scope="col">{{ t('colDepartment') }}</th>
          <th scope="col">{{ t('colState') }}</th>
          <th scope="col">{{ t('colResult') }}</th>
          <th scope="col"><span class="fa-sr-only">{{ t('colAction') }}</span></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id" :aria-current="row.dsfa && row.dsfa.id === selected ? 'true' : undefined">
          <th scope="row">{{ row.name }}</th>
          <td>{{ row.referat || t('withoutDepartment') }}</td>
          <td>
            <template v-if="row.dsfa">
              <FaBadge :tone="statusTone(row.dsfa.status)">{{ statusLabel(t, row.dsfa.status) }} · {{ t('colVersion') }} {{ row.dsfa.version }}</FaBadge>
              <FaBadge v-if="row.dsfa.pruefung_erforderlich" tone="danger">{{ t('reviewRequired') }}</FaBadge>
            </template>
            <span v-else class="fa-dataprotection__muted">{{ t('noDsfa') }}</span>
          </td>
          <td>
            <FaBadge v-if="row.dsfa?.entscheidung" :tone="recommendationTone(row.dsfa.entscheidung)">{{ decision(profile, row.dsfa.entscheidung) }}</FaBadge>
            <span v-else>{{ t('empty') }}</span>
          </td>
          <td>
            <FaButton v-if="row.dsfa" size="sm" :label="t('openAssessment')" :aria-label="`${t('openAssessment')}: ${row.name}`" @click="emit('open', row.dsfa.id)" />
            <FaButton v-else-if="editable" size="sm" variant="primary" :disabled="busy" :label="t('startAssessment')" :aria-label="`${t('startAssessment')}: ${row.name}`" @click="emit('start', row.id)" />
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
