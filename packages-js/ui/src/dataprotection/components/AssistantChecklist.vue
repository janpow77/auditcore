<script setup lang="ts">
import { computed, ref } from 'vue'
import { checklistBranchIds, checklistProgress, checklistTree, toggleChecklistNode, type ChecklistChange, type ChecklistItemView } from '@auditcore/ui-core'
import { useI18n } from '../../i18n'
import { dataprotectionMessages } from '../core'
import AssistantChecklistNode from './AssistantChecklistNode.vue'

const emit = defineEmits<{ change: [itemId: string, change: ChecklistChange] }>()
const props = defineProps<{ items: ChecklistItemView[]; busy: boolean }>()
const { t } = useI18n(dataprotectionMessages)

const tree = computed(() => checklistTree(props.items))
const progress = computed(() => checklistProgress(tree.value))
// Bereiche sind anfangs offen, Prüfpunkte zu; der Zustand übersteht neue Serverstände.
const expanded = ref<ReadonlySet<string>>(new Set(checklistBranchIds(tree.value)))

function toggle(id: string): void {
  expanded.value = toggleChecklistNode(expanded.value, id)
}
</script>

<template>
  <section class="fa-dataprotection__panel fa-checklist" data-testid="assistant-checklist" aria-labelledby="fa-assistant-checklist">
    <div class="fa-dataprotection__bar fa-checklist__head">
      <h3 id="fa-assistant-checklist">{{ t('checklistTitle') }}</h3>
      <span class="fa-dataprotection__muted">{{ t('checklistProgress', { settled: progress.settled, total: progress.total }) }}</span>
      <span v-if="progress.attention" class="fa-checklist__status fa-checklist__status--attention">{{ t('checklistAttention', { count: progress.attention }) }}</span>
      <div class="fa-dataprotection__actions">
        <button type="button" @click="expanded = new Set(checklistBranchIds(tree))">{{ t('checklistExpandAll') }}</button>
        <button type="button" @click="expanded = new Set()">{{ t('checklistCollapseAll') }}</button>
      </div>
    </div>
    <ul class="fa-checklist__tree">
      <AssistantChecklistNode v-for="node in tree" :key="node.id" :node="node" :expanded="expanded" :busy="busy" @toggle="toggle" @change="(id, change) => emit('change', id, change)" />
    </ul>
  </section>
</template>
