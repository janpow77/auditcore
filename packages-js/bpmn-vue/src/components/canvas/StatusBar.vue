<script setup lang="ts">
/** Status bar: zoom, issue counts (click opens the list), profile. */
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

defineProps<{ scale: number; count: { fehler: number; warnung: number; hinweis: number }; profile?: string; message?: string }>()
const emit = defineEmits<{ (e: 'issues'): void }>()
const { t } = useI18n()
</script>

<template>
  <footer class="fa-statusbar">
    <button type="button" class="fa-statusbar__issues" @click="emit('issues')">
      <FaIcon name="error" :size="14" /><span>{{ count.fehler }}</span>
      <FaIcon name="warning" :size="14" /><span>{{ count.warnung }}</span>
      <FaIcon name="hint" :size="14" /><span>{{ count.hinweis }}</span>
      <span class="fa-sr-only">{{ t('editor.status.issues', { errors: count.fehler, warnings: count.warnung, notes: count.hinweis }) }}</span>
    </button>
    <span class="fa-statusbar__message" role="status" aria-live="polite">{{ message }}</span>
    <span v-if="profile" class="fa-statusbar__item">{{ profile }}</span>
    <span class="fa-statusbar__item">{{ t('editor.status.zoom', { percent: Math.round(scale * 100) }) }}</span>
  </footer>
</template>
