<script setup lang="ts">
import { formatDate, useI18n } from '../../i18n'
import { dataprotectionMessages } from '../core'
import { statusLabel } from '../core'
import type { VersionSummary } from '../core'

withDefaults(defineProps<{ versions?: VersionSummary[] }>(), { versions: () => [] })
const { t, locale } = useI18n(dataprotectionMessages)
const when = (value: string | null): string => formatDate(value, locale.value, true) || t('empty')
</script>

<template>
  <section class="fa-dataprotection__panel" data-testid="vvt-history" :aria-label="t('history')">
    <h3>{{ t('history') }}</h3>
    <table class="fa-dataprotection__table">
      <thead>
        <tr>
          <th scope="col">{{ t('colVersion') }}</th>
          <th scope="col">{{ t('colStatus') }}</th>
          <th scope="col">{{ t('colCreated') }}</th>
          <th scope="col">{{ t('colReleased') }}</th>
          <th scope="col">{{ t('colActivities') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="entry in versions" :key="entry.version">
          <td>{{ entry.version }}</td>
          <td>{{ statusLabel(t, entry.status) }}</td>
          <td>{{ entry.created_by }}, {{ when(entry.created_at) }}</td>
          <td>{{ entry.released_by ? `${entry.released_by}, ${when(entry.released_at)}` : t('empty') }}</td>
          <td>{{ entry.activities }}</td>
        </tr>
        <tr v-if="!versions.length">
          <td colspan="5" class="fa-dataprotection__muted">{{ t('noHistory') }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
