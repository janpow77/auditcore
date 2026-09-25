<script setup lang="ts">
/** Validation issues grouped by severity with jump to the element. */
import { computed, ref } from 'vue'
import { issueMessage, severityLabel, type Severity, type ValidationIssue } from '@flowaudit/bpmn-flowaudit'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ issues: ValidationIssue[]; running?: boolean; error?: string | null }>()
const emit = defineEmits<{ (e: 'jump', elementId: string): void }>()
const { t, locale } = useI18n()
const filter = ref<Severity | 'alle'>('alle')

const ICONS: Record<Severity, string> = { fehler: 'error', warnung: 'warning', hinweis: 'hint' }
const SEVERITIES: Severity[] = ['fehler', 'warnung', 'hinweis']
const shown = computed(() => (filter.value === 'alle' ? props.issues : props.issues.filter((item) => item.severity === filter.value)))
const count = (severity: Severity) => props.issues.filter((item) => item.severity === severity).length
</script>

<template>
  <section class="fa-issues" :aria-label="t('issues.label')" :aria-busy="running">
    <div class="fa-issues__filter" role="group">
      <button type="button" class="fa-chip" :aria-pressed="filter === 'alle'" @click="filter = 'alle'">{{ t('issues.filter.all') }} {{ issues.length }}</button>
      <button v-for="severity in SEVERITIES" :key="severity" type="button" class="fa-chip" :aria-pressed="filter === severity" @click="filter = severity">
        <FaIcon :name="ICONS[severity]" :size="14" />{{ severityLabel(severity, locale) }} {{ count(severity) }}
      </button>
    </div>
    <p v-if="error" class="fa-badge fa-badge--danger">{{ error }}</p>
    <p v-if="!issues.length" class="fa-help">{{ t('issues.none') }}</p>
    <ol class="fa-issues__list">
      <li v-for="(item, index) in shown" :key="index" class="fa-issue" :class="`fa-issue--${item.severity}`">
        <FaIcon :name="ICONS[item.severity]" :size="16" :label="severityLabel(item.severity, locale)" />
        <div class="fa-issue__body">
          <p>{{ issueMessage(item, locale) }}</p>
          <span class="fa-help">{{ item.ruleId }}</span>
        </div>
        <button v-if="item.elementId" type="button" class="fa-btn fa-btn--ghost" @click="emit('jump', item.elementId)">{{ t('issues.jump') }}</button>
      </li>
    </ol>
  </section>
</template>

<style>
.fa-issues__filter {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.fa-issues__list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.fa-issue {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  border: 1px solid var(--fa-border);
  border-left-width: 3px;
  border-radius: var(--fa-radius-sm);
  background: var(--fa-surface);
}

.fa-issue--fehler {
  border-left-color: var(--fa-danger);
}

.fa-issue--fehler > svg {
  color: var(--fa-danger);
}

.fa-issue--warnung {
  border-left-color: var(--fa-warning);
}

.fa-issue--warnung > svg {
  color: var(--fa-warning);
}

.fa-issue--hinweis {
  border-left-color: var(--fa-info);
}

.fa-issue--hinweis > svg {
  color: var(--fa-info);
}

.fa-issue__body {
  flex: 1;
  min-width: 0;
}

.fa-issue__body p {
  margin: 0;
}
</style>
