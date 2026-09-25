<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import FaBadge from '../../base/FaBadge.vue'
import { useI18n } from '../../i18n'
import { screeningMessages } from '../messages'
import type { Outcome, ReviewView, SettingsView } from '../types'
import { awaitsSecondReview, canDecide, formatDate, requiresFourEyes, validateDecision, type ViewMessage } from '../view'
import ScreeningReviewTrail from './ScreeningReviewTrail.vue'

const props = defineProps<{ review: ReviewView; settings: SettingsView | null; busy: boolean; hitId: string }>()
const emit = defineEmits<{
  decide: [outcome: Outcome, reason: string, fourEyes: boolean]
  secondReview: [approve: boolean, reason: string]
}>()

const { t } = useI18n(screeningMessages)
const outcome = ref<Outcome | null>(null)
const reason = ref('')
const fourEyes = ref(false)
const errors = ref<ViewMessage[]>([])
const outcomes: Outcome[] = ['confirmed', 'dismissed', 'deferred']
const policy = computed(() => outcome.value !== null && requiresFourEyes(outcome.value, props.settings))
const errorTexts = computed(() => errors.value.map((error) => t(error.key, error.params)))

watch(() => [props.hitId, props.review.sequence], () => {
  outcome.value = null
  reason.value = ''
  fourEyes.value = false
  errors.value = []
})

function submitDecision(): void {
  errors.value = validateDecision({ outcome: outcome.value, reason: reason.value, fourEyes: fourEyes.value })
  if (errors.value.length || outcome.value === null) return
  emit('decide', outcome.value, reason.value.trim(), fourEyes.value || policy.value)
}

function submitSecond(approve: boolean): void {
  errors.value = reason.value.trim() ? [] : [{ key: 'errorReason' }]
  if (!errors.value.length) emit('secondReview', approve, reason.value.trim())
}
</script>

<template>
  <section class="fa-screening__panel" aria-labelledby="fa-screening-decision-title">
    <h3 id="fa-screening-decision-title">
      {{ awaitsSecondReview(review) ? t('secondReview') : t('decision') }}
      <FaBadge tone="accent">{{ t(`status_${review.status}`) }}</FaBadge>
    </h3>
    <ScreeningReviewTrail :review="review" :format-date="formatDate" />
    <form v-if="canDecide(review)" novalidate @submit.prevent="submitDecision">
      <div class="fa-screening__actions" role="group" :aria-label="t('decision')">
        <button
          v-for="o in outcomes"
          :key="o"
          type="button"
          class="fa-screening__btn"
          :class="`fa-screening__btn--${o}`"
          :aria-pressed="outcome === o"
          :title="t(`hint_${o}`)"
          @click="outcome = o"
        >
          {{ t(`action_${o}`) }}
        </button>
      </div>
      <p v-if="outcome" class="fa-screening__muted">{{ t(`hint_${outcome}`) }}</p>
      <label class="fa-screening__field">
        <span>{{ t('reason') }}</span>
        <textarea v-model="reason" maxlength="4000" required />
      </label>
      <label v-if="!policy" class="fa-screening__check">
        <input v-model="fourEyes" type="checkbox" />{{ t('fourEyes') }}
      </label>
      <p v-else class="fa-screening__muted">{{ t('fourEyesPolicy') }}</p>
      <ul v-if="errorTexts.length" class="fa-screening__errors" role="alert">
        <li v-for="e in errorTexts" :key="e">{{ e }}</li>
      </ul>
      <button class="fa-screening__btn fa-screening__btn--primary" type="submit" :disabled="busy">{{ t('saveDecision') }}</button>
    </form>
    <form v-else-if="awaitsSecondReview(review)" novalidate @submit.prevent>
      <p class="fa-screening__muted">{{ t('secondReviewHint') }}</p>
      <label class="fa-screening__field">
        <span>{{ t('reason') }}</span>
        <textarea v-model="reason" maxlength="4000" required />
      </label>
      <ul v-if="errorTexts.length" class="fa-screening__errors" role="alert">
        <li v-for="e in errorTexts" :key="e">{{ e }}</li>
      </ul>
      <div class="fa-screening__actions">
        <button class="fa-screening__btn fa-screening__btn--primary" type="button" :disabled="busy" @click="submitSecond(true)">{{ t('approve') }}</button>
        <button class="fa-screening__btn" type="button" :disabled="busy" @click="submitSecond(false)">{{ t('reject') }}</button>
      </div>
    </form>
    <p v-else class="fa-screening__muted">{{ t('final') }}</p>
  </section>
</template>
