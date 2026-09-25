<script setup lang="ts">
/** Keyboard shortcut help (declarative table). */
import BaseDialog from '../base/BaseDialog.vue'
import { useI18n } from '../../i18n/useI18n'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void }>()
const { t } = useI18n()

const SHORTCUTS: [string[], string][] = [
  [['@ctrl', 'S'], 'shortcuts.save'],
  [['@ctrl', 'Z'], 'shortcuts.undo'],
  [['@ctrl', 'Y'], 'shortcuts.redo'],
  [['@ctrl', 'F'], 'shortcuts.search'],
  [['@ctrl', 'C', '@ctrl', 'V'], 'shortcuts.copy'],
  [['@ctrl', 'A'], 'shortcuts.selectAll'],
  [['@del'], 'shortcuts.delete'],
  [['E'], 'shortcuts.edit'],
  [['H'], 'shortcuts.hand'],
  [['L'], 'shortcuts.lasso'],
  [['S'], 'shortcuts.space'],
  [['C'], 'shortcuts.connect'],
  [['@ctrl', '+', '/', '−'], 'shortcuts.zoom'],
  [['@ctrl', '0'], 'shortcuts.fit'],
  [['@ctrl', '←', '→', '↑', '↓'], 'shortcuts.move'],
  [['←', '→', '↑', '↓'], 'shortcuts.moveElement'],
  [['?'], 'shortcuts.help'],
]
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

<style>
.fa-shortcut__keys {
  white-space: nowrap;
}

.fa-shortcut__keys .fa-kbd + .fa-kbd {
  margin-left: 4px;
}
</style>
