<script setup lang="ts">
/**
 * Target/actual check and version comparison against another diagram (from
 * the collection or a file): synopsis table, binary result per element with
 * reasons, graphical diff in the canvas.
 */
import { computed, onBeforeUnmount, ref, shallowRef } from 'vue'
import {
  changeLabel,
  checkTargetActual,
  compareVersions,
  diffColors,
  HIGHLIGHT_CLASSES,
  loadDefinitions,
  modelFromDefinitions,
  synopsis,
  type Comparison,
  type FlowauditHighlight,
  type TargetActualCheck,
} from '@flowaudit/bpmn-flowaudit'
import FaIcon from '../base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'
import type { CompareSource } from './compareSource'

const props = defineProps<{ sources: CompareSource[] }>()
const { editor } = useEditorContext()
const { t } = useI18n()
const mode = ref<'version' | 'targetActual'>('targetActual')
const sourceId = ref('')
const fileXml = ref<string | null>(null)
const comparison = shallowRef<Comparison | null>(null)
const check = shallowRef<TargetActualCheck | null>(null)
const error = ref<string | null>(null)

const rows = computed(() => (comparison.value ? synopsis(comparison.value) : []))
const layer = () => editor.editor.value?.get<FlowauditHighlight>('flowauditHighlight', false)

async function otherXml(): Promise<string | null> {
  if (fileXml.value) return fileXml.value
  return (await props.sources.find((source) => source.id === sourceId.value)?.load()) ?? null
}

async function run(): Promise<void> {
  error.value = null
  try {
    const xml = await otherXml()
    if (!xml) return
    const other = modelFromDefinitions((await loadDefinitions(xml)).definitions)
    const current = editor.model()
    comparison.value = mode.value === 'version' ? compareVersions(other, current) : null
    check.value = mode.value === 'targetActual' ? checkTargetActual(other, current) : null
    paint()
  } catch (caught) {
    error.value = (caught as Error).message
  }
}

function paint(): void {
  const classes = new Map<string, string>()
  if (comparison.value) {
    const [, after] = diffColors(comparison.value)
    for (const [id, kind] of after) classes.set(id, HIGHLIGHT_CLASSES.diff[kind])
  }
  for (const result of check.value?.results ?? []) {
    if (result.actualId) classes.set(result.actualId, result.met ? HIGHLIGHT_CLASSES.walkthrough.erfuellt : HIGHLIGHT_CLASSES.walkthrough.nicht_erfuellt)
  }
  for (const id of check.value?.additionalInActual ?? []) classes.set(id, HIGHLIGHT_CLASSES.diff.hinzugefuegt)
  layer()?.apply('diff', classes)
}

async function onFile(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  fileXml.value = file ? await file.text() : null
  sourceId.value = ''
}

onBeforeUnmount(() => layer()?.clear('diff'))
</script>

<template>
  <section class="fa-compare" :aria-label="t('compare.title')">
    <div class="fa-segmented" role="radiogroup">
      <button type="button" role="radio" class="fa-btn fa-btn--ghost" :aria-checked="mode === 'targetActual'" @click="mode = 'targetActual'">{{ t('compare.mode.targetActual') }}</button>
      <button type="button" role="radio" class="fa-btn fa-btn--ghost" :aria-checked="mode === 'version'" @click="mode = 'version'">{{ t('compare.mode.version') }}</button>
    </div>
    <label class="fa-field fa-section">
      <span class="fa-label">{{ t('compare.other') }} ({{ t('compare.fromCollection') }})</span>
      <select v-model="sourceId" class="fa-select" @change="fileXml = null">
        <option value="">{{ t('common.none') }}</option>
        <option v-for="source in sources" :key="source.id" :value="source.id">{{ source.name }}</option>
      </select>
    </label>
    <label class="fa-btn fa-section"><FaIcon name="import" :size="16" />{{ t('compare.fromFile') }}<input type="file" accept=".bpmn,.xml" class="fa-sr-only" @change="onFile" /></label>
    <button type="button" class="fa-btn fa-btn--primary fa-section" :disabled="!sourceId && !fileXml" @click="run"><FaIcon name="compare" :size="16" />{{ t('compare.run') }}</button>
    <p class="fa-help">{{ t('compare.hint') }}</p>
    <p v-if="error" class="fa-badge fa-badge--danger">{{ error }}</p>
    <template v-if="check">
      <p class="fa-badge fa-badge--info" role="status">{{ t('compare.summary', { met: check.met, notMet: check.notMet, extra: check.additionalInActual.length }) }}</p>
      <ul class="fa-compare__results">
        <li v-for="result in check.results" :key="result.targetId" :class="result.met ? 'fa-compare__met' : 'fa-compare__not-met'">
          <FaIcon :name="result.met ? 'check' : 'close'" :size="14" />
          <strong>{{ result.name }}</strong>
          <span v-for="reason in result.reasons" :key="reason" class="fa-help">{{ reason }}</span>
        </li>
      </ul>
    </template>
    <template v-if="comparison">
      <p v-if="!rows.length" class="fa-help">{{ t('compare.unchanged') }}</p>
      <table v-else class="fa-table">
        <thead><tr><th>{{ t('compare.element') }}</th><th>{{ t('compare.field') }}</th><th>{{ t('compare.before') }}</th><th>{{ t('compare.after') }}</th><th>{{ t('compare.change') }}</th></tr></thead>
        <tbody>
          <tr v-for="(row, position) in rows" :key="position"><td>{{ row.element }}</td><td>{{ row.field }}</td><td>{{ row.before }}</td><td>{{ row.after }}</td><td>{{ row.change }}</td></tr>
        </tbody>
      </table>
      <p class="fa-compare__legend">
        <span class="fa-badge fa-badge--success">{{ changeLabel('hinzugefuegt') }}</span>
        <span class="fa-badge fa-badge--danger">{{ changeLabel('entfallen') }}</span>
        <span class="fa-badge fa-badge--warning">{{ changeLabel('geaendert') }}</span>
      </p>
    </template>
  </section>
</template>

<style>
.fa-compare__results {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
}

.fa-compare__results li {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 8px;
  align-items: baseline;
  padding: 6px 8px;
  border-left: 3px solid;
  border-radius: 4px;
  background: var(--fa-surface-2);
}

.fa-compare__met {
  border-color: var(--fa-success) !important;
}

.fa-compare__not-met {
  border-color: var(--fa-danger) !important;
}

.fa-compare__legend {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}
</style>
