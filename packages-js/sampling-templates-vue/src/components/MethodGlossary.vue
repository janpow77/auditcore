<script setup lang="ts">
import type { MessageKey, Translate } from '@auditcore/sampling-templates-core'
import { useId } from '@auditcore/ui'

/** Kurzerklärungen der Fachbegriffe der Verfahrensauswahl, aufklappbar. */
defineProps<{ t: Translate }>()

const id = useId('fa-st-glossary')
const TERMS: readonly { term: MessageKey; text: MessageKey }[] = [
  { term: 'glossaryMus', text: 'glossaryMusText' },
  { term: 'glossaryPps', text: 'glossaryPpsText' },
  { term: 'glossarySrs', text: 'glossarySrsText' },
  { term: 'glossaryStart', text: 'glossaryStartText' },
]
</script>

<template>
  <section class="fa-st__glossary" :aria-labelledby="id" data-glossary>
    <h3 :id="id" class="fa-st__caption">{{ t('glossary') }}</h3>
    <details v-for="entry in TERMS" :key="entry.term" class="fa-st__glossary-item">
      <summary>{{ t(entry.term) }}</summary>
      <p>{{ t(entry.text) }}</p>
    </details>
  </section>
</template>
