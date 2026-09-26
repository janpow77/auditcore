<script setup lang="ts">
import { computed } from 'vue'
import FaBadge from '../base/FaBadge.vue'
import { useI18n, type Locale } from '../i18n'
import FaTable from '../table/FaTable.vue'
import type { TableColumn, TableRow } from '../table'
import { riskMessages, type FieldEntry, type ProfileDetail, type RuleView, formatValue, parameterLabel, requirementKey, profileHintText, profileStatusText, whenMissingKey, pairs } from '@auditcore/ui-core'

const props = withDefaults(defineProps<{ profile?: ProfileDetail | null; locale?: Locale }>(), { profile: null, locale: undefined })
const { t, locale: active } = useI18n(riskMessages, () => props.locale)

const status = computed(() => profileStatusText(props.profile, t))
const hint = computed(() => profileHintText(props.profile, t))
const ruleColumns = computed<TableColumn[]>(() => [
  { key: 'code', label: t('colCode') },
  { key: 'label', label: t('colLabel') },
  { key: 'inputs', label: t('inputs') },
  { key: 'parameters', label: t('parameters') },
  { key: 'when_missing_columns', label: t('colWhenMissing'), format: (value) => t(whenMissingKey(String(value))) },
])
const fieldColumns = computed<TableColumn[]>(() => [
  { key: 'name', label: t('field'), sortable: true },
  { key: 'meaning', label: t('colMeaning') },
  { key: 'requirement', label: t('colRequirement'), sortable: true },
  { key: 'uses', label: t('colMissing') },
])
const ruleRows = computed<TableRow[]>(() => (props.profile?.rules ?? []).map((rule) => ({ ...rule, id: rule.code })))
const fieldRows = computed<TableRow[]>(() => (props.profile?.fields ?? []).map((field) => ({ ...field, id: field.name })))

const asRule = (row: TableRow): RuleView => row as unknown as RuleView
const asField = (row: TableRow): FieldEntry => row as unknown as FieldEntry
</script>

<template>
  <section v-if="profile" class="fa-risk-profile" :aria-label="t('profileInfo')">
    <dl class="fa-risk-profile__identity">
      <dt>{{ t('profile') }}</dt><dd><code>{{ profile.id }}</code></dd>
      <dt>{{ t('version') }}</dt><dd><code>{{ profile.version }}</code></dd>
      <dt>{{ t('status') }}</dt><dd><FaBadge :tone="hint ? 'warning' : 'success'">{{ status }}</FaBadge></dd>
      <dt>{{ t('fingerprint') }}</dt><dd><code class="fa-risk-profile__hash">{{ profile.fingerprint }}</code></dd>
      <dt v-if="profile.source.repository">{{ t('source') }}</dt>
      <dd v-if="profile.source.repository">{{ profile.source.repository }} · {{ profile.source.path }} · {{ profile.source.commit }}</dd>
    </dl>
    <p v-if="hint" class="fa-risk-profile__hint" role="note">{{ hint }}</p>
    <p class="fa-risk-profile__legal">{{ profile.legal_status }}</p>
    <div v-if="profile.open_decisions.length">
      <h4>{{ t('openDecisions') }}</h4>
      <ul><li v-for="decision in profile.open_decisions" :key="decision">{{ decision }}</li></ul>
    </div>
    <FaTable :columns="ruleColumns" :rows="ruleRows" row-key="code" :caption="t('rulesTitle')" :locale="locale">
      <template #cell-code="{ row }"><code>{{ row.code }}</code></template>
      <template #cell-inputs="{ row }">
        <span><code v-for="name in asRule(row).inputs" :key="name" class="fa-risk-profile__chip">{{ name }}</code></span>
      </template>
      <template #cell-parameters="{ row }">
        <span>
          <span v-for="[name, value] in pairs(asRule(row).parameters)" :key="name" class="fa-risk-profile__param">
            {{ parameterLabel(name, active) }}: {{ formatValue(value, active, t('emptyValue')) }}
          </span>
        </span>
      </template>
    </FaTable>
    <FaTable :columns="fieldColumns" :rows="fieldRows" row-key="name" :caption="t('fieldsTitle')" :locale="locale">
      <template #cell-name="{ row }"><code>{{ row.name }}</code></template>
      <template #cell-meaning="{ row }">{{ asField(row).meaning ?? t('undocumented') }}</template>
      <template #cell-requirement="{ row }">
        <FaBadge :tone="asField(row).requirement === 'optional' ? 'neutral' : 'accent'">{{ t(requirementKey(asField(row).requirement)) }}</FaBadge>
      </template>
      <template #cell-uses="{ row }">
        <span>
          <span v-for="use in asField(row).uses" :key="use.code" class="fa-risk-profile__use">
            <code>{{ use.code }}</code> ({{ use.role }}): {{ use.absent }} / {{ use.empty }}
          </span>
        </span>
      </template>
    </FaTable>
  </section>
</template>
