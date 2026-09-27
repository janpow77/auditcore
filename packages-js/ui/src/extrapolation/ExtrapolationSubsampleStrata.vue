<script setup lang="ts">
import {
  extrapolationCellLabel,
  extrapolationIssueText,
  extrapolationMessages,
  SUB_STRATUM_FIELDS,
  type ExtrapolationController,
  type ExtrapolationData,
  type SubsampleEditorView,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{ controller: ExtrapolationController; state: ExtrapolationData; editor: SubsampleEditorView; locale?: Locale }>(), { locale: undefined })
const { t } = useI18n(extrapolationMessages, () => props.locale)
const issue = (key: string): string => extrapolationIssueText(props.state.issues, `${props.editor.prefix}.${key}`, t)
const value = (event: Event): string => (event.target as HTMLInputElement).value
</script>

<template>
  <h4 class="fa-extrapolation__heading">{{ t('subStrata') }}</h4>
  <p class="fa-extrapolation__hint">{{ t('subStrataHint') }}</p>
  <p v-if="issue('strata')" class="fa-extrapolation__error">{{ issue('strata') }}</p>
  <div v-if="editor.rows.strata.length" class="fa-extrapolation__scroll">
    <table class="fa-extrapolation__grid" data-testid="extrapolation-substrata">
      <thead>
        <tr>
          <th v-for="field in SUB_STRATUM_FIELDS" :key="field.key" scope="col">{{ t(field.label) }}</th>
          <th scope="col">{{ t('remove') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, position) in editor.rows.strata" :key="row.key">
          <td v-for="field in SUB_STRATUM_FIELDS" :key="field.key">
            <input
              class="fa-extrapolation__input"
              :class="{ 'fa-extrapolation__input--number': field.numeric }"
              :inputmode="field.numeric ? 'decimal' : undefined"
              :value="row[field.key]"
              :aria-label="extrapolationCellLabel(t, field.label, position + 1)"
              :aria-invalid="issue(`strata.${position}.${field.key}`) ? 'true' : undefined"
              @input="controller.updateSubStratum(position, { [field.key]: value($event) })"
            />
          </td>
          <td>
            <FaButton size="sm" variant="ghost" icon="trash" icon-only :label="t('removeRow', { what: t('subStratum'), row: position + 1 })" @click="controller.removeSubStratum(position)" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="fa-extrapolation__actions">
    <FaButton size="sm" icon="plus" data-testid="extrapolation-add-substratum" @click="controller.addSubStratum">{{ t('addSubStratum') }}</FaButton>
  </div>
</template>
