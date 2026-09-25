<script setup lang="ts">
/** ESI requirements per element (legacy `EsiRequirementsDialog`), loaded through the ESI port. */
import { computed, ref, watch } from 'vue'
import { groupByElement, normalizeEsiResponse, summarize, type EsiPort, type EsiRequirementResult, type EsiStatus } from '@flowaudit/bpmn-flowaudit'
import BaseDialog from '../base/BaseDialog.vue'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'

const props = defineProps<{ open: boolean; port?: EsiPort; xml: () => Promise<string>; diagramId?: string }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'jump', elementId: string): void }>()
const { t } = useI18n()
const list = ref<EsiRequirementResult[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const groups = computed(() => groupByElement(list.value))
const summary = computed(() => summarize(list.value))
const STATUS: Record<EsiStatus, { icon: string; label: string; badge: string }> = {
  fulfilled: { icon: 'check', label: 'esi.fulfilled', badge: 'fa-badge--success' },
  unclear: { icon: 'hint', label: 'esi.unclear', badge: 'fa-badge--warning' },
  missing: { icon: 'close', label: 'esi.missing', badge: 'fa-badge--danger' },
}

async function load(): Promise<void> {
  if (!props.port) return
  loading.value = true
  error.value = null
  try {
    list.value = normalizeEsiResponse(await props.port.requirements(await props.xml(), props.diagramId))
  } catch (caught) {
    error.value = (caught as Error).message
  } finally {
    loading.value = false
  }
}

watch(
  () => props.open,
  (open) => open && load(),
  { immediate: true },
)
</script>

<template>
  <BaseDialog :open="open" :title="t('esi.title')" :subtitle="t('esi.subtitle')" width="760px" @update:open="emit('update:open', $event)">
    <p v-if="!port" class="fa-help">{{ t('esi.noPort') }}</p>
    <template v-else>
      <div class="fa-esi__summary">
        <span class="fa-badge">{{ t('esi.total') }} {{ summary.total }}</span>
        <span class="fa-badge fa-badge--success">{{ t('esi.fulfilled') }} {{ summary.fulfilled }}</span>
        <span class="fa-badge fa-badge--warning">{{ t('esi.unclear') }} {{ summary.unclear }}</span>
        <span class="fa-badge fa-badge--danger">{{ t('esi.missing') }} {{ summary.missing }}</span>
        <button type="button" class="fa-btn fa-btn--ghost" :disabled="loading" @click="load">{{ loading ? t('common.loading') : t('esi.reload') }}</button>
      </div>
      <p v-if="error" class="fa-badge fa-badge--danger">{{ error }}</p>
      <p v-else-if="!loading && !groups.length" class="fa-help">{{ t('esi.none') }}</p>
      <section v-for="group in groups" :key="group.elementId" class="fa-card fa-esi__group">
        <header class="fa-esi__head">
          <div>
            <strong>{{ group.elementName }}</strong>
            <span class="fa-help"> · {{ group.elementId }} · {{ group.fulfilledCount }}/{{ group.totalCount }}</span>
          </div>
          <button type="button" class="fa-btn fa-btn--ghost" @click="(emit('jump', group.elementId), emit('update:open', false))">{{ t('issues.jump') }}</button>
        </header>
        <ul class="fa-esi__list">
          <li v-for="item in group.requirements" :key="item.requirementId">
            <span class="fa-badge" :class="STATUS[item.status].badge"><FaIcon :name="STATUS[item.status].icon" :size="12" />{{ t(STATUS[item.status].label) }}</span>
            <span>{{ item.description }}</span>
            <span v-if="item.expected !== null" class="fa-help">{{ t('esi.expected') }}: {{ item.expected }}</span>
            <span v-if="item.actual !== null" class="fa-help">{{ t('esi.actual') }}: {{ item.actual }}</span>
            <span v-else-if="item.expected !== null" class="fa-help">{{ t('esi.actualMissing') }}</span>
          </li>
        </ul>
      </section>
    </template>
  </BaseDialog>
</template>

<style>
.fa-esi__summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.fa-esi__group {
  margin-top: 8px;
  padding: 8px 10px;
}

.fa-esi__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.fa-esi__list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 6px 0 0;
  padding: 0;
  list-style: none;
}

.fa-esi__list li {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: baseline;
}
</style>
