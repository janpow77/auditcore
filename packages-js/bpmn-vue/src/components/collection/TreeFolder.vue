<script setup lang="ts">
/**
 * One folder of the collection tree (recursive): collapsible, drop target
 * for diagrams and folders, rows draggable (tree pattern with ARIA).
 */
import { ref } from 'vue'
import { DIAGRAM_STATUS, label, type DiagramEntry, type FolderNode } from '@flowaudit/bpmn-flowaudit'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import { readDrag, setDrag, type DropTarget } from './dragData'

const props = defineProps<{ node: FolderNode; depth: number; selectedDiagram: string | null; selectedFolder: string | null; openDiagram: string | null }>()
const emit = defineEmits<{
  (e: 'select-diagram', id: string): void
  (e: 'open-diagram', id: string): void
  (e: 'select-folder', id: string | null): void
  (e: 'drop', payload: { kind: 'diagram' | 'folder'; id: string; target: DropTarget }): void
}>()
const { t, locale } = useI18n()
const expanded = ref(true)
const over = ref(false)

const folderId = () => props.node.folder?.id ?? null

function onDrop(event: DragEvent, position?: number): void {
  over.value = false
  const payload = readDrag(event)
  if (payload && payload.id !== folderId()) emit('drop', { ...payload, target: { folderId: folderId(), position } })
}

function statusBadge(entry: DiagramEntry): string {
  const status = entry.info?.status
  return status === 'freigegeben' ? 'fa-badge--success' : status === 'in_pruefung' ? 'fa-badge--info' : status === 'archiviert' ? '' : 'fa-badge--warning'
}
</script>

<template>
  <li role="treeitem" :aria-expanded="node.folder ? expanded : undefined" class="fa-tree__folder">
    <div
      v-if="node.folder"
      class="fa-tree__row fa-tree__row--folder"
      :class="{ 'fa-tree__row--over': over, 'fa-tree__row--selected': selectedFolder === node.folder.id }"
      :style="{ paddingLeft: `${depth * 14 + 6}px` }"
      draggable="true"
      @dragstart="setDrag($event, 'folder', node.folder.id)"
      @dragover.prevent="over = true"
      @dragleave="over = false"
      @drop.prevent="onDrop($event)"
    >
      <button type="button" class="fa-tree__toggle" :aria-label="node.folder.name" @click="expanded = !expanded">
        <FaIcon :name="expanded ? 'chevron-down' : 'chevron-right'" :size="14" />
      </button>
      <button type="button" class="fa-tree__label" @click="emit('select-folder', node.folder.id)">
        <FaIcon :name="expanded ? 'folder-open' : 'folder'" :size="16" />
        <span>{{ node.folder.name }}</span>
      </button>
    </div>
    <ul v-show="expanded" role="group" class="fa-tree__children">
      <TreeFolder
        v-for="child in node.subfolders"
        :key="child.folder?.id"
        :node="child"
        :depth="depth + 1"
        :selected-diagram="selectedDiagram"
        :selected-folder="selectedFolder"
        :open-diagram="openDiagram"
        @select-diagram="emit('select-diagram', $event)"
        @open-diagram="emit('open-diagram', $event)"
        @select-folder="emit('select-folder', $event)"
        @drop="emit('drop', $event)"
      />
      <li v-for="(entry, index) in node.diagrams" :key="entry.id" role="treeitem" :aria-selected="selectedDiagram === entry.id">
        <div
          class="fa-tree__row"
          :class="{ 'fa-tree__row--selected': selectedDiagram === entry.id, 'fa-tree__row--open': openDiagram === entry.id }"
          :style="{ paddingLeft: `${(depth + 1) * 14 + 6}px` }"
          draggable="true"
          @dragstart="setDrag($event, 'diagram', entry.id)"
          @dragover.prevent
          @drop.prevent.stop="onDrop($event, index)"
        >
          <FaIcon name="grip" :size="14" class="fa-tree__grip" />
          <button type="button" class="fa-tree__label" @click="emit('select-diagram', entry.id)" @dblclick="emit('open-diagram', entry.id)" @keydown.enter="emit('open-diagram', entry.id)">
            <FaIcon name="diagram" :size="16" />
            <span class="fa-tree__name">{{ entry.name }}</span>
          </button>
          <span class="fa-badge" :class="statusBadge(entry)">{{ entry.info?.status ? label(DIAGRAM_STATUS[entry.info.status], locale) || entry.info.status : t('collection.status.ohne_status') }}</span>
        </div>
      </li>
    </ul>
  </li>
</template>

<style>
.fa-tree__children {
  margin: 0;
  padding: 0;
  list-style: none;
}

.fa-tree__row {
  display: flex;
  align-items: center;
  gap: 4px;
  min-height: 32px;
  padding-right: 6px;
  border-radius: var(--fa-radius-sm);
}

.fa-tree__row:hover {
  background: var(--fa-surface-2);
}

.fa-tree__row--selected {
  background: var(--fa-primary-soft);
}

.fa-tree__row--open .fa-tree__name {
  font-weight: 650;
}

.fa-tree__row--over {
  outline: 2px dashed var(--fa-primary);
}

.fa-tree__toggle,
.fa-tree__label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
}

.fa-tree__label {
  flex: 1;
  min-width: 0;
  padding: 4px 2px;
  text-align: left;
}

.fa-tree__name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fa-tree__grip {
  color: var(--fa-text-muted);
  cursor: grab;
}
</style>
