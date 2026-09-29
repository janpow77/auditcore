<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref } from 'vue'
import { accountMessages, createAccountCamera, cropAccountImage } from '@auditcore/ui-core'
import { useI18n, type Locale } from '../i18n'
const props = defineProps<{ label: string; url: string; disabled: boolean; allowCamera: boolean; locale?: Locale }>()
const emit = defineEmits<{ upload: [file: Blob]; remove: [] }>()
const { t } = useI18n(accountMessages, () => props.locale)
const camera = createAccountCamera()
const active = ref(false)
const error = ref(false)
const original = ref<Blob | null>(null)
const zoom = ref(1)
const x = ref(0.5)
const y = ref(0.5)
async function crop() {
  try { if (original.value) emit('upload', await cropAccountImage(original.value, zoom.value, x.value, y.value)) }
  catch { error.value = true }
}
const video = ref<HTMLVideoElement | null>(null)
const stop = () => { camera.stop(); active.value = false }
async function start() {
  active.value = true; error.value = false
  await nextTick()
  try { if (video.value) await camera.start(video.value) } catch { error.value = true; stop() }
}
async function capture() {
  try { if (video.value) emit('upload', await camera.capture(video.value)); stop() }
  catch { error.value = true; stop() }
}
function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) { original.value = file; zoom.value = 1; x.value = y.value = 0.5; emit('upload', file) }
  input.value = ''
}
onBeforeUnmount(stop)
</script>
<template>
  <div class="fa-account__image">
    <img v-if="url" :src="url" :alt="label" width="96" height="96">
    <div v-else class="fa-account__avatar" aria-hidden="true">◎</div>
    <label>{{ t('upload') }}<input type="file" accept="image/png,image/jpeg,image/webp" :disabled="disabled" @change="upload"></label>
    <button v-if="allowCamera" type="button" :disabled="disabled" @click="start">{{ t('camera') }}</button>
    <button v-if="url" type="button" :disabled="disabled" @click="emit('remove')">{{ t('remove') }}</button>
    <div v-if="original" class="fa-account__crop">
      <label>{{ t('zoom') }}<input v-model.number="zoom" type="range" min="1" max="4" step="0.1"></label>
      <label>{{ t('horizontal') }}<input v-model.number="x" type="range" min="0" max="1" step="0.01"></label>
      <label>{{ t('vertical') }}<input v-model.number="y" type="range" min="0" max="1" step="0.01"></label>
      <button type="button" :disabled="disabled" @click="crop">{{ t('crop') }}</button>
    </div>
    <div v-if="active" class="fa-account__camera">
      <video ref="video" muted playsinline :aria-label="label" />
      <button type="button" :disabled="disabled" @click="capture">{{ t('capture') }}</button>
      <button type="button" @click="stop">{{ t('stop') }}</button>
    </div>
    <p v-if="error" role="alert">{{ t('cameraFailed') }}</p>
  </div>
</template>
