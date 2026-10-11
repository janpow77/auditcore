<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { ChecklistChange, ChecklistItemView, ChecklistStatus } from '@auditcore/ui-core'
import { useI18n } from '../../i18n'
import { dataprotectionMessages, prefixedLabel } from '../core'

const emit = defineEmits<{ change: [itemId: string, change: ChecklistChange] }>()
const { t } = useI18n(dataprotectionMessages)

const STATUSES: ChecklistStatus[] = ['offen', 'in_bearbeitung', 'zur_pruefung', 'nachgewiesen', 'klaerungsbedarf', 'nicht_erfuellt', 'nicht_anwendbar', 'erneut_zu_pruefen']
interface Edit { status: ChecklistStatus; justification: string; evidence: string }
const props = defineProps<{ items: ChecklistItemView[]; busy: boolean }>()
const edits = reactive<Record<string, Edit>>({})

// Eingaben je Prüfpunkt; ein neuer Serverstand setzt sie zurück.
watch(() => props.items, (items) => {
  for (const item of items) edits[item.id] = { status: item.status, justification: item.justification, evidence: item.evidence_ids.join(', ') }
}, { immediate: true })

function edit(item: ChecklistItemView): Edit {
  return edits[item.id] ?? { status: item.status, justification: '', evidence: '' }
}

function save(item: ChecklistItemView): void {
  const current = edit(item)
  const evidence = current.evidence.split(',').map((entry) => entry.trim()).filter(Boolean)
  emit('change', item.id, { status: current.status, justification: current.justification, evidence_ids: evidence })
}
</script>

<template>
  <section class="fa-dataprotection__panel" data-testid="assistant-checklist" aria-labelledby="fa-assistant-checklist">
    <h3 id="fa-assistant-checklist">{{ t('checklistTitle') }}</h3>
    <table class="fa-dataprotection__table">
      <tbody>
        <tr v-for="item in items" :key="item.id" :data-item="item.id">
          <th scope="row">{{ item.id }}</th>
          <td>
            {{ item.titel }}
            <span v-if="item.sperrt" class="fa-assistant__badge">{{ t('itemBlocks', { gate: item.sperrt }) }}</span>
            <br /><span class="fa-dataprotection__muted">{{ prefixedLabel(t, 'item', item.status) }} · {{ item.zustaendig }}</span>
          </td>
          <td>
            <label>{{ t('checklistStatus', { id: item.id }) }}
              <select v-model="edit(item).status">
                <option v-for="status in STATUSES" :key="status" :value="status">{{ prefixedLabel(t, 'item', status) }}</option>
              </select>
            </label>
            <label>{{ t('evidenceIds') }} <input v-model="edit(item).evidence" type="text" /></label>
            <label>{{ t('answerJustification') }} <textarea v-model="edit(item).justification" rows="2"></textarea></label>
            <button type="button" :disabled="busy" @click="save(item)">{{ t('saveItem') }}</button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
