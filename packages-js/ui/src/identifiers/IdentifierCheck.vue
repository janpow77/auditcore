<script setup lang="ts">
import { provide, watch } from 'vue'
import {
  identifierMessages,
  identifierProfileLabel,
  type IdentifierBatchAnswer,
  type IdentifierResult,
  type IdentifiersPort,
} from '@flowaudit/ui-core'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import { IDENTIFIER_CONTEXT } from './context'
import IdentifierBatch from './IdentifierBatch.vue'
import IdentifierSingle from './IdentifierSingle.vue'
import { useIdentifierCheck } from './useIdentifierCheck'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createIdentifiersRestPort({ baseUrl: '/api/kennungen' })`. */
  port?: IdentifiersPort | null
  locale?: Locale
}>(), { port: null, locale: undefined })

const emit = defineEmits<{
  'identifier-checked': [result: IdentifierResult]
  'batch-checked': [answer: IdentifierBatchAnswer]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(identifierMessages, () => props.locale)
const id = useId('fa-ident')
const view = useIdentifierCheck(() => props.port, {
  checked: (result) => emit('identifier-checked', result),
  batchChecked: (answer) => emit('batch-checked', answer),
  failed: (message) => emit('error', message),
})
const { controller, state, profile } = view
provide(IDENTIFIER_CONTEXT, { view, t, id })

watch(() => props.port, () => void controller.load(), { immediate: true })

const selected = (event: Event): string => (event.target as HTMLSelectElement).value
</script>

<template>
  <div class="fa-ident" :lang="active">
    <p v-if="!port" class="fa-ident__muted" role="status">{{ t('noPort') }}</p>
    <p v-if="state.busy === 'load'" class="fa-ident__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-ident__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <template v-if="state.catalogue">
      <div class="fa-ident__head">
        <label class="fa-ident__field">
          <span class="fa-ident__label">{{ t('profile') }}</span>
          <select :value="state.profileId ?? ''" class="fa-ident__select" data-testid="ident-profile" @change="controller.setProfile(selected($event) || null)">
            <option value="">{{ t('choose') }}</option>
            <option v-for="entry in state.catalogue.profiles" :key="entry.id" :value="entry.id">{{ identifierProfileLabel(state.catalogue, entry, t) }}</option>
          </select>
        </label>
        <details v-if="profile" class="fa-ident__source">
          <summary>{{ t('profileSource') }}</summary>
          <p>{{ profile.rationale }}</p>
          <p>{{ profile.origin }}</p>
        </details>
      </div>
      <div class="fa-ident__columns">
        <IdentifierSingle />
        <IdentifierBatch />
      </div>
    </template>
  </div>
</template>
