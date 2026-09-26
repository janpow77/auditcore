<script setup lang="ts">
/**
 * General tab: name, id, documentation, markers and the FlowStat task
 * fields (legacy `BpmnPropertiesPanel` of the audit_designer).
 */
import { computed } from 'vue'
import { FLOWSTAT_FIELDS, isActivity, type FlowstatField, type Marker } from '@flowaudit/bpmn-flowaudit'
import { FLOWSTAT_KEYS as fields, flowstatValue } from '@flowaudit/bpmn-flowaudit/ui'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'
import MarkerPicker from './MarkerPicker.vue'

const { selection, editor, readonly } = useEditorContext()
const { t } = useI18n()

const element = computed(() => selection.element.value)
const type = computed(() => selection.type.value ?? '')
const flowstat = computed(() => (isActivity(type.value) ? selection.flowstat() : null))

function setMarkers(markers: Marker[]): void {
  selection.write({ markers })
}

function setColor(color: { fill: string; stroke: string }): void {
  const current = element.value
  if (!current || current.di?.get('bioc:fill') || current.di?.get('color:background-color')) return
  editor.services().modeling.setColor([current], color)
}

const setFlowstat = (field: FlowstatField, raw: string) => selection.setFlowstat(field, flowstatValue(field, raw))
</script>

<template>
  <div v-if="element" class="fa-tab-general">
    <div class="fa-grid-2">
      <label class="fa-field fa-field--wide">
        <span class="fa-label">{{ t('props.name') }}</span>
        <input class="fa-input" :value="selection.property('name')" :disabled="readonly()" @change="selection.rename(($event.target as HTMLInputElement).value)" />
      </label>
      <label class="fa-field">
        <span class="fa-label">{{ t('props.id') }}</span>
        <input class="fa-input" :value="element.id" readonly />
      </label>
      <label class="fa-field">
        <span class="fa-label">{{ t('props.type') }}</span>
        <input class="fa-input" :value="type.replace('bpmn:', '')" readonly />
      </label>
      <label class="fa-field fa-field--wide">
        <span class="fa-label">{{ t('props.documentation') }}</span>
        <textarea class="fa-textarea" rows="4" :value="selection.documentation()" :disabled="readonly()" @change="selection.setDocumentation(($event.target as HTMLTextAreaElement).value)" />
      </label>
    </div>
    <MarkerPicker class="fa-section" :markers="selection.extensions.value.markers" :disabled="readonly()" @update="setMarkers" @color="setColor" />
    <section v-if="flowstat" class="fa-section">
      <h3 class="fa-section__title">{{ t('props.flowstat') }}</h3>
      <div class="fa-grid-2">
        <label v-for="field in fields" :key="field" class="fa-field" :class="{ 'fa-field--wide': field === 'resource' }">
          <span class="fa-label">{{ t(`props.flowstat.${field}`) }}</span>
          <input
            class="fa-input"
            :type="FLOWSTAT_FIELDS[field].numeric ? 'number' : 'text'"
            min="0"
            :value="flowstat[field] ?? ''"
            :disabled="readonly()"
            @change="setFlowstat(field, ($event.target as HTMLInputElement).value)"
          />
        </label>
      </div>
    </section>
  </div>
</template>

