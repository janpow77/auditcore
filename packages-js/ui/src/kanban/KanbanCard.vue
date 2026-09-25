<script setup lang="ts">
import { computed } from 'vue'
import { deadlineState, type Card } from '@flowaudit/kanban-core'
import FaIcon from '../base/FaIcon.vue'
import { formatDate, useI18n, type Locale } from '../i18n'
import { badgeStyle, cardAge, preview, PRIORITY_TONES, textOn } from './cardView'
import { kanbanMessages } from './messages'

const props = withDefaults(defineProps<{
  card: Card
  done?: boolean
  today: string
  now?: number
  canToggle?: boolean
  grabbed?: boolean
  dragging?: boolean
  describedBy?: string
  locale?: Locale
}>(), { done: false, now: () => Date.now(), canToggle: false, grabbed: false, dragging: false, describedBy: undefined, locale: undefined })

const emit = defineEmits<{ open: [card: Card]; 'toggle-done': [card: Card] }>()
const { t, locale: active } = useI18n(kanbanMessages, () => props.locale)

const due = computed(() => deadlineState(props.card.due, props.today))
const checklistDone = computed(() => props.card.checklist.filter((item) => item.done).length)
const age = computed(() => cardAge(props.card.created_at, props.now))
const style = computed(() => {
  const result: Record<string, string> = {}
  if (props.card.color) {
    result['--fa-kanban-card-bg'] = props.card.color
    if (textOn(props.card.color) === 'light') result['--fa-kanban-card-fg'] = '#f8fafc'
  }
  if (props.card.image) result.backgroundImage = `linear-gradient(rgb(0 0 0 / 0.35), rgb(0 0 0 / 0.35)), url("${encodeURI(props.card.image)}")`
  return result
})
const label = computed(() => [props.card.badge, props.card.title, t(`priority_${props.card.priority}`), props.card.due ? t(`due_${due.value}`) : ''].filter(Boolean).join(', '))
</script>

<template>
  <article
    class="fa-kanban-card"
    :class="[`fa-kanban-card--${card.priority}`, { 'fa-kanban-card--done': done, 'fa-kanban-card--styled': card.color || card.image, 'fa-kanban-card--grabbed': grabbed, 'fa-kanban-card--dragging': dragging }]"
    :style="style"
    :data-card-id="card.id"
    tabindex="0"
    role="listitem"
    :aria-roledescription="t('cardRole')"
    :aria-label="label"
    :aria-describedby="describedBy"
    :aria-pressed="grabbed ? 'true' : undefined"
    @click="emit('open', card)"
  >
    <div class="fa-kanban-card__head">
      <button
        v-if="canToggle"
        type="button"
        class="fa-kanban-card__check"
        :aria-label="done ? t('markOpen') : t('markDone')"
        :aria-pressed="done"
        @click.stop="emit('toggle-done', card)"
      >
        <FaIcon v-if="done" name="check" :size="12" />
      </button>
      <span v-if="card.badge" class="fa-kanban-card__badge" :style="badgeStyle(card.badge)">{{ card.badge }}</span>
      <h3 class="fa-kanban-card__title">{{ card.title }}</h3>
      <FaIcon name="grip" class="fa-kanban-card__grip" :size="16" />
    </div>
    <p v-if="card.description && !done" class="fa-kanban-card__text">{{ preview(card.description) }}</p>
    <div v-if="!done && (card.tags.length || card.checklist.length)" class="fa-kanban-card__chips">
      <span v-for="tag in card.tags.slice(0, 3)" :key="tag" class="fa-kanban-card__tag">{{ tag }}</span>
      <span v-if="card.tags.length > 3" class="fa-kanban-card__tag">{{ t('moreTags', { count: card.tags.length - 3 }) }}</span>
      <span v-if="card.checklist.length" class="fa-kanban-card__tag" :class="{ 'is-complete': checklistDone === card.checklist.length }">
        <FaIcon name="check" :size="11" /> {{ checklistDone }}/{{ card.checklist.length }}
      </span>
    </div>
    <div class="fa-kanban-card__meta">
      <span class="fa-kanban-card__priority" :class="`is-${PRIORITY_TONES[card.priority]}`">{{ t(`priority_${card.priority}`) }}</span>
      <span v-if="card.due" class="fa-kanban-card__due" :class="`is-${due}`" :title="t('dueOn', { date: formatDate(card.due, active) })">
        <FaIcon name="clock" :size="12" /> {{ formatDate(card.due, active) }}
      </span>
      <span v-if="card.attachments.length" :title="t('attachments', { count: card.attachments.length })"><FaIcon name="paperclip" :size="12" /> {{ card.attachments.length }}</span>
      <span v-if="card.links.length" :title="t('links', { count: card.links.length })"><FaIcon name="share" :size="12" /> {{ card.links.length }}</span>
      <span v-if="card.assignees.length" class="fa-kanban-card__people"><FaIcon name="user" :size="12" /> {{ card.assignees.length }}</span>
      <span v-if="age" class="fa-kanban-card__age">{{ t(age.key, { count: age.count }) }}</span>
    </div>
  </article>
</template>
