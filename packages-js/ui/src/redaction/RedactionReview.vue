<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  isRedactionArrow,
  redactionPoint,
  redactionReview,
  type RedactionController,
  type RedactionData,
  type RedactionTranslate,
} from '@auditcore/ui-core'
import FaButton from '../base/FaButton.vue'

const props = defineProps<{ id: string; controller: RedactionController; state: RedactionData; t: RedactionTranslate }>()
const view = computed(() => redactionReview(props.state, props.t))
const overlay = ref<HTMLElement | null>(null)

function point(event: PointerEvent): [number, number] {
  const bounds = overlay.value?.getBoundingClientRect()
  return bounds ? redactionPoint(bounds, event.clientX, event.clientY) : [0, 0]
}

function capture(event: PointerEvent): void {
  overlay.value?.setPointerCapture?.(event.pointerId)
}

function onDown(event: PointerEvent): void {
  if (event.button !== 0) return
  props.controller.pointerDown(point(event))
  capture(event)
}

function onMove(event: PointerEvent): void {
  props.controller.pointerMove(point(event))
}

function onUp(event: PointerEvent): void {
  props.controller.pointerUp(point(event))
}

function onResizeStart(areaId: string, event: PointerEvent): void {
  props.controller.startResize(areaId)
  capture(event)
}

function onAreaKey(areaId: string, mode: 'move' | 'resize', event: KeyboardEvent): void {
  if (mode === 'move' && (event.key === 'Delete' || event.key === 'Backspace')) {
    event.preventDefault()
    props.controller.removeArea(areaId)
    return
  }
  if (!isRedactionArrow(event.key)) return
  event.preventDefault()
  props.controller.nudgeArea(areaId, event.key, mode, event.shiftKey)
}

const checked = (event: Event): boolean => (event.target as HTMLInputElement).checked
</script>

<template>
  <section v-if="view" class="fa-redaction__card" :aria-labelledby="`${id}-review`" data-testid="redaction-review">
    <h3 :id="`${id}-review`" class="fa-redaction__heading">{{ t('reviewHeading') }}</h3>
    <div class="fa-redaction__layout">
      <section class="fa-redaction__viewer" :aria-label="t('pageView')">
        <p class="fa-redaction__muted">{{ t('reviewHelp') }}</p>
        <div class="fa-redaction__pager">
          <FaButton size="sm" icon="chevron-left" icon-only :label="t('previousPage')" :disabled="view.page <= 1" data-testid="redaction-previous" @click="controller.showPage(view.page - 1)" />
          <span class="fa-redaction__pager-text" aria-live="polite">{{ view.pageText }}</span>
          <FaButton size="sm" icon="chevron-right" icon-only :label="t('nextPage')" :disabled="view.page >= view.pageCount" data-testid="redaction-next" @click="controller.showPage(view.page + 1)" />
          <FaButton size="sm" data-testid="redaction-add-area" @click="controller.addDefaultArea">{{ t('addArea') }}</FaButton>
        </div>
        <div class="fa-redaction__page" :style="{ aspectRatio: view.aspect }">
          <img v-if="state.preview" class="fa-redaction__image" :src="state.preview" :alt="t('pageImage', { page: view.page })" draggable="false" />
          <p v-else-if="state.previewError" class="fa-redaction__error" role="alert">{{ t('previewFailed', { message: state.previewError }) }}</p>
          <p v-else class="fa-redaction__muted" role="status">{{ t('previewLoading') }}</p>
          <div ref="overlay" class="fa-redaction__overlay" data-testid="redaction-overlay" @pointerdown="onDown" @pointermove="onMove" @pointerup="onUp" @pointercancel="controller.cancelGesture">
            <button
              v-for="box in view.boxes"
              :key="box.key"
              type="button"
              :class="['fa-redaction__box', box.on ? 'fa-redaction__box--on' : 'fa-redaction__box--off']"
              :style="box.style"
              :aria-pressed="box.on"
              :aria-label="box.label"
              :title="box.label"
              :data-candidate="box.id"
              @pointerdown.stop
              @click="controller.toggle(box.id)"
            ></button>
            <div v-for="area in view.areas" :key="area.id" class="fa-redaction__area" :style="area.style" :data-area="area.number" @pointerdown.stop>
              <button type="button" class="fa-redaction__area-move" :aria-label="area.label" @keydown="onAreaKey(area.id, 'move', $event)"></button>
              <button type="button" class="fa-redaction__area-remove" :aria-label="area.removeLabel" :title="area.removeLabel" @click="controller.removeArea(area.id)">×</button>
              <button type="button" class="fa-redaction__area-resize" :aria-label="area.resizeLabel" :title="area.resizeLabel" @pointerdown.stop="onResizeStart(area.id, $event)" @keydown="onAreaKey(area.id, 'resize', $event)"></button>
            </div>
            <div v-if="view.draft" class="fa-redaction__draft" :style="view.draft"></div>
          </div>
        </div>
        <p v-if="view.areaLimit" class="fa-redaction__error" role="status">{{ view.areaLimit }}</p>
        <p v-if="view.pageButtons.length" class="fa-redaction__pages">
          <span>{{ t('pagesWithFindings') }}</span>
          <button
            v-for="number in view.pageButtons"
            :key="number"
            type="button"
            class="fa-redaction__page-link"
            :aria-current="number === view.page ? 'page' : undefined"
            @click="controller.showPage(number)"
          >{{ number }}</button>
          <span v-if="view.morePages">…</span>
        </p>
      </section>

      <aside class="fa-redaction__side" :aria-label="t('findings')">
        <div class="fa-redaction__summary">
          <p class="fa-redaction__summary-text" data-testid="redaction-summary">{{ view.summary }}</p>
          <div class="fa-redaction__buttons">
            <FaButton size="sm" :disabled="!view.hasCandidates" data-testid="redaction-select-all" @click="controller.setAll(true)">{{ t('selectAll') }}</FaButton>
            <FaButton size="sm" :disabled="!view.hasCandidates" data-testid="redaction-deselect-all" @click="controller.setAll(false)">{{ t('deselectAll') }}</FaButton>
          </div>
          <div v-if="view.sources.length > 1" class="fa-redaction__sources" role="group" :aria-label="t('sources')">
            <button
              v-for="entry in view.sources"
              :key="entry.source"
              type="button"
              :class="['fa-redaction__source', `fa-redaction__source--${entry.state}`]"
              :aria-pressed="entry.state === 'all'"
              :title="entry.title"
              :data-source="entry.source"
              @click="controller.setSource(entry.source, entry.state !== 'all')"
            >{{ entry.text }}</button>
          </div>
        </div>
        <p v-if="view.noText" class="fa-redaction__notice fa-redaction__notice--warning">{{ view.noText }}</p>
        <p v-if="view.outside" class="fa-redaction__notice">{{ view.outside }}</p>
        <label v-if="view.showFilter" class="fa-redaction__field">
          <span class="fa-redaction__label">{{ t('filter') }}</span>
          <input class="fa-redaction__input" type="search" :placeholder="t('filterPlaceholder')" :value="state.filter" data-testid="redaction-filter" @input="controller.setFilter(($event.target as HTMLInputElement).value)" />
        </label>
        <p v-if="!view.hasCandidates" class="fa-redaction__muted">{{ t('noCandidates') }}</p>
        <p v-if="view.noMatch" class="fa-redaction__muted">{{ view.noMatch }}</p>
        <ul v-if="view.groups.length" class="fa-redaction__groups">
          <li v-for="group in view.groups" :key="group.key" class="fa-redaction__group">
            <div class="fa-redaction__group-head">
              <input type="checkbox" :checked="group.state === 'all'" :indeterminate="group.state === 'some'" :aria-label="group.label" @change="controller.setGroup(group.key, checked($event))" />
              <button type="button" class="fa-redaction__group-toggle" :aria-expanded="group.expanded" @click="controller.toggleExpanded(group.key)">
                <span :class="['fa-redaction__text', group.state === 'none' && 'fa-redaction__text--off']">{{ group.text }}</span>
                <span class="fa-redaction__meta">{{ group.meta }}</span>
              </button>
            </div>
            <ul v-if="group.expanded" class="fa-redaction__items">
              <li v-for="item in group.items" :key="item.id">
                <span class="fa-redaction__number">{{ item.number }}.</span>
                <input type="checkbox" :checked="item.checked" :aria-label="item.label" @change="controller.toggle(item.id)" />
                <button v-if="item.page" type="button" class="fa-redaction__link" @click="controller.showPage(item.page)">{{ t('itemPage', { page: item.page }) }}</button>
                <span v-if="item.text" class="fa-redaction__item-text">{{ item.text }}</span>
                <span v-if="item.extra" class="fa-redaction__item-text">{{ item.extra }}</span>
              </li>
            </ul>
          </li>
        </ul>
        <div v-if="view.more">
          <FaButton size="sm" variant="ghost" data-testid="redaction-more" @click="controller.showMore">{{ view.more }}</FaButton>
        </div>
        <div v-if="view.hiddenText" class="fa-redaction__hidden">
          <p><strong>{{ t('hiddenHeading') }}</strong></p>
          <p>{{ view.hiddenText }}</p>
        </div>
        <label class="fa-redaction__check">
          <input type="checkbox" data-testid="redaction-sanitize" :checked="state.sanitize" @change="controller.setOption('sanitize', checked($event))" />
          <span>{{ t('sanitize') }}</span>
        </label>
        <p class="fa-redaction__muted">{{ t('applyHelp') }}</p>
        <div class="fa-redaction__actions">
          <FaButton data-testid="redaction-back" @click="controller.back">{{ t('back') }}</FaButton>
          <FaButton variant="primary" :loading="state.busy === 'apply'" data-testid="redaction-apply" @click="controller.apply">{{ t('apply') }}</FaButton>
        </div>
      </aside>
    </div>
  </section>
</template>
