<script setup lang="ts">
/** Right column: properties, issue list, walk-through and comparison as tabs. */
import type { Comment, PaletteColor } from '@flowaudit/bpmn-flowaudit'
import FaIcon from './base/FaIcon.vue'
import IssueList from './views/IssueList.vue'
import WalkthroughPanel from './views/WalkthroughPanel.vue'
import ComparePanel from './views/ComparePanel.vue'
import { SIDE_VIEWS as VIEWS, type CompareSource } from '@flowaudit/bpmn-flowaudit/ui'
import PropertiesPanel from '../panels/PropertiesPanel.vue'
import { useI18n } from '../i18n/useI18n'
import { useEditorContext } from '../stores/context'
import type { SideView } from '../composables/useEditorSetup'

defineProps<{ view: SideView; comments: Comment[]; author: string; compareSources: CompareSource[]; palette?: readonly PaletteColor[] }>()
const emit = defineEmits<{ (e: 'update:view', value: SideView): void; (e: 'update:comments', value: Comment[]): void; (e: 'jump', id: string): void }>()
const { validation } = useEditorContext()
const { t } = useI18n()

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
