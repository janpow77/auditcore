<script setup lang="ts">
/**
 * Editable list of FlowAudit entries (controls, risks, findings, …) from a
 * declarative `ListDescriptor`: collapsible items, add and remove.
 */
import { ref } from 'vue'
import FaIcon from '../components/base/FaIcon.vue'
import { useI18n } from '../i18n/useI18n'
import FieldForm from './FieldForm.vue'
import type { FieldDescriptor, ListDescriptor } from './descriptors'
import type { Option } from './useOptions'

const props = defineProps<{
  descriptor: ListDescriptor
  items: Record<string, unknown>[]
  optionsFor: (field: FieldDescriptor) => Option[]
  disabled?: boolean
}>()
const emit = defineEmits<{ (e: 'update', items: Record<string, unknown>[]): void }>()
const { t } = useI18n()
const open = ref<number | null>(null)

function update(index: number, value: Record<string, unknown>): void {
  emit('update', props.items.map((item, i) => (i === index ? value : item)))
}

function add(): void {
  emit('update', [...props.items, props.descriptor.create()])
  open.value = props.items.length
}

function remove(index: number): void {
  emit('update', props.items.filter((_, i) => i !== index))
  open.value = null
}

function toggle(index: number): void {
  open.value = open.value === index ? null : index
}
</script>

<template>
  <section class="fa-list-editor">
    <header class="fa-list-editor__head">
      <h3>{{ t(descriptor.title) }} <span class="fa-badge">{{ items.length }}</span></h3>
      <button type="button" class="fa-btn fa-btn--ghost" :disabled="disabled" @click="add">
        <FaIcon name="plus" :size="16" />{{ t('common.add') }}
      </button>
    </header>
    <p v-if="!items.length" class="fa-help">{{ t('common.empty') }}</p>
    <ul class="fa-list-editor__items">
      <li v-for="(item, index) in items" :key="index" class="fa-card">
        <div class="fa-list-editor__row">
          <button type="button" class="fa-list-editor__toggle" :aria-expanded="open === index" @click="toggle(index)">
            <FaIcon :name="open === index ? 'chevron-down' : 'chevron-right'" :size="16" />
            <span class="fa-list-editor__summary">{{ descriptor.summary(item) || t('common.new') }}</span>
            <span v-for="badge in descriptor.badges?.(item) ?? []" :key="badge" class="fa-badge fa-badge--info">{{ t(badge) }}</span>
          </button>
          <button type="button" class="fa-icon-btn" :disabled="disabled" :aria-label="t('common.remove')" @click="remove(index)">
            <FaIcon name="delete" :size="16" />
          </button>
        </div>
        <div v-if="open === index" class="fa-list-editor__form">
          <FieldForm :value="item" :fields="descriptor.fields" :options-for="optionsFor" :disabled="disabled" @update="update(index, $event)" />
        </div>
      </li>
    </ul>
  </section>
</template>

<style>
.fa-list-editor + .fa-list-editor {
  margin-top: 18px;
}

.fa-list-editor__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.fa-list-editor__head h3 {
  margin: 0;
  font-size: 13px;
  font-weight: 650;
}

.fa-list-editor__items {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.fa-list-editor__row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px;
}

.fa-list-editor__toggle {
  display: flex;
  flex: 1;
  align-items: center;
  gap: 6px;
  min-width: 0;
  padding: 6px 4px;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.fa-list-editor__summary {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fa-list-editor__form {
  padding: 4px 10px 12px;
  border-top: 1px solid var(--fa-border);
}
</style>
