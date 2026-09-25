<script setup lang="ts">
/** Right column: properties, issue list, walk-through and comparison as tabs. */
import type { Comment, PaletteColor } from '@flowaudit/bpmn-flowaudit'
import FaIcon from './base/FaIcon.vue'
import IssueList from './views/IssueList.vue'
import WalkthroughPanel from './views/WalkthroughPanel.vue'
import ComparePanel from './views/ComparePanel.vue'
import type { CompareSource } from './views/compareSource'
import PropertiesPanel from '../panels/PropertiesPanel.vue'
import { useI18n } from '../i18n/useI18n'
import { useEditorContext } from '../stores/context'
import type { SideView } from '../composables/useEditorSetup'

defineProps<{ view: SideView; comments: Comment[]; author: string; compareSources: CompareSource[]; palette?: readonly PaletteColor[] }>()
const emit = defineEmits<{ (e: 'update:view', value: SideView): void; (e: 'update:comments', value: Comment[]): void; (e: 'jump', id: string): void }>()
const { validation } = useEditorContext()
const { t } = useI18n()

const VIEWS: { id: SideView; label: string; icon: string }[] = [
  { id: 'properties', label: 'props.label', icon: 'info' },
  { id: 'issues', label: 'issues.label', icon: 'validate' },
  { id: 'walkthrough', label: 'walk.title', icon: 'play' },
  { id: 'compare', label: 'compare.title', icon: 'compare' },
]
</script>

<template>
  <div class="fa-side">
    <div class="fa-side__tabs" role="tablist">
      <button
        v-for="entry in VIEWS"
        :key="entry.id"
        type="button"
        role="tab"
        class="fa-side__tab"
        :aria-selected="view === entry.id"
        :title="t(entry.label)"
        @click="emit('update:view', entry.id)"
      >
        <FaIcon :name="entry.icon" :size="16" /><span class="fa-side__tab-label">{{ t(entry.label) }}</span>
        <span v-if="entry.id === 'issues' && validation.count.value.fehler" class="fa-badge fa-badge--danger">{{ validation.count.value.fehler }}</span>
      </button>
    </div>
    <div class="fa-side__body" role="tabpanel">
      <PropertiesPanel v-if="view === 'properties'" :comments="comments" :author="author" :palette="palette" @update:comments="emit('update:comments', $event)" />
      <div v-else class="fa-side__pad">
        <IssueList v-if="view === 'issues'" :issues="validation.issues.value" :running="validation.running.value" :error="validation.error.value" @jump="emit('jump', $event)" />
        <WalkthroughPanel v-else-if="view === 'walkthrough'" :tester="author" />
        <ComparePanel v-else :sources="compareSources" />
      </div>
    </div>
  </div>
</template>

<style>
.fa-side {
  display: flex;
  flex-direction: column;
  width: 420px;
  min-width: 320px;
  height: 100%;
  border-left: 1px solid var(--fa-border);
  background: var(--fa-surface);
}

.fa-side__tabs {
  display: flex;
  gap: 2px;
  padding: 4px 6px 0;
  border-bottom: 1px solid var(--fa-border);
  overflow-x: auto;
}

.fa-side__tab {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 8px 10px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--fa-text-muted);
  font: inherit;
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
}

.fa-side__tab:not([aria-selected='true']) .fa-side__tab-label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
}

.fa-side__tab[aria-selected='true'] {
  border-bottom-color: var(--fa-primary);
  color: var(--fa-text);
  font-weight: 600;
}

.fa-side__body {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.fa-side__pad {
  padding: 12px 14px;
}
</style>
