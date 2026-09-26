<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import { useI18n } from '../../i18n'
import { blockProgress, screeningTone, withAnswer, withJustification } from '../core'
import { dataprotectionMessages } from '../core'
import { prefixedLabel } from '../core'
import type { DataProtectionProfile, Proposal, SurveyInput } from '../core'
import DsfaQuestion from './DsfaQuestion.vue'

const props = withDefaults(defineProps<{
  profile: DataProtectionProfile
  survey: SurveyInput
  proposal?: Proposal | null
  preview?: boolean
  readonly?: boolean
}>(), { proposal: null, preview: false, readonly: false })

const emit = defineEmits<{ 'survey-change': [survey: SurveyInput] }>()
const { t } = useI18n(dataprotectionMessages)
const screening = computed(() => props.proposal?.screening ?? null)
const open = computed(() => (screening.value ? screening.value.unanswered.length + screening.value.unknown.length : 0))
</script>

<template>
  <div data-testid="dsfa-screening">
    <section v-if="screening" class="fa-dataprotection__panel" :aria-label="t('screeningResult')">
      <div class="fa-dataprotection__bar">
        <h3>{{ t('screeningResult') }}</h3>
        <FaBadge :tone="screeningTone(screening.outcome)">{{ prefixedLabel(t, 'outcome', screening.outcome) }}</FaBadge>
        <FaBadge v-if="preview" tone="accent">{{ t('preview') }}</FaBadge>
      </div>
      <p aria-live="polite">{{ screening.reasoning }}</p>
      <p class="fa-dataprotection__muted">
        {{ t('hardTriggers', { count: screening.hard_triggers.length }) }} ·
        {{ t('points', { points: screening.points, threshold: screening.points_threshold }) }} ·
        {{ t('openAnswers', { count: open }) }}
      </p>
    </section>
    <section v-for="block in profile.screening.blocks" :key="block.key" class="fa-dataprotection__panel" :aria-label="block.title">
      <div class="fa-dataprotection__bar">
        <h3>{{ block.title }}</h3>
        <span class="fa-dataprotection__muted">{{ t('progress', { ...blockProgress(block, survey) }) }}</span>
      </div>
      <DsfaQuestion
        v-for="question in block.questions"
        :key="question.key"
        :question="question"
        :answer="survey.answers[question.key] ?? null"
        :readonly="readonly"
        @answer="emit('survey-change', withAnswer(survey, question.key, $event))"
        @justify="emit('survey-change', withJustification(survey, question.key, $event))"
      />
    </section>
  </div>
</template>
