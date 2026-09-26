<script setup lang="ts">
/**
 * Info column of the selected diagram: key info, tags, approvals and the
 * keyboard-accessible alternative to drag-and-drop („move to …“).
 */
import { computed, ref } from 'vue'
import type { DiagramEntry, Folder } from '@auditcore/bpmn-flowaudit'
import { infoRows, toggledTags } from '@auditcore/bpmn-flowaudit/ui'
import FaIcon from '../base/FaIcon.vue'
import PromptDialog from '../base/PromptDialog.vue'
import { useI18n } from '../../i18n/useI18n'
import type { CollectionStore } from '../../stores/collectionStore'

const props = defineProps<{ store: CollectionStore; entry: DiagramEntry }>()
const emit = defineEmits<{ (e: 'open', id: string): void; (e: 'deleted'): void }>()
const { t, locale } = useI18n()
const renaming = ref(false)
const tagging = ref(false)

const folders = computed<Folder[]>(() => [...props.store.collection.value.folders.values()])
const tags = computed(() => [...props.store.collection.value.tags.values()])
const rows = computed(() => infoRows(props.entry, t, locale.value))
const toggleTag = (id: string) => void props.store.setTags(props.entry.id, toggledTags(props.entry, id))

async function remove(): Promise<void> {
  if (!window.confirm(t('common.confirmDelete', { name: props.entry.name }))) return
  await props.store.removeDiagram(props.entry.id)
  emit('deleted')
}
</script>

<template>
  <section class="fa-info-column" :aria-label="t('collection.info')">
    <header class="fa-info-column__head">
      <h3>{{ entry.name }}</h3>
      <button type="button" class="fa-btn fa-btn--primary" @click="emit('open', entry.id)"><FaIcon name="folder-open" :size="16" />{{ t('collection.open') }}</button>
    </header>
    <dl class="fa-info-column__list">
      <template v-for="[term, value] in rows" :key="term">
        <dt>{{ term }}</dt>
        <dd>{{ value }}</dd>
      </template>
    </dl>
    <div class="fa-info-column__tags">
      <span v-for="tag in tags.filter((item) => entry.tags.includes(item.id))" :key="tag.id" class="fa-chip" :style="{ borderColor: tag.color }"><FaIcon name="tag" :size="12" />{{ tag.name }}</span>
    </div>
    <details class="fa-info-column__more">
      <summary>{{ t('collection.tags') }}</summary>
      <div class="fa-info-column__tags">
        <button v-for="tag in tags" :key="tag.id" type="button" class="fa-chip" :aria-pressed="entry.tags.includes(tag.id)" @click="toggleTag(tag.id)">{{ tag.name }}</button>
        <button type="button" class="fa-chip" @click="tagging = true"><FaIcon name="plus" :size="12" />{{ t('collection.newTag') }}</button>
      </div>
    </details>
    <label class="fa-field">
      <span class="fa-label">{{ t('collection.moveTo') }}</span>
      <select class="fa-select" :value="entry.folderId ?? ''" @change="store.moveDiagram(entry.id, ($event.target as HTMLSelectElement).value || null)">
        <option value="">{{ t('collection.topLevel') }}</option>
        <option v-for="folder in folders" :key="folder.id" :value="folder.id">{{ folder.name }}</option>
      </select>
    </label>
    <div v-if="entry.approvals.length" class="fa-info-column__approvals">
      <span class="fa-label">{{ t('collection.approvals') }}</span>
      <p v-for="approval in entry.approvals" :key="approval.version" class="fa-help"><FaIcon name="lock" :size="12" /> {{ approval.version }} · {{ approval.approvedOn }} · <code>{{ approval.sha256.slice(0, 16) }}…</code></p>
    </div>
    <div class="fa-info-column__actions">
      <button type="button" class="fa-btn" @click="renaming = true"><FaIcon name="new" :size="16" />{{ t('collection.rename') }}</button>
      <button type="button" class="fa-btn fa-btn--danger" @click="remove"><FaIcon name="delete" :size="16" />{{ t('common.delete') }}</button>
    </div>
    <PromptDialog v-model:open="renaming" :title="t('collection.rename')" :label="t('collection.diagramName')" :value="entry.name" @confirm="store.renameDiagram(entry.id, $event)" />
    <PromptDialog v-model:open="tagging" :title="t('collection.newTag')" :label="t('collection.tags')" @confirm="store.createTag($event)" />
  </section>
</template>
