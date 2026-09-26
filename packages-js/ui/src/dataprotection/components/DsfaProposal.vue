<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import { useI18n } from '../../i18n'
import { decisionTitle, recommendationTone } from '../core'
import { dataprotectionMessages } from '../core'
import { prefixedLabel } from '../core'
import type { DataProtectionProfile, Proposal } from '../core'

const props = withDefaults(defineProps<{
  profile: DataProtectionProfile
  proposal: Proposal
  preview?: boolean
  openPoints?: string[]
}>(), { preview: false, openPoints: () => [] })

const { t } = useI18n(dataprotectionMessages)
const title = computed(() => prefixedLabel(t, 'recommendation', props.proposal.recommendation, decisionTitle(props.profile, props.proposal.recommendation)))
</script>

<template>
  <section class="fa-dataprotection__panel" data-testid="dsfa-proposal" :aria-label="t('proposalTitle')">
    <div class="fa-dataprotection__bar">
      <h3>{{ t('proposalTitle') }}</h3>
      <FaBadge :tone="recommendationTone(proposal.recommendation)">{{ title }}</FaBadge>
      <FaBadge v-if="preview" tone="accent">{{ t('preview') }}</FaBadge>
    </div>
    <p aria-live="polite">{{ proposal.recommendation_text }}</p>
    <p class="fa-dataprotection__muted">{{ proposal.reasoning }}</p>
    <p v-if="proposal.consultation_notice" class="fa-dataprotection__alert fa-dataprotection__alert--info">
      <strong>{{ t('consultation') }}:</strong> {{ proposal.consultation_notice.text }}
    </p>
    <template v-if="proposal.issues.length || openPoints.length">
      <h4>{{ t('issuesTitle') }}</h4>
      <ul class="fa-dataprotection__issues">
        <li v-for="issue in proposal.issues" :key="issue.code + issue.subject" :class="{ 'is-blocking': issue.blocking }">{{ issue.message }}</li>
        <li v-for="point in openPoints" :key="point">{{ point }}</li>
      </ul>
    </template>
    <p class="fa-dataprotection__muted">{{ t('profile', { id: proposal.profile.id, version: proposal.profile.version }) }}</p>
  </section>
</template>
