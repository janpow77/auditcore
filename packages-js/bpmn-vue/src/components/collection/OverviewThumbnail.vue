<script setup lang="ts">
/**
 * Thumbnail of one diagram in the folder overview: requested only once it
 * scrolls into view, shown as an image (never as inline SVG), a quiet
 * placeholder while loading or without a picture.
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import type { Thumbnails } from '@auditcore/bpmn-flowaudit/ui'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ diagramId: string; name: string; thumbnails: Thumbnails }>()
const { t } = useI18n()
const root = ref<HTMLElement | null>(null)
const url = ref<string | null>(null)
const state = ref<'waiting' | 'loading' | 'done'>('waiting')
let observer: IntersectionObserver | null = null

async function load(): Promise<void> {
  if (state.value !== 'waiting') return
  state.value = 'loading'
  url.value = await props.thumbnails.get(props.diagramId)
  state.value = 'done'
}

onMounted(() => {
  if (typeof IntersectionObserver === 'undefined' || !root.value) return void load()
  observer = new IntersectionObserver((entries) => entries.some((entry) => entry.isIntersecting) && (observer?.disconnect(), void load()), { rootMargin: '200px' })
  observer.observe(root.value)
})
onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <div ref="root" class="fa-thumb__image" :class="{ 'fa-thumb__image--loading': state === 'loading' }">
    <img v-if="url" :src="url" :alt="t('collection.overview.thumbnail', { name })" loading="lazy" decoding="async">
    <span v-else-if="state === 'done'" class="fa-thumb__empty">{{ t('collection.overview.noThumbnail') }}</span>
  </div>
</template>
