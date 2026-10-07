<script setup lang="ts">
/**
 * Audit attributes: name/value properties defined by the profile
 * (`camunda:property`). Single choices as select, several values as check
 * boxes, yes/no as one check box, free text on blur. An empty value removes
 * the property; properties the profile does not know stay untouched.
 */
import { computed } from 'vue'
import type { PropertyPatch } from '@auditcore/bpmn-flowaudit'
import { isYes, propertyFields, textPatch, togglePatch, yesNoPatch, type PropertyField } from '@auditcore/bpmn-flowaudit/ui'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'

const { selection, profile, readonly } = useEditorContext()
const { t, locale } = useI18n()

const fields = computed(() => propertyFields(profile(), selection.type.value, selection.namedProperties(), locale.value))
const labelOf = (name: string) => fields.value.find((field) => field.name === name)?.label ?? name
const inactiveHint = (field: PropertyField) => {
  const condition = profile()?.properties?.entries.find((entry) => entry.name === field.name)?.depends_on
  return condition ? t('props.properties.inactive', { property: labelOf(condition.property), values: condition.values.join(', ') }) : ''
}
const write = (patch: PropertyPatch) => selection.writeProperties(patch)
</script>

<template>
  <div class="fa-tab-properties">
    <p class="fa-help">{{ t('props.properties.help') }}</p>
    <div v-for="field in fields" :key="field.name" class="fa-field fa-property" :class="{ 'fa-property--inactive': !field.active }">
      <span :id="`fa-prop-${field.name}`" class="fa-label">{{ field.label }}</span>
      <select
        v-if="field.kind === 'choice'"
        class="fa-select"
        :value="field.selected[0] ?? ''"
        :disabled="readonly()"
        :aria-labelledby="`fa-prop-${field.name}`"
        @change="write(textPatch(field, ($event.target as HTMLSelectElement).value))"
      >
        <option value="">{{ t('props.properties.none') }}</option>
        <option v-for="option in field.options" :key="option.value" :value="option.value">
          {{ option.known ? option.label : `${option.label} (${t('props.properties.unknown')})` }}
        </option>
      </select>
      <div v-else-if="field.kind === 'multi_choice'" class="fa-property__choices" role="group" :aria-labelledby="`fa-prop-${field.name}`">
        <label v-for="option in field.options" :key="option.value" class="fa-check">
          <input
            type="checkbox"
            :checked="field.selected.includes(option.value)"
            :disabled="readonly()"
            @change="write(togglePatch(field, option.value))"
          />
          {{ option.label }}
          <span v-if="!option.known" class="fa-badge">{{ t('props.properties.unknown') }}</span>
        </label>
      </div>
      <label v-else-if="field.kind === 'yes_no'" class="fa-check">
        <input type="checkbox" :checked="isYes(field)" :disabled="readonly()" :aria-labelledby="`fa-prop-${field.name}`" @change="write(yesNoPatch(field, ($event.target as HTMLInputElement).checked))" />
        {{ t('props.properties.yes') }}
      </label>
      <input
        v-else
        class="fa-input"
        :value="field.text"
        :disabled="readonly()"
        :aria-labelledby="`fa-prop-${field.name}`"
        @change="write(textPatch(field, ($event.target as HTMLInputElement).value))"
      />
      <span v-if="field.help" class="fa-help">{{ field.help }}</span>
      <span v-if="!field.active" class="fa-help fa-property__hint">{{ inactiveHint(field) }}</span>
    </div>
  </div>
</template>
