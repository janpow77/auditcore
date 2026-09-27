<!-- AttributeSampling: Merkmalsstichprobe für Systemprüfungen (Leitfaden 7.9); Logik im Kern (createAttributesController). -->
<script setup lang="ts">
import { computed, watch } from 'vue'
import {
  ATTRIBUTE_FIELDS,
  attributesApproachChoices,
  attributesConclusionTone,
  attributesConfidenceChoices,
  attributesFieldLabel,
  attributesFormMessage,
  attributesIssueKey,
  attributesMessages,
  attributesMetrics,
  attributesPercent,
  attributesStepColumns,
  attributesStepRows,
  createAttributesController,
  type AttributeApproach,
  type AttributesPort,
  type AttributesResult,
} from '@auditcore/ui-core'
import FaBadge from '../base/FaBadge.vue'
import FaButton from '../base/FaButton.vue'
import { useId } from '../composables/useId'
import { useStore } from '../composables/useStore'
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'

const props = withDefaults(defineProps<{
  /** Fachlogik, z. B. `createAttributesRestPort({ baseUrl: '/api/extrapolation' })`. */
  port?: AttributesPort | null
  locale?: Locale
}>(), { port: null, locale: undefined })

const emit = defineEmits<{
  'evaluation-completed': [result: AttributesResult]
  error: [message: string]
}>()
const { t, locale: active } = useI18n(attributesMessages, () => props.locale)
const controller = createAttributesController({
  port: () => props.port,
  callbacks: () => ({
    evaluated: (result) => emit('evaluation-completed', result),
    failed: (message) => emit('error', message),
  }),
})
const state = useStore(controller.store)
const id = useId('fa-attributes')
const approaches = computed(() => attributesApproachChoices(t))
const levels = computed(() => attributesConfidenceChoices(state.value.catalogue))
const metrics = computed(() => (state.value.result ? attributesMetrics(state.value.result, t, active.value) : []))
const message = computed(() => attributesFormMessage(state.value.issues, t))
const issue = (key: string): string => {
  const found = state.value.issues[key]
  return found ? t(attributesIssueKey(found)) : ''
}
const value = (event: Event): string => (event.target as HTMLInputElement | HTMLSelectElement).value

watch(() => props.port, () => void controller.load(), { immediate: true })
</script>

<template>
  <section class="fa-attributes" :lang="active" :aria-labelledby="`${id}-title`">
    <h3 :id="`${id}-title`" class="fa-attributes__heading">{{ t('title') }}</h3>
    <p v-if="state.busy === 'load'" class="fa-attributes__muted" role="status">{{ t('loading') }}</p>
    <p v-if="state.error" class="fa-attributes__failure" role="alert">{{ t('failed', { message: state.error }) }}</p>
    <template v-if="state.catalogue">
      <p class="fa-attributes__muted">{{ t('notice') }}</p>
      <div class="fa-attributes__form">
        <label class="fa-attributes__field">
          <span class="fa-attributes__label">{{ t('approach') }}</span>
          <select class="fa-attributes__select" :value="state.form.approach" data-testid="attributes-approach" @change="controller.update({ approach: value($event) as AttributeApproach })">
            <option v-for="entry in approaches" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
          </select>
        </label>
        <label v-for="field in ATTRIBUTE_FIELDS" :key="field.key" class="fa-attributes__field">
          <span class="fa-attributes__label">{{ attributesFieldLabel(field.key, state.form.approach, t) }}</span>
          <input class="fa-attributes__input" inputmode="decimal" :value="state.form[field.key]" :aria-invalid="issue(field.key) ? 'true' : undefined" :data-testid="`attributes-${field.key}`" @input="controller.update({ [field.key]: value($event) })" />
          <span v-if="issue(field.key)" class="fa-attributes__error">{{ issue(field.key) }}</span>
        </label>
        <label class="fa-attributes__field">
          <span class="fa-attributes__label">{{ t('confidence') }}</span>
          <select class="fa-attributes__select" :value="state.form.confidence === null ? '' : String(state.form.confidence)" :aria-invalid="issue('confidence') ? 'true' : undefined" data-testid="attributes-confidence" @change="controller.update({ confidence: value($event) === '' ? null : Number(value($event)) })">
            <option value="">{{ t('choose') }}</option>
            <option v-for="level in levels" :key="level" :value="String(level)">{{ attributesPercent(level, active) }}</option>
          </select>
        </label>
        <label v-if="state.form.approach === 'normal'" class="fa-attributes__field">
          <span class="fa-attributes__label">{{ t('factorProfile') }}</span>
          <select class="fa-attributes__select" :value="state.form.profileId ?? ''" data-testid="attributes-profile" @change="controller.update({ profileId: value($event) || null })">
            <option value="">{{ t('choose') }}</option>
            <option v-for="entry in state.catalogue.factor_profiles" :key="entry.id" :value="entry.id">{{ entry.label }}</option>
          </select>
        </label>
      </div>
      <div class="fa-attributes__actions">
        <FaButton variant="primary" :loading="state.busy === 'evaluate'" data-testid="attributes-evaluate" @click="controller.evaluate">{{ t('evaluate') }}</FaButton>
        <p v-if="message" class="fa-attributes__error" role="alert">{{ message }}</p>
      </div>
      <template v-if="state.result">
        <h4 class="fa-attributes__heading">{{ t('resultTitle') }}</h4>
        <p><FaBadge :tone="attributesConclusionTone(state.result.attributes.conclusion)" data-testid="attributes-conclusion">{{ t(`conclusion${state.result.attributes.conclusion}`) }}</FaBadge></p>
        <dl class="fa-attributes__metrics" data-testid="attributes-metrics">
          <div v-for="metric in metrics" :key="metric.id" class="fa-attributes__metric" :data-metric="metric.id">
            <dt>{{ metric.label }}</dt>
            <dd>{{ metric.value }}</dd>
          </div>
        </dl>
        <details>
          <summary>{{ t('derivation') }}</summary>
          <FaTable :columns="attributesStepColumns(t, active)" :rows="attributesStepRows(state.result)" :caption="t('derivation')" :locale="locale" data-testid="attributes-steps" />
        </details>
        <p class="fa-attributes__muted">{{ t('fingerprint') }}: {{ state.result.fingerprint }}</p>
      </template>
    </template>
  </section>
</template>
