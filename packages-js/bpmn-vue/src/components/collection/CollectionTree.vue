<script setup lang="ts">
/**
 * Diagram collection as folder tree with drag-and-drop, search and filters
 * by status and tag (legacy `BpmnDiagramTree`, now with real folders).
 */
import { computed, ref } from 'vue'
import { DIAGRAM_STATUS, label } from '@flowaudit/bpmn-flowaudit'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import type { CollectionStore } from '../../stores/collectionStore'
import PromptDialog from '../base/PromptDialog.vue'
import TreeFolder from './TreeFolder.vue'
import { readDrag } from './dragData'

const props = defineProps<{ store: CollectionStore; selectedDiagram: string | null; openDiagram: string | null }>()
const emit = defineEmits<{ (e: 'select-diagram', id: string | null): void; (e: 'open-diagram', id: string): void }>()
const { t, locale } = useI18n()
const overRoot = ref(false)
const prompt = ref<{ kind: 'folder' | 'diagram'; open: boolean }>({ kind: 'folder', open: false })

const tags = computed(() => [...props.store.collection.value.tags.values()])
const empty = computed(() => props.store.collection.value.diagrams.size === 0)

async function create(name: string): Promise<void> {
  const folder = props.store.selectedFolder.value
  if (prompt.value.kind === 'folder') {
    await props.store.createFolder(name, folder)
    return
  }
  const id = await props.store.createDiagram(name, folder)
  if (id) emit('open-diagram', id)
}

async function onDrop(payload: { kind: 'diagram' | 'folder'; id: string; target: { folderId: string | null; position?: number } }): Promise<void> {
  if (payload.kind === 'diagram') await props.store.moveDiagram(payload.id, payload.target.folderId, payload.target.position)
  else await props.store.moveFolder(payload.id, payload.target.folderId)
}

function dropOnRoot(event: DragEvent): void {
  overRoot.value = false
  const payload = readDrag(event)
  if (payload) void onDrop({ ...payload, target: { folderId: null } })
}

function selectFolder(id: string | null): void {
  props.store.selectedFolder.value = id
  emit('select-diagram', null)
}
</script>

<template>
  <nav class="fa-collection" :aria-label="t('collection.label')">
    <header class="fa-collection__head">
      <h2>{{ t('collection.label') }}</h2>
      <button type="button" class="fa-icon-btn" :title="t('collection.newFolder')" :aria-label="t('collection.newFolder')" @click="prompt = { kind: 'folder', open: true }"><FaIcon name="folder-new" /></button>
      <button type="button" class="fa-icon-btn" :title="t('collection.newDiagram')" :aria-label="t('collection.newDiagram')" @click="prompt = { kind: 'diagram', open: true }"><FaIcon name="new" /></button>
    </header>
    <div class="fa-collection__filters">
      <input v-model="store.filter.search" class="fa-input" type="search" :placeholder="t('common.search')" :aria-label="t('common.search')" />
      <div class="fa-grid-2">
        <select v-model="store.filter.status" class="fa-select" :aria-label="t('collection.filter.status')">
          <option value="">{{ t('collection.filter.status') }}: {{ t('common.all') }}</option>
          <option v-for="(text, code) in DIAGRAM_STATUS" :key="code" :value="code">{{ label(text, locale) }}</option>
        </select>
        <select v-model="store.filter.tag" class="fa-select" :aria-label="t('collection.filter.tag')">
          <option value="">{{ t('collection.filter.tag') }}: {{ t('common.all') }}</option>
          <option v-for="tag in tags" :key="tag.id" :value="tag.id">{{ tag.name }}</option>
        </select>
      </div>
    </div>
    <p v-if="store.error.value" class="fa-badge fa-badge--danger" role="alert">{{ store.error.value }}</p>
    <p v-if="store.loading.value" class="fa-help">{{ t('common.loading') }}</p>
    <p v-else-if="empty" class="fa-help fa-collection__empty">{{ t('collection.empty') }}</p>
    <div
      class="fa-collection__root"
      :class="{ 'fa-tree__row--over': overRoot, 'fa-tree__row--selected': store.selectedFolder.value === null }"
      @dragover.prevent="overRoot = true"
      @dragleave="overRoot = false"
      @drop.prevent="dropOnRoot"
    >
      <button type="button" class="fa-tree__label" @click="selectFolder(null)"><FaIcon name="overview" :size="16" />{{ t('collection.topLevel') }}</button>
    </div>
    <ul role="tree" class="fa-tree" :aria-label="t('collection.label')">
      <TreeFolder
        :node="store.tree.value"
        :depth="-1"
        :selected-diagram="selectedDiagram"
        :selected-folder="store.selectedFolder.value"
        :open-diagram="openDiagram"
        @select-diagram="emit('select-diagram', $event)"
        @open-diagram="emit('open-diagram', $event)"
        @select-folder="selectFolder"
        @drop="onDrop"
      />
    </ul>
    <PromptDialog
      v-model:open="prompt.open"
      :title="prompt.kind === 'folder' ? t('collection.newFolder') : t('collection.newDiagram')"
      :label="prompt.kind === 'folder' ? t('collection.folderName') : t('collection.diagramName')"
      @confirm="create"
    />
  </nav>
</template>

<style>
.fa-collection {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  padding: 10px;
  overflow: auto;
}

.fa-collection__head {
  display: flex;
  align-items: center;
  gap: 4px;
}

.fa-collection__head h2 {
  flex: 1;
  margin: 0;
  font-size: 14px;
  font-weight: 700;
}

.fa-collection__filters {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fa-collection__root {
  display: flex;
  border-radius: var(--fa-radius-sm);
  padding: 2px 6px;
}

.fa-tree {
  margin: 0;
  padding: 0;
  list-style: none;
}
</style>
