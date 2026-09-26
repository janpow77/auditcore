<script setup lang="ts">
/**
 * Walk-through test: go through the diagram step by step, record per step
 * case, voucher, result and remark (`flowaudit:pruefschritt`); key controls
 * of the step with sample size for the control test. Steps are highlighted
 * in the diagram (current, met, not met).
 */
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { nextStepId, recordStep, walkthroughProgress, walkthroughSteps, type AuditStep, type FlowauditHighlight } from '@flowaudit/bpmn-flowaudit'
import { clampStep, progressPercent, stepDraft, WALK_FIELDS as FIELDS, walkthroughClasses } from '@flowaudit/bpmn-flowaudit/ui'
import FaIcon from '../base/FaIcon.vue'
import FieldForm from '../../panels/FieldForm.vue'
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

function highlight(): void {
  if (!editor.state.ready) return
  const layer = editor.editor.value?.get<FlowauditHighlight>('flowauditHighlight', false)
  if (!layer) return
  layer.apply('walkthrough', walkthroughClasses(steps.value, current.value?.elementId))
}

function go(step: number): void {
  index.value = clampStep(step, steps.value.length)
  draft.value = stepDraft(props.tester)
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
    <div class="fa-walk__bar" :style="{ '--done': progressPercent(progress) }" aria-hidden="true" />
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
