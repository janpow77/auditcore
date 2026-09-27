<script setup lang="ts">
import { computed } from 'vue'
import {
  extrapolationIssueText,
  extrapolationMessages,
  subsampleEditorView,
  subsampleEstimatorChoices,
  type ExtrapolationController,
  type ExtrapolationData,
  type SubsampleEstimator,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import ExtrapolationSubsampleItems from './ExtrapolationSubsampleItems.vue'
import ExtrapolationSubsampleStrata from './ExtrapolationSubsampleStrata.vue'

const props = withDefaults(defineProps<{ controller: ExtrapolationController; state: ExtrapolationData; locale?: Locale }>(), { locale: undefined })
const { t } = useI18n(extrapolationMessages, () => props.locale)
const id = useId('fa-extrapolation-subsample')
const editor = computed(() => subsampleEditorView(props.state, t))
const estimators = computed(() => subsampleEstimatorChoices(t))
const issue = (key: string): string => extrapolationIssueText(props.state.issues, `${editor.value?.prefix}.${key}`, t)
const value = (event: Event): string => (event.target as HTMLInputElement).value
</script>

<template>
  <section v-if="editor" class="fa-extrapolation__card" :aria-labelledby="`${id}-title`" data-testid="extrapolation-subsample">
    <h3 :id="`${id}-title`" class="fa-extrapolation__heading">{{ editor.title }}</h3>
    <p class="fa-extrapolation__hint">{{ t('subsampleHint') }}</p>
    <div class="fa-extrapolation__settings">
      <label class="fa-extrapolation__field">
        <span class="fa-extrapolation__label">{{ t('estimator') }}</span>
        <select class="fa-extrapolation__select" :value="editor.rows.estimator" data-testid="extrapolation-subsample-estimator" @change="controller.updateSubsample({ estimator: value($event) as SubsampleEstimator })">
          <option v-for="entry in estimators" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
        </select>
      </label>
      <label v-if="editor.rows.estimator === 'mean_per_unit' && editor.rows.strata.length === 0" class="fa-extrapolation__field">
        <span class="fa-extrapolation__label">{{ t('subPopulation') }}</span>
        <input class="fa-extrapolation__input fa-extrapolation__input--number" inputmode="numeric" :value="editor.rows.populationSize" :aria-invalid="issue('populationSize') ? 'true' : undefined" data-testid="extrapolation-subsample-size" @input="controller.updateSubsample({ populationSize: value($event) })" />
        <span v-if="issue('populationSize')" class="fa-extrapolation__error">{{ issue('populationSize') }}</span>
      </label>
    </div>
    <ExtrapolationSubsampleStrata :controller="controller" :state="state" :editor="editor" :locale="locale" />
    <ExtrapolationSubsampleItems :controller="controller" :state="state" :editor="editor" :locale="locale" />
    <div class="fa-extrapolation__actions">
      <FaButton size="sm" icon="plus" data-testid="extrapolation-add-subitem" @click="controller.addSubItem">{{ t('addSubItem') }}</FaButton>
      <FaButton v-if="editor.nested" size="sm" variant="ghost" data-testid="extrapolation-subsample-back" @click="controller.editNestedSubsample(null)">{{ t('backToUnit') }}</FaButton>
      <FaButton size="sm" variant="ghost" data-testid="extrapolation-subsample-close" @click="controller.editSubsample(null)">{{ t('close') }}</FaButton>
    </div>
  </section>
</template>
