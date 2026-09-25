<script setup lang="ts">
/**
 * Structured recording of legal bases (act, article/section, paragraph,
 * point, version, ELI/CELEX/URL, short title, note) with search
 * suggestions. 1.0 free text entries stay visible as legacy and can be
 * split into structured entries.
 */
import { ref } from 'vue'
import {
  citation,
  findCitations,
  forWriting,
  isStructured,
  legalBasisKey,
  shortCitation,
  splitFreeText,
  type LegalBasis,
  type LegalSearchPort,
} from '@flowaudit/bpmn-flowaudit'
import FaIcon from '../../components/base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import FieldForm from '../FieldForm.vue'
import type { FieldDescriptor } from '../descriptors'
import LegalSearch from './LegalSearch.vue'

const props = defineProps<{ items: LegalBasis[]; port?: LegalSearchPort; profileId?: string; disabled?: boolean }>()
const emit = defineEmits<{ (e: 'update', items: LegalBasis[]): void }>()
const { t } = useI18n()
const open = ref<number | null>(null)

const legal = (key: string, extra: Partial<FieldDescriptor> = {}): FieldDescriptor => ({ key, label: `legal.${key}`, kind: 'text', ...extra })
const FIELDS: FieldDescriptor[] = [
  legal('act', { wide: true, placeholder: 'Verordnung (EU) 2021/1060' }),
  legal('article'),
  legal('section'),
  legal('annex'),
  legal('paragraph'),
  legal('subparagraph'),
  legal('sentence'),
  legal('point'),
  legal('number'),
  legal('version', { wide: true }),
  legal('celex'),
  legal('eli'),
  legal('url', { wide: true }),
  legal('shortTitle', { wide: true }),
  legal('note', { wide: true }),
  { key: 'confidential', label: 'field.confidential', kind: 'checkbox', wide: true },
]

const asRecord = (item: LegalBasis) => item as unknown as Record<string, unknown>

function emitItems(items: LegalBasis[]): void {
  emit('update', items.map(forWriting))
}

function add(value: LegalBasis): void {
  if (props.items.some((item) => legalBasisKey(item) === legalBasisKey(value))) return
  emitItems([...props.items, value])
  open.value = null
}

function update(index: number, value: Record<string, unknown>): void {
  // Structured edits regenerate the text; free text of the legacy form stays.
  const next = value as LegalBasis
  const previous = props.items[index]
  const regenerated = isStructured(next) && previous && previous.text === citation(previous) ? { ...next, text: undefined } : next
  emitItems(props.items.map((item, i) => (i === index ? regenerated : item)))
}

function remove(index: number): void {
  emitItems(props.items.filter((_, i) => i !== index))
}

/** Splits a legacy free text into structured entries (unrecognised parts stay text). */
function structure(index: number): void {
  const legacy = props.items[index]
  if (!legacy) return
  const parts = splitFreeText(legacy.text ?? '').flatMap((part) => {
    const hits = findCitations(part)
    return hits.length ? hits.map((hit) => hit.legalBasis) : [{ text: part }]
  })
  emitItems([...props.items.slice(0, index), ...parts, ...props.items.slice(index + 1)])
}
</script>

<template>
  <section class="fa-legal">
    <LegalSearch :port="port" :profile-id="profileId" :disabled="disabled" @choose="add" />
    <p v-if="!items.length" class="fa-help">{{ t('legal.empty') }}</p>
    <ul class="fa-list-editor__items fa-legal__items">
      <li v-for="(item, index) in items" :key="index" class="fa-card">
        <div class="fa-list-editor__row">
          <button type="button" class="fa-list-editor__toggle" :aria-expanded="open === index" @click="open = open === index ? null : index">
            <FaIcon :name="open === index ? 'chevron-down' : 'chevron-right'" :size="16" />
            <span class="fa-legal__text">
              <strong>{{ shortCitation(item) || item.text }}</strong>
              <span v-if="isStructured(item)" class="fa-menu-hint">{{ t('legal.long') }}: {{ citation(item) }}</span>
              <span v-else class="fa-badge fa-badge--warning">{{ t('legal.legacy') }}</span>
            </span>
          </button>
          <button type="button" class="fa-icon-btn" :disabled="disabled" :aria-label="t('common.remove')" @click="remove(index)">
            <FaIcon name="delete" :size="16" />
          </button>
        </div>
        <div v-if="open === index" class="fa-list-editor__form">
          <template v-if="!isStructured(item)">
            <p class="fa-help">{{ t('legal.legacyHelp') }}</p>
            <ul class="fa-legal__legacy">
              <li v-for="part in splitFreeText(item.text ?? '')" :key="part">{{ part }}</li>
            </ul>
            <button type="button" class="fa-btn" :disabled="disabled" @click="structure(index)">
              <FaIcon name="enrich" :size="16" />{{ t('legal.structure') }}
            </button>
          </template>
          <FieldForm v-else :value="asRecord(item)" :fields="FIELDS" :options-for="() => []" :disabled="disabled" @update="update(index, $event)" />
        </div>
      </li>
    </ul>
  </section>
</template>

<style>
.fa-legal__items {
  margin-top: 10px;
}

.fa-legal__text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.fa-legal__legacy {
  margin: 6px 0 10px;
  padding-left: 18px;
}
</style>
