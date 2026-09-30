<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { applyTheme, readTheme, resolvedTheme, FaIcon, type ThemeMode } from '@auditcore/ui'

type ThemeTarget = 'auditcore' | 'data-theme' | 'class'
const props = withDefaults(defineProps<{ storageKey?: string; label?: string; target?: ThemeTarget }>(), {
  storageKey: 'fa-theme',
  label: 'Farbschema wechseln',
  target: 'auditcore',
})
const emit = defineEmits<{ change: [mode: 'light' | 'dark'] }>()
const dark = ref(false)
const icon = computed(() => dark.value ? 'sun' : 'moon')
let media: MediaQueryList | null = null

function savedTheme(): 'light' | 'dark' | null {
  try {
    const saved = localStorage.getItem(props.storageKey)
    return saved === 'light' || saved === 'dark' ? saved : null
  } catch {
    return null
  }
}

function setDark(value: boolean): void {
  dark.value = value
  const mode: ThemeMode = value ? 'dark' : 'light'
  const root = document.documentElement
  applyTheme(mode, root)
  if (props.target === 'data-theme') root.dataset.theme = mode
  if (props.target === 'class') root.classList.toggle('dark', value)
}

function onSystemChange(event: MediaQueryListEvent): void {
  if (!savedTheme()) setDark(event.matches)
}

function onStorage(event: StorageEvent): void {
  if (event.key !== props.storageKey && event.key !== null) return
  const saved = savedTheme()
  if (saved) setDark(saved === 'dark')
}

onMounted(() => {
  const saved = savedTheme()
  const root = document.documentElement
  const existing = props.target === 'data-theme'
    ? (root.dataset.theme === 'light' || root.dataset.theme === 'dark' ? root.dataset.theme : null)
    : props.target === 'auditcore'
      ? (readTheme(root) === 'system' ? null : readTheme(root))
      : null
  if (saved) setDark(saved === 'dark')
  else if (existing) setDark(existing === 'dark')
  else {
    setDark(resolvedTheme() === 'dark')
    media = typeof window.matchMedia === 'function' ? window.matchMedia('(prefers-color-scheme: dark)') : null
    media?.addEventListener('change', onSystemChange)
  }
  window.addEventListener('storage', onStorage)
})

onBeforeUnmount(() => {
  media?.removeEventListener('change', onSystemChange)
  window.removeEventListener('storage', onStorage)
})

function toggle(): void {
  const next = dark.value ? 'light' : 'dark'
  setDark(next === 'dark')
  try {
    localStorage.setItem(props.storageKey, next)
  } catch {
    // The visible theme still works when browser storage is unavailable.
  }
  emit('change', next)
}
</script>

<template>
  <button class="fa-layout-theme-switch" type="button" :aria-label="label" :title="label" :aria-pressed="dark" @click="toggle">
    <FaIcon :name="icon" :size="18" />
    <span class="fa-layout-theme-switch__text">{{ dark ? 'Hellmodus' : 'Dunkelmodus' }}</span>
  </button>
</template>
