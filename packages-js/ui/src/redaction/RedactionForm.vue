<script setup lang="ts">
import { computed } from 'vue'
import {
  redactionPatternText,
  redactionSizeText,
  redactionValidationText,
  type Locale,
  type RedactionController,
  type RedactionData,
  type RedactionTranslate,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'

const props = defineProps<{ id: string; controller: RedactionController; state: RedactionData; t: RedactionTranslate; locale: Locale }>()

const catalogue = computed(() => props.state.catalogue)
const problem = computed(() => redactionValidationText(props.state.validation, catalogue.value, props.t, props.locale, props.state.fileFixed))

function onFile(event: Event): void {
  props.controller.selectFile((event.target as HTMLInputElement).files?.[0] ?? null)
}

const checked = (event: Event): boolean => (event.target as HTMLInputElement).checked
</script>

<template>
  <form v-if="catalogue" class="fa-redaction__card" novalidate :aria-labelledby="`${id}-form`" data-testid="redaction-form" @submit.prevent="controller.plan">
    <h3 :id="`${id}-form`" class="fa-redaction__heading" tabindex="-1">{{ t('formHeading') }}</h3>
    <p v-if="state.presetsApplied" class="fa-redaction__notice" role="status" data-testid="redaction-presets-changed">{{ t('presetsChanged') }}</p>
    <p v-if="state.fileFixed" :id="`${id}-file-provided`" class="fa-redaction__field fa-redaction__provided" data-testid="redaction-file-provided">
      <span class="fa-redaction__label">{{ t('fileProvided') }}</span>{{ ' ' }}
      <span class="fa-redaction__value">{{ state.filename }}</span>
    </p>
    <template v-else>
      <label class="fa-redaction__field">
        <span class="fa-redaction__label">{{ t('file') }}</span>
        <input class="fa-redaction__file" type="file" accept="application/pdf,.pdf" :aria-describedby="`${id}-file-help`" data-testid="redaction-file" @change="onFile" />
      </label>
      <p v-if="state.filename" class="fa-redaction__muted" data-testid="redaction-file-chosen">{{ t('fileChosen', { name: state.filename }) }}</p>
      <p :id="`${id}-file-help`" class="fa-redaction__muted">{{ t('fileHelp', { size: redactionSizeText(catalogue.limits.max_upload_bytes, locale), pages: catalogue.limits.max_pages }) }}</p>
    </template>
    <fieldset class="fa-redaction__patterns" :aria-describedby="state.fileFixed ? `${id}-file-provided` : undefined">
      <legend class="fa-redaction__label">{{ t('patterns') }}</legend>
      <label v-for="pattern in catalogue.patterns" :key="pattern.id" class="fa-redaction__check" :title="pattern.hint">
        <input type="checkbox" :data-pattern="pattern.id" :checked="state.patterns.includes(pattern.id)" :disabled="!pattern.available" @change="controller.setPattern(pattern.id, checked($event))" />
        <span>{{ redactionPatternText(pattern, t) }}</span>
      </label>
    </fieldset>
    <label class="fa-redaction__field">
      <span class="fa-redaction__label">{{ t('terms') }}</span>
      <textarea class="fa-redaction__input" rows="4" :aria-describedby="`${id}-terms-help`" data-testid="redaction-terms" :value="state.terms" @input="controller.setTerms(($event.target as HTMLTextAreaElement).value)"></textarea>
    </label>
    <p :id="`${id}-terms-help`" class="fa-redaction__muted">{{ t('termsHelp', { count: catalogue.limits.max_terms, length: catalogue.limits.max_term_length }) }}</p>
    <div class="fa-redaction__options">
      <label class="fa-redaction__check">
        <input type="checkbox" data-testid="redaction-case" :checked="state.caseSensitive" @change="controller.setOption('caseSensitive', checked($event))" />
        <span>{{ t('caseSensitive') }}</span>
      </label>
      <label class="fa-redaction__check">
        <input type="checkbox" data-testid="redaction-whole-word" :checked="state.wholeWord" @change="controller.setOption('wholeWord', checked($event))" />
        <span>{{ t('wholeWord') }}</span>
      </label>
    </div>
    <p v-if="problem" class="fa-redaction__error" role="alert">{{ problem }}</p>
    <div>
      <FaButton variant="primary" type="submit" :loading="state.busy === 'plan'" data-testid="redaction-search">{{ t('search') }}</FaButton>
    </div>
  </form>
</template>
