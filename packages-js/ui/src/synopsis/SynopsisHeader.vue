<script setup lang="ts">
import FaIcon from '../base/FaIcon.vue'
import type { SynopsisTranslate, SynopsisView } from '@flowaudit/ui-core'

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
