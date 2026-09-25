<script setup lang="ts">
/** Search for elements by name, id, role or domain key; Enter jumps to the first hit. */
import { computed, ref } from 'vue'
import { displayName, type ProcessModel } from '@flowaudit/bpmn-flowaudit'
import BaseDialog from '../base/BaseDialog.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ open: boolean; model: ProcessModel | null }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'jump', id: string): void }>()
const { t } = useI18n()
const query = ref('')

function haystack(element: ProcessModel['elements'][number]): string {
  const ext = element.extensions
  return [
    element.id,
    element.name,
    element.actor?.role,
    element.actor?.displayName,
    ...ext.auditReferences.flatMap((r) => [`KA ${r.keyRequirement}`, `BK ${r.assessmentCriterion}`]),
    ...ext.crossReferences.map((r) => r.key),
    ...ext.findings.map((f) => f.reference),
  ]
    .filter(Boolean)
    .join(' ')
    .toLocaleLowerCase('de')
}

const hits = computed(() => {
  const needle = query.value.trim().toLocaleLowerCase('de')
  if (!props.model || !needle) return []
  return props.model.elements.filter((element) => !element.type.endsWith('Flow') && haystack(element).includes(needle)).slice(0, 50)
})

function jump(id: string): void {
  emit('jump', id)
  emit('update:open', false)
}
</script>

<template>
  <BaseDialog :open="open" :title="t('search.title')" width="520px" @update:open="emit('update:open', $event)">
    <input v-model="query" class="fa-input" type="search" :placeholder="t('search.placeholder')" :aria-label="t('search.title')" @keydown.enter.prevent="hits[0] && jump(hits[0].id)" />
    <ul class="fa-search__hits" role="listbox">
      <li v-for="hit in hits" :key="hit.id">
        <button type="button" role="option" class="fa-menu-item" @click="jump(hit.id)">
          <span>
            <strong>{{ displayName(hit) }}</strong>
            <span class="fa-menu-hint">{{ hit.type.replace('bpmn:', '') }} · {{ hit.id }}</span>
          </span>
        </button>
      </li>
    </ul>
    <p v-if="query.trim() && !hits.length" class="fa-help">{{ t('search.none') }}</p>
  </BaseDialog>
</template>

<style>
.fa-search__hits {
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
  max-height: 360px;
  overflow: auto;
}
</style>
