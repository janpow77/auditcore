<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import FaButton from '../../base/FaButton.vue'
import { useId } from '../../composables/useId'
import { formatDate, useI18n } from '../../i18n'
import { decisionTitle, isDeviation, mayRelease, parseConditions } from '../dsfaView'
import { dataprotectionMessages } from '../messages'
import type { AssessmentView, DecisionInput, DataProtectionProfile, Proposal } from '../types'

const props = withDefaults(defineProps<{
  profile: DataProtectionProfile
  view: AssessmentView
  proposal: Proposal
  dirty?: boolean
  actor?: string
  busy?: string | null
}>(), { dirty: false, actor: '', busy: null })

const emit = defineEmits<{ decide: [decision: DecisionInput]; 'dpo-request': [from: string, on: string]; release: [] }>()
const { t, locale } = useI18n(dataprotectionMessages)
const id = useId('fa-dsfa-decision')
const decision = ref('')
const justification = ref('')
const conditions = ref('')
const dpoFrom = ref('')
const dpoOn = ref('')
const deviation = computed(() => isDeviation(props.proposal, decision.value))
const canRelease = computed(() => mayRelease(props.view, props.actor) && !props.dirty && !props.view.release_blockers.length)
const when = (value: string | null): string => formatDate(value, locale.value, true)

watch(() => props.view, (view) => {
  decision.value = view.decision ?? (props.proposal.recommendation === 'unvollstaendig' ? '' : props.proposal.recommendation)
  justification.value = view.deviation_justification ?? ''
  conditions.value = view.conditions.join('\n')
}, { immediate: true })

function submit(): void {
  emit('decide', { decision: decision.value, justification: justification.value, conditions: parseConditions(conditions.value) })
}
</script>

<template>
  <div data-testid="dsfa-decision">
    <section class="fa-dataprotection__panel" :aria-labelledby="`${id}-title`">
      <h3 :id="`${id}-title`">{{ t('decisionTitle') }}</h3>
      <p v-if="view.decided_by" class="fa-dataprotection__muted">
        {{ t('decidedBy', { person: view.decided_by, date: when(view.decided_at), decision: decisionTitle(profile, view.decision) }) }}
      </p>
      <p v-if="dirty" class="fa-dataprotection__alert fa-dataprotection__alert--warning">{{ t('saveFirst') }}</p>
      <template v-if="!view.locked">
        <div class="fa-dataprotection__field">
          <label :for="`${id}-select`">{{ t('decision') }}</label>
          <select :id="`${id}-select`" v-model="decision">
            <option value="" disabled>{{ t('chooseDecision') }}</option>
            <option v-for="entry in profile.decisions" :key="entry.key" :value="entry.key">{{ entry.title }}</option>
          </select>
        </div>
        <p v-if="deviation" class="fa-dataprotection__note fa-dataprotection__note--blocking" role="status">{{ t('deviationHint') }}</p>
        <div class="fa-dataprotection__field" :class="{ 'fa-dataprotection__field--required': deviation }">
          <label :for="`${id}-why`">{{ t('decisionJustification') }}</label>
          <textarea :id="`${id}-why`" v-model="justification" rows="3" :aria-required="deviation" />
        </div>
        <div v-if="decision === 'freigabe_mit_auflagen'" class="fa-dataprotection__field fa-dataprotection__field--required">
          <label :for="`${id}-cond`">{{ t('conditions') }}</label>
          <textarea :id="`${id}-cond`" v-model="conditions" rows="3" />
        </div>
        <FaButton variant="primary" :disabled="!decision || dirty" :loading="busy === 'decided'" :label="t('decide')" @click="submit" />
      </template>
    </section>
    <section v-if="profile.profile.release_mode === 'dokumentation'" class="fa-dataprotection__panel" :aria-labelledby="`${id}-dpo`">
      <h3 :id="`${id}-dpo`">{{ t('dpoTitle') }}</h3>
      <p v-if="view.dpo_requested_from" class="fa-dataprotection__muted">
        {{ t('dpoRecorded', { person: view.dpo_requested_from, date: formatDate(view.dpo_requested_on, locale) }) }}
      </p>
      <div v-if="!view.locked" class="fa-dataprotection__grid">
        <div class="fa-dataprotection__field">
          <label :for="`${id}-from`">{{ t('dpoFrom') }}</label>
          <input :id="`${id}-from`" v-model="dpoFrom" type="text" />
        </div>
        <div class="fa-dataprotection__field">
          <label :for="`${id}-on`">{{ t('dpoOn') }}</label>
          <input :id="`${id}-on`" v-model="dpoOn" type="date" />
        </div>
      </div>
      <FaButton v-if="!view.locked" :disabled="!dpoFrom.trim() || !dpoOn || dirty" :loading="busy === 'dpo'" :label="t('dpoRecord')" @click="emit('dpo-request', dpoFrom.trim(), dpoOn)" />
    </section>
    <section class="fa-dataprotection__panel" :aria-labelledby="`${id}-release`">
      <h3 :id="`${id}-release`">{{ t('releaseTitle') }}</h3>
      <template v-if="view.locked">
        <p>{{ t('releasedBy', { person: view.released_by ?? '', date: when(view.released_at) }) }}</p>
        <h4 v-if="view.release_open_points.length">{{ t('releaseOpenPoints') }}</h4>
        <ul class="fa-dataprotection__issues">
          <li v-for="point in view.release_open_points" :key="point">{{ point }}</li>
        </ul>
      </template>
      <template v-else>
        <p v-if="view.release_blockers.length" class="fa-dataprotection__alert fa-dataprotection__alert--warning">
          {{ t('releaseBlockers') }} {{ view.release_blockers[0] }}
        </p>
        <p v-else-if="view.open_points.length" class="fa-dataprotection__muted">{{ t('releaseInfo') }}</p>
        <p v-if="actor && view.editors.includes(actor)" class="fa-dataprotection__muted" data-testid="dsfa-four-eyes">{{ t('fourEyesHint') }}</p>
        <FaButton icon="lock" :disabled="!canRelease" :loading="busy === 'released'" :label="t('release')" @click="emit('release')" />
      </template>
    </section>
  </div>
</template>
