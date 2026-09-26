<script setup lang="ts">
/** Search for elements by name, id, role or domain key; Enter jumps to the first hit. */
import { computed, ref } from 'vue'
import { displayName, type ProcessModel } from '@auditcore/bpmn-flowaudit'
import { searchElements } from '@auditcore/bpmn-flowaudit/ui'
import BaseDialog from '../base/BaseDialog.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ open: boolean; model: ProcessModel | null }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'jump', id: string): void }>()
const { t } = useI18n()
const query = ref('')

const hits = computed(() => searchElements(props.model, query.value))

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
