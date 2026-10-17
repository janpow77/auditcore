<script setup lang="ts">
import type { Translate } from '@auditcore/sampling-templates-core'
import { FaButton } from '@auditcore/ui'
import type { SessionNotice } from '../composables/useSamplingSession'

/** Hinweise oberhalb des Rechenblatts: Beispielwerte, Meldungen beim Öffnen, Fehler. */
defineProps<{ notices: readonly SessionNotice[]; sample: boolean; t: Translate }>()
defineEmits<{ dismiss: [id: number]; clear: [] }>()
</script>

<template>
  <div v-if="sample || notices.length" class="fa-st__notices">
    <div v-if="sample" class="fa-st__notice" data-notice="sample">
      <p>{{ t('sampleNotice') }}</p>
      <FaButton size="sm" :label="t('emptyForm')" @click="$emit('clear')" />
    </div>
    <div v-for="notice in notices" :key="notice.id" class="fa-st__notice" :class="`fa-st__notice--${notice.tone}`" :role="notice.tone === 'danger' ? 'alert' : 'status'" :data-notice="notice.tone">
      <p>{{ notice.text }}</p>
      <FaButton size="sm" :label="t('close')" @click="$emit('dismiss', notice.id)" />
    </div>
  </div>
</template>
