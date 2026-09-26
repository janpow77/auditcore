<script setup lang="ts">
import { computed } from 'vue'
import { identifierErrorKey, kindNeedsCountry } from '@flowaudit/ui-core'
import FaButton from '../base/FaButton.vue'
import { useIdentifierContext } from './context'
import IdentifierResultView from './IdentifierResultView.vue'

const { view, t, id } = useIdentifierContext()
const { controller, state, kinds } = view
const kindInfo = computed(() => kinds.value.find((entry) => entry.id === state.value.kind) ?? null)
const selected = (event: Event): string => (event.target as HTMLSelectElement).value
const typed = (event: Event): string => (event.target as HTMLInputElement).value
</script>

<template>
  <section v-if="state.catalogue" class="fa-ident__card" :aria-labelledby="`${id}-single`">
    <h3 :id="`${id}-single`" class="fa-ident__heading">{{ t('single') }}</h3>
    <form class="fa-ident__form" novalidate @submit.prevent="controller.check">
      <label class="fa-ident__field">
        <span class="fa-ident__label">{{ t('kind') }}</span>
        <select :value="state.kind ?? ''" class="fa-ident__select" data-testid="ident-kind" @change="controller.setKind(selected($event) || null)">
          <option value="">{{ t('choose') }}</option>
          <option v-for="entry in kinds" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
        </select>
      </label>
      <p v-if="kindInfo" class="fa-ident__muted">{{ kindInfo.description }}</p>
      <label class="fa-ident__field">
        <span class="fa-ident__label">{{ t('value') }}</span>
        <input :value="state.value" class="fa-ident__input" autocomplete="off" spellcheck="false" :maxlength="state.catalogue.limits.max_value_length" data-testid="ident-value" @input="controller.setField('value', typed($event))" />
      </label>
      <label v-if="kindNeedsCountry(state.catalogue, state.kind)" class="fa-ident__field">
        <span class="fa-ident__label">{{ t('country') }}</span>
        <input :value="state.country" class="fa-ident__input fa-ident__input--short" autocomplete="off" maxlength="3" :aria-describedby="`${id}-country`" data-testid="ident-country" @input="controller.setField('country', typed($event))" />
        <span :id="`${id}-country`" class="fa-ident__muted">{{ t('countryHelp') }}</span>
      </label>
      <p v-if="state.validation" class="fa-ident__error" role="alert">{{ t(identifierErrorKey(state.validation)) }}</p>
      <FaButton variant="primary" type="submit" :loading="state.busy === 'check'" data-testid="ident-check">{{ t('check') }}</FaButton>
    </form>
    <IdentifierResultView v-if="state.result" :result="state.result" />
  </section>
</template>
