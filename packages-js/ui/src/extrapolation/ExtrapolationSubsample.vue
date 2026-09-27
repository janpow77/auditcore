<script setup lang="ts">
import { computed } from 'vue'
import {
  extrapolationCellLabel,
  extrapolationIssueText,
  extrapolationMessages,
  SUB_ITEM_FIELDS,
  subsampleEstimatorChoices,
  type ExtrapolationController,
  type ExtrapolationData,
  type SubsampleEstimator,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'

const props = withDefaults(defineProps<{ controller: ExtrapolationController; state: ExtrapolationData; locale?: Locale }>(), { locale: undefined })
const { t } = useI18n(extrapolationMessages, () => props.locale)
const id = useId('fa-extrapolation-subsample')
const index = computed(() => props.state.subsampleUnit)
const unit = computed(() => (index.value === null ? null : props.state.form.units[index.value] ?? null))
const rows = computed(() => unit.value?.subsample ?? null)
const estimators = computed(() => subsampleEstimatorChoices(t))
const issue = (key: string): string => extrapolationIssueText(props.state.issues, `units.${index.value}.subsample.${key}`, t)
const value = (event: Event): string => (event.target as HTMLInputElement).value
const checked = (event: Event): boolean => (event.target as HTMLInputElement).checked
</script>

<template>
  <section v-if="unit && rows" class="fa-extrapolation__card" :aria-labelledby="`${id}-title`" data-testid="extrapolation-subsample">
    <h3 :id="`${id}-title`" class="fa-extrapolation__heading">{{ t('subsampleTitle', { unit: unit.id || String((index ?? 0) + 1) }) }}</h3>
    <p class="fa-extrapolation__hint">{{ t('subsampleHint') }}</p>
    <div class="fa-extrapolation__settings">
      <label class="fa-extrapolation__field">
        <span class="fa-extrapolation__label">{{ t('estimator') }}</span>
        <select class="fa-extrapolation__select" :value="rows.estimator" data-testid="extrapolation-subsample-estimator" @change="controller.updateSubsample({ estimator: value($event) as SubsampleEstimator })">
          <option v-for="entry in estimators" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
        </select>
      </label>
      <label v-if="rows.estimator === 'mean_per_unit'" class="fa-extrapolation__field">
        <span class="fa-extrapolation__label">{{ t('subPopulation') }}</span>
        <input class="fa-extrapolation__input fa-extrapolation__input--number" inputmode="numeric" :value="rows.populationSize" :aria-invalid="issue('populationSize') ? 'true' : undefined" data-testid="extrapolation-subsample-size" @input="controller.updateSubsample({ populationSize: value($event) })" />
        <span v-if="issue('populationSize')" class="fa-extrapolation__error">{{ issue('populationSize') }}</span>
      </label>
    </div>
    <h4 class="fa-extrapolation__heading">{{ t('subItems') }}</h4>
    <p v-if="issue('items')" class="fa-extrapolation__error">{{ issue('items') }}</p>
    <div class="fa-extrapolation__scroll">
      <table class="fa-extrapolation__grid" data-testid="extrapolation-subsample-items">
        <thead>
          <tr>
            <th v-for="field in SUB_ITEM_FIELDS" :key="field.key" scope="col">{{ t(field.label) }}</th>
            <th scope="col">{{ t('exhaustive') }}</th>
            <th scope="col">{{ t('remove') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, position) in rows.items" :key="item.key">
            <td v-for="field in SUB_ITEM_FIELDS" :key="field.key">
              <input
                class="fa-extrapolation__input"
                :class="{ 'fa-extrapolation__input--number': field.numeric }"
                :inputmode="field.numeric ? 'decimal' : undefined"
                :value="item[field.key]"
                :aria-label="extrapolationCellLabel(t, field.label, position + 1)"
                :aria-invalid="issue(`items.${position}.${field.key}`) ? 'true' : undefined"
                @input="controller.updateSubItem(position, { [field.key]: value($event) })"
              />
            </td>
            <td>
              <input type="checkbox" class="fa-extrapolation__check" :checked="item.exhaustive" :aria-label="extrapolationCellLabel(t, 'exhaustive', position + 1)" @change="controller.updateSubItem(position, { exhaustive: checked($event) })" />
            </td>
            <td>
              <FaButton size="sm" variant="ghost" icon="trash" icon-only :label="t('removeRow', { what: t('subItemId'), row: position + 1 })" @click="controller.removeSubItem(position)" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="fa-extrapolation__actions">
      <FaButton size="sm" icon="plus" data-testid="extrapolation-add-subitem" @click="controller.addSubItem">{{ t('addSubItem') }}</FaButton>
      <FaButton size="sm" variant="ghost" data-testid="extrapolation-subsample-close" @click="controller.editSubsample(null)">{{ t('close') }}</FaButton>
    </div>
  </section>
</template>
