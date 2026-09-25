<script setup lang="ts">
/**
 * Walk-through test: go through the diagram step by step, record per step
 * case, voucher, result and remark (`flowaudit:pruefschritt`); key controls
 * of the step with sample size for the control test. Steps are highlighted
 * in the diagram (current, met, not met).
 */
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { HIGHLIGHT_CLASSES, nextStepId, recordStep, walkthroughProgress, walkthroughSteps, type AuditStep, type FlowauditHighlight } from '@flowaudit/bpmn-flowaudit'
import FaIcon from '../base/FaIcon.vue'
import FieldForm from '../../panels/FieldForm.vue'
import { AUDIT_STEP_LIST } from '../../panels/descriptors'
import { useOptions } from '../../panels/useOptions'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'

const props = defineProps<{ tester?: string }>()
const { editor, profile, ports, readonly } = useEditorContext()
const { t, locale } = useI18n()
const { optionsFor } = useOptions({ profile, catalogue: ports.catalogue, locale })

const index = ref(0)
const draft = ref<AuditStep>({})
const steps = computed(() => {
  void editor.state.changes
  return editor.state.ready ? walkthroughSteps(editor.model()) : []
})
const current = computed(() => steps.value[index.value])
const progress = computed(() => walkthroughProgress(steps.value))
const FIELDS = AUDIT_STEP_LIST.fields.filter((field) => field.key !== 'id')

function highlight(): void {
  if (!editor.state.ready) return
  const layer = editor.editor.value?.get<FlowauditHighlight>('flowauditHighlight', false)
  if (!layer) return
  const classes = new Map<string, string>(steps.value.map((step) => [step.elementId, HIGHLIGHT_CLASSES.walkthrough[step.status]]))
  if (current.value) classes.set(current.value.elementId, HIGHLIGHT_CLASSES.walkthrough.current)
  layer.apply('walkthrough', classes)
}

function go(step: number): void {
  index.value = Math.max(0, Math.min(step, steps.value.length - 1))
  draft.value = { tester: props.tester, date: new Date().toISOString().slice(0, 10), result: 'erfuellt' }
  if (current.value) editor.select(current.value.elementId)
}

function save(): void {
  if (!current.value) return
  recordStep(editor.access(), current.value.elementId, { id: nextStepId(editor.model()), ...draft.value })
  go(index.value + 1)
}

watch([steps, index], highlight, { immediate: true })
onBeforeUnmount(() => editor.editor.value?.get<FlowauditHighlight>('flowauditHighlight', false)?.clear('walkthrough'))
go(0)
</script>

<template>
  <section class="fa-walk" :aria-label="t('walk.title')">
    <p class="fa-help" role="status">{{ t('walk.progress', { ...progress }) }}</p>
    <div class="fa-walk__bar" :style="{ '--done': `${progress.total ? (progress.done / progress.total) * 100 : 0}%` }" aria-hidden="true" />
    <p v-if="!steps.length" class="fa-help">{{ t('walk.noSteps') }}</p>
    <template v-else-if="current">
      <div class="fa-walk__nav">
        <button type="button" class="fa-icon-btn" :disabled="index === 0" :aria-label="t('walk.previous')" @click="go(index - 1)"><FaIcon name="step-back" /></button>
        <div class="fa-walk__current">
          <span class="fa-help">{{ index + 1 }} / {{ steps.length }}</span>
          <strong>{{ current.name }}</strong>
          <span class="fa-badge">{{ t(`walk.status.${current.status}`) }}</span>
        </div>
        <button type="button" class="fa-icon-btn" :disabled="index >= steps.length - 1" :aria-label="t('walk.next')" @click="go(index + 1)"><FaIcon name="step-forward" /></button>
      </div>
      <div v-if="current.keyControls.length" class="fa-card fa-walk__controls">
        <h3 class="fa-section__title">{{ t('walk.keyControls') }}</h3>
        <p v-for="control in current.keyControls" :key="control.id">
          <FaIcon name="marker-schluesselkontrolle" :size="14" /> {{ control.id }} {{ control.label }} <span class="fa-help">· {{ control.frequency }}</span>
        </p>
      </div>
      <ul class="fa-walk__done">
        <li v-for="step in current.steps" :key="step.id">{{ step.id }} · {{ step.case }} · {{ step.result }}</li>
      </ul>
      <h3 class="fa-section__title fa-section">{{ t('walk.record') }}</h3>
      <FieldForm :value="draft" :fields="FIELDS" :options-for="optionsFor" :disabled="readonly()" @update="draft = $event" />
      <button type="button" class="fa-btn fa-btn--primary fa-section" :disabled="readonly()" @click="save"><FaIcon name="check" :size="16" />{{ t('walk.record') }}</button>
    </template>
    <ol class="fa-walk__list">
      <li v-for="(step, position) in steps" :key="step.elementId">
        <button type="button" class="fa-menu-item" :aria-current="position === index" @click="go(position)">
          <span class="fa-walk__dot" :class="`fa-walk__dot--${step.status}`" />{{ step.name }}
        </button>
      </li>
    </ol>
  </section>
</template>

<style>
.fa-walk__bar {
  height: 6px;
  margin: 4px 0 12px;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--fa-success) var(--done), var(--fa-surface-3) var(--done));
}

.fa-walk__nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fa-walk__current {
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.fa-walk__controls {
  margin-top: 10px;
  padding: 8px 10px;
}

.fa-walk__controls p {
  margin: 2px 0;
}

.fa-walk__done {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 12px;
  color: var(--fa-text-muted);
}

.fa-walk__list {
  margin: 16px 0 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--fa-border);
}

.fa-walk__list [aria-current='true'] {
  background: var(--fa-primary-soft);
}

.fa-walk__dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--fa-surface-3);
  flex-shrink: 0;
}

.fa-walk__dot--erfuellt {
  background: var(--fa-success);
}

.fa-walk__dot--nicht_erfuellt {
  background: var(--fa-danger);
}
</style>
