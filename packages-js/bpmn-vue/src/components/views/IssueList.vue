<script setup lang="ts">
/** Validation issues grouped by severity with jump to the element. */
import { computed, ref } from 'vue'
import { issueMessage, severityLabel, type Severity, type ValidationIssue } from '@flowaudit/bpmn-flowaudit'
import { countSeverity, filterIssues, ISSUE_ICONS as ICONS, SEVERITIES } from '@flowaudit/bpmn-flowaudit/ui'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ issues: ValidationIssue[]; running?: boolean; error?: string | null }>()
const emit = defineEmits<{ (e: 'jump', elementId: string): void }>()
const { t, locale } = useI18n()
const filter = ref<Severity | 'alle'>('alle')

const shown = computed(() => filterIssues(props.issues, filter.value))
const count = (severity: Severity) => countSeverity(props.issues, severity)
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
