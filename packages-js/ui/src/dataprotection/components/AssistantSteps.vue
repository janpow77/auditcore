<script setup lang="ts">
import { stepReachable, type AssistantView } from '@auditcore/ui-core'
import { useI18n } from '../../i18n'
import { dataprotectionMessages, prefixedLabel } from '../core'

defineProps<{ view: AssistantView; busy: boolean }>()
const emit = defineEmits<{ select: [step: string] }>()
const { t } = useI18n(dataprotectionMessages)

</script>

<template>
  <nav class="fa-assistant__steps" :aria-label="t('stepsNav')">
    <ol>
      <li v-for="(step, index) in view.steps" :key="step.id">
        <button type="button" :aria-current="step.id === view.step?.id ? 'step' : undefined" :disabled="busy || !stepReachable(view, index)" @click="emit('select', step.id)">
          {{ step.title }}
          <span class="fa-assistant__badge">{{ prefixedLabel(t, 'stepStatus', step.status) }}</span>
        </button>
      </li>
    </ol>
  </nav>
</template>
