<script setup lang="ts">
/**
 * Diagram info: all info fields incl. profile, funds, programming period,
 * status, validity, approval with hash, confidentiality and header colours
 * (legacy columns header_title/…/header_color). Edits a copy; „apply“
 * writes one undo step.
 */
import { computed, ref, watch } from 'vue'
import { FUNDS, FUND_SHORT, headerOf, label, type Approval, type DiagramInfo, type ListExtensionKey, type ProfileSummary } from '@flowaudit/bpmn-flowaudit'
import BaseDialog from '../base/BaseDialog.vue'
import FaIcon from '../base/FaIcon.vue'
import FieldForm from '../../panels/FieldForm.vue'
import ListEditor from '../../panels/ListEditor.vue'
import LegalBasisEditor from '../../panels/legal/LegalBasisEditor.vue'
import { LISTS, type DescribedListKey } from '../../panels/descriptors'
import { useOptions } from '../../panels/useOptions'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'
import { INFO_SECTIONS } from './infoFields'

const props = defineProps<{ open: boolean; info: DiagramInfo | null; profiles: ProfileSummary[]; approvals?: Approval[]; fallbackTitle: string }>()
const emit = defineEmits<{ (e: 'update:open', value: boolean): void; (e: 'apply', info: DiagramInfo): void; (e: 'approve', info: DiagramInfo): void; (e: 'new-version', info: DiagramInfo): void }>()
const { t, locale } = useI18n()
const { ports, profile, readonly } = useEditorContext()
const { optionsFor } = useOptions({ profile, catalogue: ports.catalogue, locale })
const draft = ref<DiagramInfo>({})

watch(
  () => props.open,
  (open) => {
    if (open) draft.value = JSON.parse(JSON.stringify(props.info ?? {})) as DiagramInfo
  },
  { immediate: true },
)

const header = computed(() => headerOf(draft.value, props.fallbackTitle))
const lastApproval = computed(() => props.approvals?.[props.approvals.length - 1])
const DIAGRAM_LISTS: DescribedListKey[] = ['auditReferences', 'risks', 'findings', 'sources', 'crossReferences']

function merge(value: Record<string, unknown>): void {
  draft.value = { ...(value as DiagramInfo) }
}

function toggleFund(code: string): void {
  const funds = new Set(draft.value.funds ?? [])
  if (funds.has(code)) funds.delete(code)
  else funds.add(code)
  draft.value = { ...draft.value, funds: [...funds] }
}

function listItems(key: ListExtensionKey): Record<string, unknown>[] {
  return ((draft.value as Record<string, unknown>)[key] as Record<string, unknown>[] | undefined) ?? []
}
</script>

<template>
  <BaseDialog :open="open" :title="t('info.title')" width="860px" @update:open="emit('update:open', $event)">
    <div class="fa-info-preview" :style="{ background: header.color, color: header.textColor }" :aria-label="t('info.preview')">
      <strong>{{ header.title }}</strong><span>{{ header.subtitle }}</span>
    </div>
    <section v-for="section in INFO_SECTIONS" :key="section.id" class="fa-info-section">
      <h3 class="fa-section__title">{{ t(section.title) }}</h3>
      <FieldForm :value="draft" :fields="section.fields" :options-for="optionsFor" :disabled="readonly() && section.id !== 'status'" @update="merge" />
      <template v-if="section.id === 'scope'">
        <label class="fa-field fa-section">
          <span class="fa-label">{{ t('info.field.profile') }}</span>
          <select class="fa-select" :value="draft.profile ?? ''" :disabled="readonly()" @change="draft = { ...draft, profile: ($event.target as HTMLSelectElement).value || undefined }">
            <option value="">{{ t('common.none') }}</option>
            <option v-for="entry in profiles" :key="entry.id" :value="entry.id">{{ entry.title }} ({{ entry.version }})</option>
          </select>
        </label>
        <fieldset class="fa-info-funds">
          <legend class="fa-label">{{ t('info.field.funds') }}</legend>
          <button v-for="(text, code) in FUNDS" :key="code" type="button" class="fa-chip" :title="label(text, locale)" :aria-pressed="(draft.funds ?? []).includes(String(code))" :disabled="readonly()" @click="toggleFund(String(code))">
            {{ FUND_SHORT[code] ?? code }}
          </button>
        </fieldset>
      </template>
    </section>
    <section class="fa-info-section">
      <h3 class="fa-section__title">{{ t('info.section.header') }}</h3>
      <div class="fa-grid-2">
        <label class="fa-field"><span class="fa-label">{{ t('info.field.headerColor') }}</span><input type="color" class="fa-input" :value="header.color" :disabled="readonly()" @change="draft = { ...draft, headerColor: ($event.target as HTMLInputElement).value }" /></label>
        <label class="fa-field"><span class="fa-label">{{ t('info.field.headerTextColor') }}</span><input type="color" class="fa-input" :value="header.textColor" :disabled="readonly()" @change="draft = { ...draft, headerTextColor: ($event.target as HTMLInputElement).value }" /></label>
      </div>
    </section>
    <section class="fa-info-section">
      <h3 class="fa-section__title">{{ t('info.section.legal') }}</h3>
      <LegalBasisEditor :items="draft.legalBases ?? []" :port="ports.legalSearch" :profile-id="profile()?.id" :disabled="readonly()" @update="draft = { ...draft, legalBases: $event }" />
      <ListEditor v-for="key in DIAGRAM_LISTS" :key="key" class="fa-section" :descriptor="LISTS[key]" :items="listItems(key)" :options-for="optionsFor" :disabled="readonly()" @update="draft = { ...draft, [key]: $event }" />
    </section>
    <section class="fa-info-section">
      <h3 class="fa-section__title">{{ t('info.approval') }}</h3>
      <p class="fa-help">{{ t('info.approveHelp') }}</p>
      <p v-if="lastApproval" class="fa-info-hash"><FaIcon name="hash" :size="14" />{{ t('info.approvedHash') }} ({{ lastApproval.version }}): <code>{{ lastApproval.sha256 }}</code></p>
      <div class="fa-info-actions">
        <button type="button" class="fa-btn" :disabled="readonly()" @click="emit('approve', draft)"><FaIcon name="lock" :size="16" />{{ t('info.approve') }}</button>
        <button type="button" class="fa-btn" @click="emit('new-version', draft)"><FaIcon name="new" :size="16" />{{ t('info.newVersion') }}</button>
      </div>
    </section>
    <template #footer>
      <button type="button" class="fa-btn" @click="emit('update:open', false)">{{ t('common.cancel') }}</button>
      <button type="button" class="fa-btn fa-btn--primary" :disabled="readonly()" @click="(emit('apply', draft), emit('update:open', false))">{{ t('common.apply') }}</button>
    </template>
  </BaseDialog>
</template>

<style>
.fa-info-preview {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 14px;
  border-radius: var(--fa-radius);
  margin-bottom: 12px;
}

.fa-info-section + .fa-info-section {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--fa-border);
}

.fa-info-funds {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 12px 0 0;
  padding: 0;
  border: 0;
}

.fa-info-hash code {
  font-family: var(--fa-mono);
  font-size: 12px;
  word-break: break-all;
}

.fa-info-actions {
  display: flex;
  gap: 8px;
}
</style>
