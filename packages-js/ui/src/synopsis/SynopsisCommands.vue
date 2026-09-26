<script setup lang="ts">
import type { SynopsisTranslate, SynopsisView } from '@flowaudit/ui-core'

/** Gesetzessynopse: offene Änderungsbefehle und konsolidierte Arbeitsfassung. */
defineProps<{ view: SynopsisView; t: SynopsisTranslate }>()
</script>

<template>
  <section v-if="view.openCommands.length" class="fa-synopsis-commands" :aria-label="t('openCommands')">
    <h3>{{ t('openCommands') }}</h3>
    <ol>
      <li v-for="command in view.openCommands" :key="command">{{ command }}</li>
    </ol>
  </section>
  <details v-if="view.consolidated.length" class="fa-synopsis-commands fa-synopsis-commands--consolidated">
    <summary>{{ t('consolidated') }}</summary>
    <dl>
      <template v-for="entry in view.consolidated" :key="`${entry.section}-${entry.paragraph}-${entry.inserted}`">
        <dt>
          {{ t('consolidatedEntry', { section: entry.section, paragraph: entry.paragraph }) }}
          <span v-if="entry.repealed">{{ t('repealed') }}</span>
          <span v-else-if="entry.inserted">{{ t('inserted') }}</span>
        </dt>
        <dd :class="{ 'fa-synopsis-commands__repealed': entry.repealed }">{{ entry.text }}</dd>
      </template>
    </dl>
  </details>
</template>
