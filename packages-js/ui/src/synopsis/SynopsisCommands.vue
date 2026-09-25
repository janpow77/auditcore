<script setup lang="ts">
import type { SynopsisTranslate, SynopsisView } from './viewModel'

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

<style>
.fa-synopsis-commands { padding: var(--fa-space-3) var(--fa-space-4); border: 1px solid var(--fa-color-border); border-radius: var(--fa-radius); background: var(--fa-color-surface); font-size: var(--fa-font-size-sm); }
.fa-synopsis-commands h3 { margin: 0 0 var(--fa-space-2); font-size: var(--fa-font-size-md); }
.fa-synopsis-commands ol { margin: 0; padding-left: var(--fa-space-5); display: flex; flex-direction: column; gap: var(--fa-space-1); }
.fa-synopsis-commands summary { cursor: pointer; font-weight: 600; }
.fa-synopsis-commands summary:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); border-radius: var(--fa-radius-sm); }
.fa-synopsis-commands dl { margin: var(--fa-space-3) 0 0; }
.fa-synopsis-commands dt { font-weight: 600; margin-top: var(--fa-space-2); }
.fa-synopsis-commands dt span { font-weight: 400; color: var(--fa-color-text-muted); }
.fa-synopsis-commands dd { margin: 0; white-space: pre-wrap; }
.fa-synopsis-commands__repealed { text-decoration: line-through; color: var(--fa-color-text-muted); }
</style>
