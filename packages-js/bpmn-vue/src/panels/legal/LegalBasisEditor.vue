<script setup lang="ts">
/**
 * Structured recording of legal bases (act, article/section, paragraph,
 * point, version, ELI/CELEX/URL, short title, note) with search
 * suggestions. 1.0 free text entries stay visible as legacy and can be
 * split into structured entries.
 */
import { ref } from 'vue'
import { citation, isStructured, shortCitation, splitFreeText, type LegalBasis, type LegalSearchPort } from '@flowaudit/bpmn-flowaudit'
import { addLegalBasis, LEGAL_FIELDS as FIELDS, removeLegalBasis, structureLegalBasis, updateLegalBasis } from '@flowaudit/bpmn-flowaudit/ui'
import FaIcon from '../../components/base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import FieldForm from '../FieldForm.vue'
import LegalSearch from './LegalSearch.vue'

const props = defineProps<{ items: LegalBasis[]; port?: LegalSearchPort; profileId?: string; disabled?: boolean }>()
const emit = defineEmits<{ (e: 'update', items: LegalBasis[]): void }>()
const { t } = useI18n()
const open = ref<number | null>(null)

const asRecord = (item: LegalBasis) => item as unknown as Record<string, unknown>

function add(value: LegalBasis): void {
  const next = addLegalBasis(props.items, value)
  if (!next) return
  emit('update', next)
  open.value = null
}

const update = (index: number, value: Record<string, unknown>) => emit('update', updateLegalBasis(props.items, index, value as LegalBasis))
const remove = (index: number) => emit('update', removeLegalBasis(props.items, index))

function structure(index: number): void {
  const next = structureLegalBasis(props.items, index)
  if (next) emit('update', next)
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
