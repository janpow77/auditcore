<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { CHECKLIST_STATUSES, checklistChange, checklistEdit, checklistMeta, type ChecklistChange, type ChecklistItemView } from '@auditcore/ui-core'
import { formatDate, useI18n } from '../../i18n'
import { dataprotectionMessages, prefixedLabel } from '../core'

const props = defineProps<{ item: ChecklistItemView; busy: boolean }>()
const emit = defineEmits<{ change: [itemId: string, change: ChecklistChange] }>()
const { t, locale } = useI18n(dataprotectionMessages)

const edit = reactive(checklistEdit(props.item))
// Ein neuer Serverstand setzt die Eingaben zurück.
watch(() => props.item, (item) => Object.assign(edit, checklistEdit(item)))
const meta = computed(() => checklistMeta(t, props.item, (value, withTime) => formatDate(value, locale.value, withTime)))

function save(): void {
  emit('change', props.item.id, checklistChange(props.item, edit))
}
</script>

<template>
  <div class="fa-checklist__detail">
    <dl class="fa-dataprotection__dl">
      <template v-for="row in meta" :key="row.key">
        <dt>{{ row.label }}</dt>
        <dd>{{ row.value }}</dd>
      </template>
    </dl>
    <div class="fa-checklist__form">
      <label class="fa-dataprotection__field">{{ t('checklistStatus', { id: item.id }) }}<select v-model="edit.status">
        <option v-for="status in CHECKLIST_STATUSES" :key="status" :value="status">{{ prefixedLabel(t, 'item', status) }}</option>
      </select></label>
      <label class="fa-dataprotection__field">{{ t('evidenceIds') }}<input v-model="edit.evidence" type="text" /></label>
      <label class="fa-dataprotection__field">{{ t('checklistOwner') }}<input v-model="edit.owner" type="text" /></label>
      <label class="fa-dataprotection__field">{{ t('checklistDue') }}<input v-model="edit.due" type="date" /></label>
      <label class="fa-dataprotection__field fa-checklist__wide">{{ t('answerJustification') }}<textarea v-model="edit.justification" rows="2"></textarea></label>
      <button type="button" class="fa-checklist__save" :disabled="busy" @click="save">{{ t('saveItem') }}</button>
    </div>
  </div>
</template>
