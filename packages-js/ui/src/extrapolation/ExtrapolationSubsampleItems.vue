<script setup lang="ts">
import { computed } from 'vue'
import {
  extrapolationCellLabel,
  extrapolationIssueText,
  extrapolationMessages,
  SUB_ITEM_FIELDS,
  type ExtrapolationController,
  type ExtrapolationData,
  type SubsampleEditorView,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{ controller: ExtrapolationController; state: ExtrapolationData; editor: SubsampleEditorView; locale?: Locale }>(), { locale: undefined })
const { t } = useI18n(extrapolationMessages, () => props.locale)
const names = computed(() => props.editor.rows.strata.map((row) => row.name.trim()).filter(Boolean))
const issue = (key: string): string => extrapolationIssueText(props.state.issues, `${props.editor.prefix}.${key}`, t)
const value = (event: Event): string => (event.target as HTMLInputElement | HTMLSelectElement).value
const checked = (event: Event): boolean => (event.target as HTMLInputElement).checked
</script>

<template>
  <h4 class="fa-extrapolation__heading">{{ t('subItems') }}</h4>
  <p v-if="issue('items')" class="fa-extrapolation__error">{{ issue('items') }}</p>
  <div class="fa-extrapolation__scroll">
    <table class="fa-extrapolation__grid" data-testid="extrapolation-subsample-items">
      <thead>
        <tr>
          <th v-if="names.length" scope="col">{{ t('subStratum') }}</th>
          <th v-for="field in SUB_ITEM_FIELDS" :key="field.key" scope="col">{{ t(field.label) }}</th>
          <th scope="col">{{ t('exhaustive') }}</th>
          <th v-if="editor.allowNested" scope="col">{{ t('subsample') }}</th>
          <th scope="col">{{ t('remove') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(item, position) in editor.rows.items" :key="item.key">
          <td v-if="names.length">
            <select class="fa-extrapolation__select" :value="item.stratum" :aria-label="extrapolationCellLabel(t, 'subStratum', position + 1)" :aria-invalid="issue(`items.${position}.stratum`) ? 'true' : undefined" @change="controller.updateSubItem(position, { stratum: value($event) })">
              <option value="">{{ t('choose') }}</option>
              <option v-for="name in names" :key="name" :value="name">{{ name }}</option>
            </select>
          </td>
          <td v-for="field in SUB_ITEM_FIELDS" :key="field.key">
            <input
              class="fa-extrapolation__input"
              :class="{ 'fa-extrapolation__input--number': field.numeric }"
              :inputmode="field.numeric ? 'decimal' : undefined"
              :value="field.key === 'random' && item.subsample ? t('fromSubsample') : item[field.key]"
              :disabled="field.key === 'random' && item.subsample !== null"
              :aria-label="extrapolationCellLabel(t, field.label, position + 1)"
              :aria-invalid="issue(`items.${position}.${field.key}`) ? 'true' : undefined"
              @input="controller.updateSubItem(position, { [field.key]: value($event) })"
            />
          </td>
          <td>
            <input type="checkbox" class="fa-extrapolation__check" :checked="item.exhaustive" :aria-label="extrapolationCellLabel(t, 'exhaustive', position + 1)" @change="controller.updateSubItem(position, { exhaustive: checked($event) })" />
          </td>
          <td v-if="editor.allowNested" class="fa-extrapolation__nowrap">
            <template v-if="item.subsample">
              <FaButton size="sm" variant="ghost" icon="edit" icon-only :label="t('nestedOpen', { row: position + 1 })" @click="controller.editNestedSubsample(position)" />
              <FaButton size="sm" variant="ghost" icon="trash" icon-only :label="t('nestedDrop', { row: position + 1 })" @click="controller.toggleNestedSubsample(position)" />
            </template>
            <FaButton v-else size="sm" variant="ghost" icon="plus" icon-only :label="t('nestedCreate', { row: position + 1 })" @click="controller.toggleNestedSubsample(position)" />
          </td>
          <td>
            <FaButton size="sm" variant="ghost" icon="trash" icon-only :label="t('removeRow', { what: t('subItemId'), row: position + 1 })" @click="controller.removeSubItem(position)" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
