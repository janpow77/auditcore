<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../i18n'
import { codeLabel, screeningMessages } from '../messages'
import type { ReviewStatus } from '../types'
import type { FilterOptions, HitFilter } from '../view'

const props = defineProps<{ modelValue: HitFilter; options: FilterOptions }>()
const emit = defineEmits<{ 'update:modelValue': [value: HitFilter] }>()
const { t } = useI18n(screeningMessages)

const single = (key: 'statuses' | 'lists' | 'subjects' | 'confidences') =>
  computed<string>({
    get: () => props.modelValue[key][0] ?? '',
    set: (value) => emit('update:modelValue', { ...props.modelValue, [key]: value ? [value] : [] }),
  })

const status = single('statuses')
const list = single('lists')
const subject = single('subjects')
const confidence = single('confidences')
const text = computed<string>({
  get: () => props.modelValue.text,
  set: (value) => emit('update:modelValue', { ...props.modelValue, text: value }),
})
const minScore = computed<string>({
  get: () => (props.modelValue.minScore === null ? '' : String(props.modelValue.minScore)),
  set: (value) => {
    const parsed = value === '' ? null : Number(value)
    emit('update:modelValue', { ...props.modelValue, minScore: Number.isFinite(parsed) ? parsed : null })
  },
})
const statuses: ReviewStatus[] = ['open', 'pending_second_review', 'confirmed', 'dismissed', 'deferred']
</script>

<template>
  <section class="fa-screening__panel" aria-labelledby="fa-screening-filter-title">
    <h3 id="fa-screening-filter-title">{{ t('filters') }}</h3>
    <div class="fa-screening__filters">
      <label class="fa-screening__field">
        <span>{{ t('filterStatus') }}</span>
        <select v-model="status">
          <option value="">{{ t('all') }}</option>
          <option v-for="key in statuses" :key="key" :value="key">{{ t(`status_${key}`) }}</option>
        </select>
      </label>
      <label class="fa-screening__field">
        <span>{{ t('filterList') }}</span>
        <select v-model="list">
          <option value="">{{ t('all') }}</option>
          <option v-for="l in options.lists" :key="l.key" :value="l.key">{{ l.name }}</option>
        </select>
      </label>
      <label class="fa-screening__field">
        <span>{{ t('filterSubject') }}</span>
        <select v-model="subject">
          <option value="">{{ t('all') }}</option>
          <option v-for="s in options.subjects" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
      </label>
      <label class="fa-screening__field">
        <span>{{ t('filterConfidence') }}</span>
        <select v-model="confidence">
          <option value="">{{ t('all') }}</option>
          <option v-for="c in options.confidences" :key="c" :value="c">{{ codeLabel(t, 'class', c) }}</option>
        </select>
      </label>
      <label class="fa-screening__field">
        <span>{{ t('filterMinScore') }}</span>
        <input v-model="minScore" type="number" step="any" inputmode="decimal" />
      </label>
      <label class="fa-screening__field">
        <span>{{ t('filterText') }}</span>
        <input v-model="text" type="search" />
      </label>
    </div>
  </section>
</template>
