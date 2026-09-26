<script setup lang="ts">
/** Keyboard shortcut help (declarative table). */
import BaseDialog from '../base/BaseDialog.vue'
import { SHORTCUTS } from '@auditcore/bpmn-flowaudit/ui'
import { useI18n } from '../../i18n/useI18n'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void }>()
const { t } = useI18n()

</script>

<template>
  <BaseDialog :open="open" :title="t('shortcuts.title')" width="480px" @update:open="emit('update:open', $event)">
    <table class="fa-table">
      <tbody>
        <tr v-for="[keys, label] in SHORTCUTS" :key="label">
          <td class="fa-shortcut__keys">
            <kbd v-for="(key, index) in keys" :key="index" class="fa-kbd">{{ key.startsWith('@') ? t(`key.${key.slice(1)}`) : key }}</kbd>
          </td>
          <td>{{ t(label) }}</td>
        </tr>
      </tbody>
    </table>
  </BaseDialog>
</template>
