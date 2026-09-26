<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import RiskFlagState from './RiskFlagState.vue'
import { riskMessages, type ProfileReference, formatValue, parameterLabel, severityTone, profileStatusText, pairs, type FlagEntry } from '@auditcore/ui-core'

const props = withDefaults(defineProps<{
  entry: FlagEntry
  profile?: ProfileReference | null
  locale?: Locale
}>(), { profile: null, locale: undefined })

const { t, locale: active } = useI18n(riskMessages, () => props.locale)
const inputs = computed(() => pairs(props.entry.inputs))
const parameters = computed(() => pairs(props.entry.parameters))
const evidence = computed(() => pairs(props.entry.evidence))
const origin = computed(() => pairs(props.entry.origin))
const status = computed(() => profileStatusText(props.profile, t))
const headingId = useId('fa-risk-card')
</script>

<template>
  <article class="fa-risk-card" :class="`fa-risk-card--${entry.state}`" :aria-labelledby="headingId" :data-code="entry.code">
    <header class="fa-risk-card__head">
      <RiskFlagState :state="entry.state" :locale="locale" />
      <h4 :id="headingId"><code>{{ entry.code }}</code> {{ entry.label }}</h4>
      <FaBadge v-if="entry.severity" :tone="severityTone(entry.severity)">{{ t('severity') }}: {{ entry.severity }}</FaBadge>
    </header>
    <p v-if="profile" class="fa-risk-card__profile">
      {{ t('profile') }} <code>{{ profile.id }}</code> · {{ t('version') }} <code>{{ profile.version }}</code> · {{ status }}
    </p>
    <p class="fa-risk-card__reason"><strong>{{ t('reason') }}:</strong> {{ entry.reason }}</p>
    <div class="fa-risk-card__grid">
      <table v-if="inputs.length" class="fa-risk-card__pairs">
        <caption>{{ t('inputs') }}</caption>
        <thead><tr><th scope="col">{{ t('field') }}</th><th scope="col">{{ t('value') }}</th></tr></thead>
        <tbody>
          <tr v-for="[name, value] in inputs" :key="name">
            <th scope="row"><code>{{ name }}</code></th>
            <td :class="{ 'fa-risk-card__empty': value === null || value === '' }">{{ formatValue(value, active, t('emptyValue')) }}</td>
          </tr>
        </tbody>
      </table>
      <table v-if="parameters.length" class="fa-risk-card__pairs">
        <caption>{{ t('parameters') }}</caption>
        <tbody>
          <tr v-for="[name, value] in parameters" :key="name">
            <th scope="row">{{ parameterLabel(name, active) }}</th>
            <td>{{ formatValue(value, active, t('emptyValue')) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="entry.note" class="fa-risk-card__note"><strong>{{ t('note') }}:</strong> {{ entry.note }}</p>
    <details v-if="evidence.length" class="fa-risk-card__more">
      <summary>{{ t('evidence') }}</summary>
      <dl><template v-for="[name, value] in evidence" :key="name"><dt>{{ name }}</dt><dd>{{ formatValue(value, active, t('emptyValue')) }}</dd></template></dl>
    </details>
    <details v-if="origin.length" class="fa-risk-card__more">
      <summary>{{ t('origin') }}</summary>
      <dl><template v-for="[name, value] in origin" :key="name"><dt>{{ name }}</dt><dd>{{ formatValue(value, active, t('emptyValue')) }}</dd></template></dl>
    </details>
  </article>
</template>
