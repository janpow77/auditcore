<script setup lang="ts">
import { computed } from 'vue'
import { needsJustification, questionFieldId, questionOptions, type AssistantQuestion, type Draft } from '@auditcore/ui-core'
import { useI18n } from '../../i18n'
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
  <fieldset class="fa-assistant__question" :data-question="question.id" :aria-describedby="`${fieldId}-help`" :aria-invalid="error ? 'true' : undefined">
    <legend>
      {{ question.text }}
      <span class="fa-assistant__badge">{{ question.required ? t('requiredQuestion') : t('optionalQuestion') }}</span>
    </legend>
    <details v-if="question.help || question.reference" :id="`${fieldId}-help`">
      <summary>{{ t('whyAsked') }}</summary>
      <p>{{ question.help }}</p>
      <p v-if="question.reference" class="fa-dataprotection__muted">{{ t('reference', { reference: question.reference }) }}</p>
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
    <textarea v-else :id="fieldId" :value="draft.value" rows="3" :aria-label="question.text" @input="set({ value: ($event.target as HTMLTextAreaElement).value })"></textarea>
    <label v-if="showReason">{{ t('answerJustification') }}
      <textarea :value="draft.justification" rows="2" @input="set({ justification: ($event.target as HTMLTextAreaElement).value })"></textarea>
    </label>
    <p v-if="error" :id="`${fieldId}-error`" class="fa-dataprotection__alert" role="alert">{{ error }}</p>
    <button type="button" :disabled="busy || draft.value === ''" @click="emit('save')">{{ t('saveAnswer') }}</button>
  </fieldset>
</template>
