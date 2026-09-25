<script setup lang="ts">
/**
 * Workbench: diagram collection (folder tree, info column, group overview)
 * plus editor – the successor of the audit_designer view `BpmnEditor.vue`.
 * Persistence goes through the storage port.
 */
import { computed, onMounted, ref, toRaw, watch } from 'vue'
import type { Comment, ProfileData, ProfileSummary, RoleAlias, StoragePort, ValidationPort } from '@flowaudit/bpmn-flowaudit'
import type { EditorPorts } from '../stores/context'
import { createI18n, provideI18n, type Locale } from '../i18n/useI18n'
import { createCollectionStore } from '../stores/collectionStore'
import type { EditorFactory } from '../editor/createEditor'
import CollectionTree from './collection/CollectionTree.vue'
import DiagramInfoColumn from './collection/DiagramInfoColumn.vue'
import GroupOverview from './collection/GroupOverview.vue'
import FlowauditEditor from './FlowauditEditor.vue'
import '../styles/theme.css'

const props = withDefaults(
  defineProps<{
    storage: StoragePort
    profile?: ProfileData | null
    profiles?: ProfileSummary[]
    ports?: EditorPorts & { validation?: ValidationPort }
    locale?: Locale
    author?: string
    roleAliases?: RoleAlias[]
    editorFactory?: EditorFactory
  }>(),
  { profile: null, profiles: () => [], ports: () => ({}), locale: 'de', author: '', roleAliases: () => [] },
)
const emit = defineEmits<{ (e: 'open', id: string): void; (e: 'error', message: string): void }>()
const { t } = provideI18n(createI18n(props.locale))
// Ports are plain objects; a reactive proxy (e.g. from `reactive()`) would break cloning in the ports.
const storage = toRaw(props.storage)
const store = createCollectionStore(storage)

const selected = ref<string | null>(null)
const openId = ref<string | null>(null)
const xml = ref('')
const comments = ref<Comment[]>([])
const saving = ref(false)
const dirty = ref(false)

const selectedEntry = computed(() => (selected.value ? store.entry(selected.value) : undefined))
const openEntry = computed(() => (openId.value ? store.entry(openId.value) : undefined))
const compareSources = computed(() =>
  [...store.collection.value.diagrams.values()].filter((entry) => entry.id !== openId.value).map((entry) => ({ id: entry.id, name: entry.name, load: () => storage.loadDiagram(entry.id) })),
)
const folderTitle = computed(() => (store.selectedFolder.value ? store.collection.value.folders.get(store.selectedFolder.value)?.name ?? '' : t('collection.topLevel')))

async function open(id: string): Promise<void> {
  if (dirty.value && !window.confirm(t('workbench.discard'))) return
  xml.value = await storage.loadDiagram(id)
  comments.value = (await storage.loadComments?.(id)) ?? []
  openId.value = id
  selected.value = id
  dirty.value = false
  emit('open', id)
}

async function save(payload: { xml: string }): Promise<void> {
  if (!openId.value) return
  saving.value = true
  await store.saveDiagram(openId.value, payload.xml)
  await storage.saveComments?.(openId.value, comments.value)
  saving.value = false
  dirty.value = false
}

async function approve(payload: { xml: string; info: { version?: string; approvedBy?: string; approvedOn?: string; systemCutoffDate?: string } }): Promise<void> {
  if (!openId.value) return
  await save(payload)
  await store.approveDiagram(openId.value, payload.xml, payload.info.version ?? '1', { approvedBy: payload.info.approvedBy, approvedOn: payload.info.approvedOn, cutoffDate: payload.info.systemCutoffDate })
}

async function createAndOpen(): Promise<void> {
  const id = await store.createDiagram(t('collection.newDiagram'), store.selectedFolder.value)
  if (id) await open(id)
}

function onDeleted(): void {
  if (openId.value === selected.value) openId.value = null
  selected.value = null
}

function onXml(value: string): void {
  if (value !== xml.value) dirty.value = true
  xml.value = value
}

watch(store.error, (message) => message && emit('error', message))
onMounted(() => store.load())
</script>

<template>
  <div class="fa-root fa-workbench" :lang="locale">
    <aside class="fa-workbench__side">
      <CollectionTree :store="store" :selected-diagram="selected" :open-diagram="openId" @select-diagram="selected = $event" @open-diagram="open" />
    </aside>
    <main class="fa-workbench__main">
      <FlowauditEditor
        v-if="openEntry"
        :key="openEntry.id"
        :xml="xml"
        :name="openEntry.name"
        :diagram-id="openEntry.id"
        :profile="profile"
        :profiles="profiles"
        :ports="ports"
        :locale="locale"
        :comments="comments"
        :approvals="openEntry.approvals"
        :author="author"
        :compare-sources="compareSources"
        :role-aliases="roleAliases"
        :saving="saving"
        :editor-factory="editorFactory"
        @update:xml="onXml"
        @update:name="store.renameDiagram(openEntry.id, $event)"
        @update:comments="comments = $event"
        @save="save"
        @approve="approve"
        @new="createAndOpen"
      />
      <div v-else class="fa-workbench__overview">
        <GroupOverview :overview="store.overview.value" :profile="profile" :issues="store.issues.value" :title="folderTitle" @open="open" />
        <DiagramInfoColumn v-if="selectedEntry" class="fa-workbench__info" :store="store" :entry="selectedEntry" @open="open" @deleted="onDeleted" />
      </div>
    </main>
  </div>
</template>

<style>
.fa-workbench {
  display: flex;
  height: 100%;
  min-height: 560px;
  overflow: hidden;
}

.fa-workbench__side {
  display: flex;
  flex-direction: column;
  width: 300px;
  min-width: 240px;
  border-right: 1px solid var(--fa-border);
  background: var(--fa-surface);
  overflow: auto;
}

.fa-workbench__main {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
}

.fa-workbench__main > .fa-editor {
  flex: 1;
}

.fa-workbench__overview {
  display: flex;
  flex: 1;
  min-height: 0;
}

.fa-workbench__overview > .fa-overview {
  flex: 1;
  min-width: 0;
  overflow: auto;
}

.fa-workbench__info {
  width: 340px;
  flex-shrink: 0;
  border-left: 1px solid var(--fa-border);
  background: var(--fa-surface);
  overflow: auto;
}
</style>
