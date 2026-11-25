<script setup lang="ts">
import type { ChecklistChange, ChecklistTreeNode } from '@auditcore/ui-core'
import { useI18n } from '../../i18n'
import { dataprotectionMessages, prefixedLabel } from '../core'
import AssistantChecklistDetail from './AssistantChecklistDetail.vue'

// Rekursiver Knoten: Bereiche zeigen ihre Kinder, Prüfpunkte ihre Detailansicht.
defineProps<{ node: ChecklistTreeNode; expanded: ReadonlySet<string>; busy: boolean }>()
const emit = defineEmits<{ toggle: [id: string]; change: [itemId: string, change: ChecklistChange] }>()
const { t } = useI18n(dataprotectionMessages)
</script>

<template>
  <li class="fa-checklist__node" :class="`fa-checklist__node--${node.kind}`" :data-node="node.id" :data-item="node.item?.id">
    <button type="button" class="fa-checklist__row" :aria-expanded="expanded.has(node.id)" @click="emit('toggle', node.id)">
      <span class="fa-checklist__chevron" aria-hidden="true">▸</span>
      <span class="fa-checklist__dot" :class="`fa-checklist__dot--${node.tone}`" aria-hidden="true"></span>
      <template v-if="node.item">
        <span class="fa-checklist__key">{{ node.item.id }}</span>
        <span class="fa-checklist__title">{{ node.label }}</span>
        <span v-if="node.item.sperrt" class="fa-assistant__badge">{{ t('itemBlocks', { gate: node.item.sperrt }) }}</span>
        <span class="fa-checklist__status" :class="`fa-checklist__status--${node.tone}`">{{ prefixedLabel(t, 'item', node.item.status) }}</span>
      </template>
      <template v-else>
        <span class="fa-checklist__title">{{ t('checklistArea', { area: node.label }) }}</span>
        <span v-if="node.progress.attention" class="fa-checklist__status fa-checklist__status--attention">{{ t('checklistAttention', { count: node.progress.attention }) }}</span>
        <span class="fa-checklist__status" :class="`fa-checklist__status--${node.tone}`">{{ t('checklistProgress', { settled: node.progress.settled, total: node.progress.total }) }}</span>
      </template>
    </button>
    <template v-if="expanded.has(node.id)">
      <AssistantChecklistDetail v-if="node.item" :item="node.item" :busy="busy" @change="(id, change) => emit('change', id, change)" />
      <ul v-else class="fa-checklist__children">
        <AssistantChecklistNode v-for="child in node.children" :key="child.id" :node="child" :expanded="expanded" :busy="busy" @toggle="emit('toggle', $event)" @change="(id, change) => emit('change', id, change)" />
      </ul>
    </template>
  </li>
</template>
