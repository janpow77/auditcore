<script setup lang="ts">
import type { MessageKey, Translate } from '@auditcore/sampling-templates-core'
import { FaButton, useClickOutside, useId } from '@auditcore/ui'
import { computed, nextTick, ref } from 'vue'
import type { MenuAction } from '../types'

/** Menü „Arbeitsstand“: Öffnen, Speichern, Neu, Beispielwerte, lokalen Entwurf löschen. */
const props = defineProps<{ t: Translate; draft: boolean }>()
const emit = defineEmits<{ action: [action: MenuAction] }>()

interface Entry {
  action: MenuAction
  label: MessageKey
  hint?: MessageKey
  separated?: boolean
}
const ENTRIES: readonly Entry[] = [
  { action: 'open', label: 'menuOpen', hint: 'menuOpenHint' },
  { action: 'save', label: 'menuSave', hint: 'menuSaveHint' },
  { action: 'new', label: 'menuNew', separated: true },
  { action: 'sample', label: 'menuSample' },
  { action: 'clearDraft', label: 'menuClearDraft', separated: true },
]
const entries = computed(() => ENTRIES.filter((entry) => entry.action !== 'clearDraft' || props.draft))
const id = useId('fa-st-menu')
const open = ref(false)
const root = ref<HTMLElement | null>(null)
const items = ref<HTMLButtonElement[]>([])
const trigger = (): HTMLButtonElement | null => root.value?.querySelector('button') ?? null

useClickOutside(root, () => (open.value = false))

function show(index = 0): void {
  open.value = true
  void nextTick(() => items.value.at(index)?.focus())
}

function close(): void {
  open.value = false
  trigger()?.focus()
}

function choose(action: MenuAction): void {
  close()
  emit('action', action)
}

function onMenuKey(event: KeyboardEvent): void {
  const index = items.value.indexOf(document.activeElement as HTMLButtonElement)
  const last = items.value.length - 1
  const next: Record<string, number> = { ArrowDown: index >= last ? 0 : index + 1, ArrowUp: index <= 0 ? last : index - 1, Home: 0, End: last }
  if (event.key === 'Escape') close()
  else if (event.key === 'Tab') open.value = false
  else if (event.key in next) items.value[next[event.key] ?? 0]?.focus()
  else return
  if (event.key !== 'Tab') event.preventDefault()
}

function onTriggerKey(event: KeyboardEvent): void {
  if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return
  event.preventDefault()
  show(event.key === 'ArrowUp' ? -1 : 0)
}
</script>

<template>
  <div ref="root" class="fa-st__menu-wrap" @keydown="!open && onTriggerKey($event)">
    <FaButton icon="chevron-down" :label="t('menu')" aria-haspopup="menu" :aria-expanded="open" :aria-controls="open ? id : undefined" @click="open ? close() : show()" />
    <div v-if="open" :id="id" class="fa-st__menu" role="menu" :aria-label="t('menu')" @keydown="onMenuKey">
      <template v-for="entry in entries" :key="entry.action">
        <div v-if="entry.separated" class="fa-st__menu-sep" role="separator"></div>
        <button ref="items" type="button" class="fa-st__menu-item" role="menuitem" tabindex="-1" :data-action="entry.action" @click="choose(entry.action)">
          <span>{{ t(entry.label) }}</span>
          <span v-if="entry.hint" class="fa-st__muted">{{ t(entry.hint) }}</span>
        </button>
      </template>
    </div>
  </div>
</template>
