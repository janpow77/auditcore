<script setup lang="ts">
import { watch } from 'vue'
import { DEFAULT_LIMITS, type Column } from '@flowaudit/kanban-core'
import FaButton from '../base/FaButton.vue'
import FaDialog from '../base/FaDialog.vue'
import { useI18n, type Locale } from '../i18n'
import ColumnEditorRow from './ColumnEditorRow.vue'
import { kanbanDialogMessages } from './messages'
import { useColumnEditor } from './useColumnEditor'

const props = withDefaults(defineProps<{ open: boolean; columns: readonly Column[]; locale?: Locale }>(), { locale: undefined })
const emit = defineEmits<{ close: []; save: [columns: Column[]] }>()
const { t } = useI18n(kanbanDialogMessages, () => props.locale)
const editor = useColumnEditor()
const { draft, problem, canAdd, canRemove, dirty, removed } = editor

watch(() => props.open, (open) => {
  if (open) editor.reset(props.columns)
}, { immediate: true })

function save(): void {
  const columns = editor.validated()
  if (columns) emit('save', columns)
}
</script>

<template>
  <FaDialog :open="open" :title="t('settingsTitle')" :description="t('settingsDescription')" size="lg" :locale="locale" @close="emit('close')">
    <p class="fa-kanban-detail__label">{{ t('columns', { count: draft.length, max: DEFAULT_LIMITS.columns_max }) }}</p>
    <ol class="fa-kanban-settings__list">
      <ColumnEditorRow
        v-for="(column, index) in draft"
        :key="column.id"
        :column="column"
        :first="index === 0"
        :last="index === draft.length - 1"
        :can-remove="canRemove"
        :locale="locale"
        @update="editor.update(index, $event)"
        @remove="editor.remove(index)"
        @move="editor.move(index, $event)"
      />
    </ol>
    <p v-if="removed.length" class="fa-kanban-settings__hint">{{ t('removedHint') }}</p>
    <p v-if="problem" class="fa-field__note" role="alert" style="color: var(--fa-color-danger)">{{ problem }}</p>
    <template #footer>
      <FaButton icon="plus" :disabled="!canAdd" @click="editor.add(t('newColumn'))">{{ t('addColumn') }}</FaButton>
      <span style="flex: 1" />
      <FaButton @click="emit('close')">{{ t('cancel') }}</FaButton>
      <FaButton variant="primary" :disabled="!dirty" data-testid="kanban-settings-save" @click="save">{{ t('save') }}</FaButton>
    </template>
  </FaDialog>
</template>
