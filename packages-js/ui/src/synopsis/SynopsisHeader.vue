<script setup lang="ts">
import FaIcon from '../base/FaIcon.vue'
import type { SynopsisTranslate, SynopsisView } from './viewModel'

defineProps<{ view: SynopsisView; selectedText: string; editable: boolean; headingId: string; t: SynopsisTranslate }>()
</script>

<template>
  <header class="fa-synopsis-header">
    <h2 :id="headingId" class="fa-synopsis-header__title">{{ view.title }}</h2>
    <p class="fa-synopsis-header__files">{{ view.filesText }}</p>
    <p class="fa-synopsis-header__counts">{{ view.countsText }}</p>
    <p class="fa-synopsis-header__meta">{{ view.detectedText }}</p>
    <p class="fa-synopsis-header__meta fa-synopsis-header__hash">{{ view.hashesText }}</p>
    <p v-if="editable" class="fa-synopsis-header__meta">{{ selectedText }}</p>
    <p v-if="view.isArticleLaw" class="fa-synopsis-header__commands">
      {{ t('commands', { recognised: view.recognisedCommands, open: view.openCommands.length }) }}
    </p>
    <ul class="fa-synopsis-header__notices">
      <li v-for="notice in view.notices" :key="notice"><FaIcon name="info" :size="16" /> <span>{{ notice }}</span></li>
    </ul>
  </header>
</template>

<style>
.fa-synopsis-header { display: flex; flex-direction: column; gap: var(--fa-space-1); }
.fa-synopsis-header__title { margin: 0; font-size: var(--fa-font-size-lg); line-height: 1.3; }
.fa-synopsis-header p { margin: 0; }
.fa-synopsis-header__files { font-weight: 600; overflow-wrap: anywhere; }
.fa-synopsis-header__counts { color: var(--fa-color-text); }
.fa-synopsis-header__meta { font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-synopsis-header__hash { font-family: var(--fa-font-mono); overflow-wrap: anywhere; }
.fa-synopsis-header__commands { margin-top: var(--fa-space-2) !important; padding: var(--fa-space-2) var(--fa-space-3); border-radius: var(--fa-radius-sm); background: var(--fa-color-warning-soft); color: var(--fa-color-text); }
.fa-synopsis-header__notices { display: flex; flex-direction: column; gap: var(--fa-space-2); margin: var(--fa-space-2) 0 0; padding: 0; list-style: none; }
.fa-synopsis-header__notices li { display: flex; gap: var(--fa-space-2); align-items: flex-start; padding: var(--fa-space-2) var(--fa-space-3); border-left: 4px solid var(--fa-color-warning); border-radius: var(--fa-radius-sm); background: var(--fa-color-warning-soft); font-size: var(--fa-font-size-sm); }
.fa-synopsis-header__notices .fa-icon { flex: none; margin-top: 0.15rem; color: var(--fa-color-warning); }
</style>
