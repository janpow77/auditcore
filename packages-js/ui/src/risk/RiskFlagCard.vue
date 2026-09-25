<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import { useId } from '../composables/useId'
import { useI18n, type Locale } from '../i18n'
import RiskFlagState from './RiskFlagState.vue'
import { riskMessages } from './messages'
import type { ProfileReference } from './types'
import { formatValue, parameterLabel, severityTone } from './view/format'
import { statusKey } from './view/labels'
import { pairs, type FlagEntry } from './view/state'

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
const status = computed(() => {
  const key = props.profile ? statusKey(props.profile.status) : null
  return key ? t(key) : (props.profile?.status ?? '')
})
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

<style>
.fa-risk-card { display: grid; gap: var(--fa-space-2); padding: var(--fa-space-3) var(--fa-space-4); border: 1px solid var(--fa-color-border); border-inline-start: 4px solid var(--fa-color-danger); border-radius: var(--fa-radius); background: var(--fa-color-surface); color: var(--fa-color-text); font: var(--fa-font-size-sm) / var(--fa-line-height) var(--fa-font-sans); }
.fa-risk-card--undetermined { border-style: dashed; border-inline-start: 4px dashed var(--fa-color-warning); background: var(--fa-color-surface-raised); }
.fa-risk-card__head { display: flex; flex-wrap: wrap; align-items: center; gap: var(--fa-space-2); }
.fa-risk-card__head h4 { flex: 1 1 16rem; margin: 0; font-size: var(--fa-font-size-md); }
.fa-risk-card code { font-family: var(--fa-font-mono); font-size: 0.95em; }
.fa-risk-card__profile { margin: 0; font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-risk-card__reason, .fa-risk-card__note { margin: 0; }
.fa-risk-card__note { color: var(--fa-color-text-muted); }
.fa-risk-card__grid { display: grid; gap: var(--fa-space-3); grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); }
.fa-risk-card__pairs { border-collapse: collapse; width: 100%; }
.fa-risk-card__pairs caption { text-align: start; font-weight: 600; padding-bottom: var(--fa-space-1); }
.fa-risk-card__pairs th, .fa-risk-card__pairs td { padding: 2px var(--fa-space-2); border-bottom: 1px solid var(--fa-color-border); text-align: start; vertical-align: top; }
.fa-risk-card__pairs thead th { font-size: var(--fa-font-size-xs); color: var(--fa-color-text-muted); }
.fa-risk-card__pairs tbody th { font-weight: 400; color: var(--fa-color-text-muted); }
.fa-risk-card__empty { color: var(--fa-color-warning); font-style: italic; font-weight: 600; }
.fa-risk-card__more summary { cursor: pointer; color: var(--fa-color-accent); }
.fa-risk-card__more summary:focus-visible { outline: none; box-shadow: var(--fa-focus-ring); border-radius: var(--fa-radius-sm); }
.fa-risk-card__more dl { display: grid; grid-template-columns: max-content 1fr; gap: 2px var(--fa-space-3); margin: var(--fa-space-2) 0 0; }
.fa-risk-card__more dt { color: var(--fa-color-text-muted); }
.fa-risk-card__more dd { margin: 0; word-break: break-word; }
</style>
