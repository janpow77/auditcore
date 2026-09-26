<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import { useId } from '../../composables/useId'
import { useI18n } from '../../i18n'
import { ANSWER_VALUES } from '../core'
import { dataprotectionMessages } from '../core'
import { prefixedLabel } from '../core'
import type { AnswerInput, AnswerValue, QuestionView } from '../core'

const props = withDefaults(defineProps<{
  question: QuestionView
  answer?: AnswerInput | null
  readonly?: boolean
}>(), { answer: null, readonly: false })

const emit = defineEmits<{ answer: [value: AnswerValue]; justify: [text: string] }>()
const { t } = useI18n(dataprotectionMessages)
const id = useId('fa-dsfa-q')
const value = computed(() => props.answer?.value ?? null)
const tone = computed(() => (props.question.effect === 'hart' ? 'danger' : props.question.effect === 'fria' ? 'accent' : 'neutral'))
</script>

<template>
  <fieldset class="fa-dsfa__question" :class="{ 'fa-dsfa__question--yes': value === 'ja' }" :disabled="readonly" :data-question="question.key">
    <legend>{{ question.text }}</legend>
    <div class="fa-dsfa__meta">
      <FaBadge :tone="tone">{{ prefixedLabel(t, 'effect', question.effect) }}</FaBadge>
      <span class="fa-dataprotection__ref">{{ question.reference }}</span>
    </div>
    <div class="fa-dataprotection__choices">
      <label v-for="option in ANSWER_VALUES" :key="option" class="fa-dataprotection__choice">
        <input type="radio" :name="id" :value="option" :checked="value === option" @change="emit('answer', option)" />
        {{ prefixedLabel(t, 'answer', option) }}
      </label>
    </div>
    <div v-if="value === 'ja' || value === 'unbekannt'" class="fa-dataprotection__field">
      <label :for="`${id}-why`">{{ t('justification') }}</label>
      <input :id="`${id}-why`" type="text" :value="answer?.justification ?? ''" @input="emit('justify', ($event.target as HTMLInputElement).value)" />
    </div>
    <details v-if="question.explanation">
      <summary>{{ t('explanation') }}</summary>
      <p>{{ question.explanation }}</p>
    </details>
  </fieldset>
</template>
