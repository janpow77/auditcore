<script setup lang="ts">
/**
 * Properties panel with tabs (General, Role, Legal bases, Audit reference,
 * Control & risk, Evidence, Findings, Source, Notes, Colour). Tabs follow the
 * WAI-ARIA tabs pattern (arrow keys, Home/End).
 */
import { computed, ref, watch } from 'vue'
import type { Comment, PaletteColor } from '@flowaudit/bpmn-flowaudit'
import FaIcon from '../components/base/FaIcon.vue'
import { useI18n } from '../i18n/useI18n'
import { useEditorContext } from '../stores/context'
import { listsFor, tabsFor, type TabId } from './tabs'
import ColorTab from './tabs/ColorTab.vue'
import GeneralTab from './tabs/GeneralTab.vue'
import LegalTab from './tabs/LegalTab.vue'
import ListsTab from './tabs/ListsTab.vue'
import NotesTab from './tabs/NotesTab.vue'
import RoleTab from './tabs/RoleTab.vue'

defineProps<{ comments: Comment[]; author: string; palette?: readonly PaletteColor[] }>()
const emit = defineEmits<{ (e: 'update:comments', value: Comment[]): void }>()
const { selection } = useEditorContext()
const { t } = useI18n()

const active = ref<TabId>('general')
const type = computed(() => selection.type.value)
const tabs = computed(() => tabsFor(type.value))
const current = computed(() => tabs.value.find((tab) => tab.id === active.value) ?? tabs.value[0])
const tabRefs = ref<HTMLElement[]>([])

watch(tabs, (list) => {
  if (!list.some((tab) => tab.id === active.value)) active.value = 'general'
})

function onKey(event: KeyboardEvent, index: number): void {
  const moves: Record<string, number> = { ArrowRight: index + 1, ArrowDown: index + 1, ArrowLeft: index - 1, ArrowUp: index - 1, Home: 0, End: tabs.value.length - 1 }
  const move = moves[event.key]
  if (move === undefined) return
  event.preventDefault()
  const next = (move + tabs.value.length) % tabs.value.length
  const tab = tabs.value[next]
  if (tab) active.value = tab.id
  tabRefs.value[next]?.focus()
}
</script>

<template>
  <aside class="fa-props" :aria-label="t('props.label')">
    <p v-if="!selection.element.value" class="fa-props__empty">{{ t('editor.noSelection') }}</p>
    <template v-else>
      <div class="fa-props__tabs" role="tablist" aria-orientation="vertical" :aria-label="t('props.label')">
        <button
          v-for="(tab, index) in tabs"
          :id="`fa-tab-${tab.id}`"
          :key="tab.id"
          :ref="(el) => (tabRefs[index] = el as HTMLElement)"
          type="button"
          role="tab"
          class="fa-props__tab"
          :aria-selected="current?.id === tab.id"
          :aria-controls="`fa-tabpanel-${tab.id}`"
          :tabindex="current?.id === tab.id ? 0 : -1"
          :title="t(tab.label)"
          @click="active = tab.id"
          @keydown="onKey($event, index)"
        >
          <FaIcon :name="tab.icon" :size="18" />
          <span class="fa-props__tab-label">{{ t(tab.label) }}</span>
        </button>
      </div>
      <section v-if="current" :id="`fa-tabpanel-${current.id}`" class="fa-props__panel" role="tabpanel" :aria-labelledby="`fa-tab-${current.id}`" tabindex="0">
        <h2 class="fa-props__title">{{ t(current.label) }}</h2>
        <GeneralTab v-if="current.id === 'general'" />
        <RoleTab v-else-if="current.id === 'role'" />
        <LegalTab v-else-if="current.id === 'legal'" />
        <NotesTab v-else-if="current.id === 'notes'" :comments="comments" :author="author" @update:comments="emit('update:comments', $event)" />
        <ColorTab v-else-if="current.id === 'color'" :palette="palette" />
        <ListsTab v-else :lists="listsFor(current, type ?? '')" />
      </section>
    </template>
  </aside>
</template>

<style>
.fa-props {
  display: flex;
  height: 100%;
  min-height: 0;
  background: var(--fa-surface);
}

.fa-props__empty {
  margin: 16px;
  color: var(--fa-text-muted);
}

.fa-props__tabs {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 44px;
  padding: 6px 4px;
  border-right: 1px solid var(--fa-border);
  background: var(--fa-surface-2);
}

.fa-props__tab {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid transparent;
  border-radius: var(--fa-radius-sm);
  background: transparent;
  color: var(--fa-text-muted);
  cursor: pointer;
}

.fa-props__tab[aria-selected='true'] {
  background: var(--fa-surface);
  border-color: var(--fa-border);
  color: var(--fa-primary);
  box-shadow: var(--fa-shadow-sm);
}

.fa-props__tab-label {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
}

.fa-props__panel {
  flex: 1;
  min-width: 0;
  padding: 12px 14px 24px;
  overflow: auto;
}

.fa-props__title {
  margin: 0 0 10px;
  font-size: 15px;
  font-weight: 650;
}
</style>
