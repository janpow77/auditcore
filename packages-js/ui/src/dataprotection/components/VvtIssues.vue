<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../i18n'
import { dataprotectionMessages } from '../core'
import { completeness } from '../core'
import type { Issue } from '../core'

const props = withDefaults(defineProps<{ issues?: Issue[] }>(), { issues: () => [] })
const { t } = useI18n(dataprotectionMessages)
const summary = computed(() => completeness(props.issues))
</script>

<template>
  <section class="fa-dataprotection__panel" data-testid="vvt-issues" :aria-label="t('completenessTitle')">
    <h3>{{ t('completenessTitle') }}</h3>
    <p aria-live="polite">
      {{ issues.length ? t('completenessSummary', { blocking: summary.blocking, hints: summary.hints }) : t('completenessOk') }}
    </p>
    <ul v-if="issues.length" class="fa-dataprotection__issues">
      <li v-for="issue in issues" :key="issue.subject + issue.code" :class="{ 'is-blocking': issue.blocking }">
        <strong>{{ issue.blocking ? t('blockingLabel') : t('hintLabel') }}:</strong> {{ issue.message }}
      </li>
    </ul>
  </section>
</template>
