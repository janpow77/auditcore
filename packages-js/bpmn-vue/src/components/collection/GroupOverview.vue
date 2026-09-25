<script setup lang="ts">
/**
 * Group overview of a folder (recursive): status distribution, legal basis
 * coverage, key requirement coverage (catalogue of the profile) and
 * collection issues.
 */
import { computed } from 'vue'
import { DIAGRAM_STATUS, issueMessage, keyRequirements, label, localized, type GroupOverview as Overview, type ProfileData, type ValidationIssue } from '@flowaudit/bpmn-flowaudit'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ overview: Overview; profile: ProfileData | null; issues: ValidationIssue[]; title: string }>()
const emit = defineEmits<{ (e: 'open', id: string): void }>()
const { t, locale } = useI18n()

const percent = computed(() => Math.round((props.overview.legalBasisCoverage ?? 0) * 100))
const statuses = computed(() => Object.entries(props.overview.statusDistribution))
const requirements = computed(() => keyRequirements(props.profile))
const covered = (number: number) => props.overview.keyRequirementCoverage[number] ?? []
const statusLabel = (code: string) => (DIAGRAM_STATUS[code] ? label(DIAGRAM_STATUS[code], locale.value) : t(`collection.status.${code}`))
</script>

<template>
  <section class="fa-overview" :aria-label="t('collection.overview')">
    <h2>{{ title }}</h2>
    <div class="fa-overview__cards">
      <div class="fa-card fa-overview__card">
        <span class="fa-label">{{ t('collection.overview.count') }}</span>
        <strong class="fa-overview__number">{{ overview.count }}</strong>
      </div>
      <div class="fa-card fa-overview__card">
        <span class="fa-label">{{ t('collection.overview.legal') }}</span>
        <strong class="fa-overview__number">{{ overview.legalBasisCoverage === null ? '–' : `${percent} %` }}</strong>
        <div class="fa-meter" role="meter" :aria-valuenow="percent" aria-valuemin="0" aria-valuemax="100"><span :style="{ width: `${percent}%` }" /></div>
        <span class="fa-help">{{ t('collection.overview.legalValue', { with: overview.activitiesWithLegalBasis, total: overview.activities, percent }) }}</span>
      </div>
      <div class="fa-card fa-overview__card">
        <span class="fa-label">{{ t('collection.overview.status') }}</span>
        <ul class="fa-overview__status">
          <li v-for="[code, count] in statuses" :key="code"><span class="fa-badge">{{ statusLabel(code) }}</span> {{ count }}</li>
        </ul>
      </div>
    </div>
    <h3 class="fa-section__title fa-section">{{ t('collection.overview.ka') }}</h3>
    <div class="fa-overview__ka">
      <div v-for="requirement in requirements" :key="requirement.number" class="fa-overview__ka-cell" :class="{ 'fa-overview__ka-cell--covered': covered(requirement.number).length }" :title="localized(requirement.title, locale)">
        <strong>KA {{ requirement.number }}</strong>
        <span>{{ covered(requirement.number).length }}</span>
      </div>
    </div>
    <template v-if="overview.expired.length">
      <h3 class="fa-section__title fa-section">{{ t('collection.overview.expired') }}</h3>
      <button v-for="id in overview.expired" :key="id" type="button" class="fa-chip" @click="emit('open', id)">{{ id }}</button>
    </template>
    <template v-if="issues.length">
      <h3 class="fa-section__title fa-section">{{ t('collection.overview.issues') }}</h3>
      <ul class="fa-overview__issues">
        <li v-for="(item, index) in issues" :key="index">{{ issueMessage(item, locale) }}</li>
      </ul>
    </template>
  </section>
</template>

<style>
.fa-overview {
  padding: 20px 24px;
  overflow: auto;
}

.fa-overview h2 {
  margin: 0 0 14px;
  font-size: 18px;
}

.fa-overview__cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.fa-overview__card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
}

.fa-overview__number {
  font-size: 26px;
  font-weight: 700;
}

.fa-meter {
  height: 8px;
  border-radius: 4px;
  background: var(--fa-surface-3);
  overflow: hidden;
}

.fa-meter span {
  display: block;
  height: 100%;
  background: var(--fa-success);
}

.fa-overview__status {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.fa-overview__ka {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(84px, 1fr));
  gap: 6px;
}

.fa-overview__ka-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 4px;
  border: 1px solid var(--fa-border);
  border-radius: var(--fa-radius-sm);
  background: var(--fa-surface);
  color: var(--fa-text-muted);
}

.fa-overview__ka-cell--covered {
  border-color: var(--fa-success);
  background: var(--fa-success-soft);
  color: var(--fa-text);
}

.fa-overview__issues {
  padding-left: 18px;
}
</style>
