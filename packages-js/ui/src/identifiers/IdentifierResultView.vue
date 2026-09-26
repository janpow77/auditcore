<script setup lang="ts">
import { computed } from 'vue'
import { identifierFacts, identifierReasonText, identifierStatusText, identifierStatusTone, type IdentifierResult } from '@flowaudit/ui-core'
import { useIdentifierContext } from './context'

const props = defineProps<{ result: IdentifierResult }>()
const { view, t } = useIdentifierContext()
const { state, profile } = view
const reason = computed(() => identifierReasonText(props.result, profile.value?.title ?? props.result.profile, t))
const facts = computed(() => (state.value.catalogue ? identifierFacts(state.value.catalogue, props.result, t) : []))
</script>

<template>
  <div class="fa-ident__result" aria-live="polite" data-testid="ident-result">
    <p class="fa-ident__status">
      <span :class="['fa-ident__badge', `fa-ident__badge--${identifierStatusTone(result.status)}`]">{{ identifierStatusText(result.status, t) }}</span>
      <span>{{ result.kind_label }}</span>
    </p>
    <dl class="fa-ident__facts">
      <dt>{{ t('message') }}</dt>
      <dd>{{ reason }}</dd>
      <template v-if="result.reason_label">
        <dt>{{ t('reason') }}</dt>
        <dd>{{ result.reason_label }}</dd>
      </template>
      <template v-if="result.normalized">
        <dt>{{ t('normalized') }}</dt>
        <dd><code>{{ result.normalized }}</code></dd>
      </template>
      <template v-if="result.country">
        <dt>{{ t('countryFound') }}</dt>
        <dd>{{ result.country }}</dd>
      </template>
    </dl>
    <details v-if="facts.length" class="fa-ident__details">
      <summary>{{ t('details') }}</summary>
      <dl class="fa-ident__facts">
        <template v-for="fact in facts" :key="fact.key">
          <dt>{{ fact.label }}</dt>
          <dd>{{ fact.value }}</dd>
        </template>
      </dl>
    </details>
  </div>
</template>
