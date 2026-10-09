<script setup lang="ts">
import { computed } from 'vue'
import { needsJustification, questionFieldId, questionOptions, type AssistantQuestion, type Draft } from '@auditcore/ui-core'
import { useI18n } from '../../i18n'
import AssistantTable from './AssistantTable.vue'
import { dataprotectionMessages } from '../core'

const props = defineProps<{ question: AssistantQuestion; draft: Draft; error?: string; busy: boolean }>()
const emit = defineEmits<{ change: [draft: Draft]; save: []; confirm: [] }>()
const { t } = useI18n(dataprotectionMessages)

const fieldId = computed(() => questionFieldId(props.question))
const withNa = computed(() => (props.question.kind === 'text' ? [] : questionOptions(t, props.question)))
const suggestion = computed(() => props.question.answer !== null && props.question.answer.origin !== 'bestaetigt')
const showReason = computed(() => needsJustification(props.question, props.draft.value) || props.draft.justification !== '')

function set(patch: Partial<Draft>): void {
  emit('change', { ...props.draft, ...patch })
}
</script>

<template>
  <fieldset :class="['fa-assistant__question', question.depth ? `fa-assistant__question--depth-${Math.min(question.depth, 2)}` : '']" :data-question="question.id" :aria-describedby="`${fieldId}-help`" :aria-invalid="error ? 'true' : undefined">
    <legend>
      <span class="fa-assistant__number">{{ question.number }}</span>
      {{ question.text }}
      <span class="fa-assistant__badge">{{ question.required ? t('requiredQuestion') : t('optionalQuestion') }}</span>
    </legend>
    <details v-if="question.hints.length || question.reference" :id="`${fieldId}-help`" class="fa-assistant__hints">
      <summary>{{ t('whyAsked') }}</summary>
      <ul>
        <li v-if="question.reference">{{ t('reference', { reference: question.reference }) }}</li>
        <li v-for="(hint, index) in question.hints" :key="index">{{ hint }}</li>
      </ul>
    </details>
    <p v-if="suggestion" class="fa-dataprotection__alert fa-dataprotection__alert--warning">
      {{ t('suggestion', { origin: question.answer?.origin ?? '' }) }}
      <button type="button" :disabled="busy" @click="emit('confirm')">{{ t('confirmSuggestion') }}</button>
    </p>
    <div v-if="withNa.length" class="fa-assistant__choices" role="radiogroup" :aria-label="question.text">
      <label v-for="option in withNa" :key="option.key">
        <input :id="`${fieldId}-${option.key}`" type="radio" :name="fieldId" :value="option.key" :checked="draft.value === option.key" @change="set({ value: option.key })" />
        {{ option.title }}
      </label>
    </div>
    <input v-else-if="question.kind === 'zahl'" :id="fieldId" type="number" min="0" step="1" inputmode="numeric" :value="draft.value" :aria-label="`${question.text} ${t('numberInput')}`" @input="set({ value: ($event.target as HTMLInputElement).value })" />
    <AssistantTable v-else-if="question.kind === 'tabelle'" :question="question" :value="draft.value" @change="(value) => set({ value })" />
    <textarea v-else :id="fieldId" :value="draft.value" rows="3" :aria-label="question.text" @input="set({ value: ($event.target as HTMLTextAreaElement).value })"></textarea>
    <label v-if="showReason">{{ t('answerJustification') }}
      <textarea :value="draft.justification" rows="2" @input="set({ justification: ($event.target as HTMLTextAreaElement).value })"></textarea>
    </label>
    <p v-if="error" :id="`${fieldId}-error`" class="fa-dataprotection__alert" role="alert">{{ error }}</p>
    <button type="button" :disabled="busy || draft.value === ''" @click="emit('save')">{{ t('saveAnswer') }}</button>
  </fieldset>
</template>
