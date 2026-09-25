<script setup lang="ts">
/**
 * Role tab: `flowaudit:akteur` at pools and lanes (role from the profile's
 * catalogue plus free display name). For flow nodes it shows the role
 * inherited from the lane or pool.
 */
import { computed } from 'vue'
import { label, roleOf, rolesFor, type DiagramElement } from '@flowaudit/bpmn-flowaudit'
import FaIcon from '../../components/base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'

const { selection, editor, profile, readonly } = useEditorContext()
const { t, locale } = useI18n()

const type = computed(() => selection.type.value ?? '')
const isContainer = computed(() => type.value === 'bpmn:Participant' || type.value === 'bpmn:Lane')
const actor = computed(() => selection.extensions.value.actor ?? {})
const roles = computed(() => rolesFor(profile(), editor.state.info?.programmingPeriod))

const inherited = computed(() => {
  void selection.version.value
  const element = selection.element.value
  if (!element || isContainer.value) return null
  const found = editor.model().byId.get(element.id)?.actor
  const role = roleOf(profile(), found?.role)
  return found ? { name: found.sourceName, role: role ? label(role.label, locale.value) : t('role.none') } : null
})

function update(patch: { role?: string; displayName?: string }): void {
  const next = { ...actor.value, ...patch }
  selection.write({ actor: next.role || next.displayName ? next : undefined })
}

function choose(code: string): void {
  update({ role: code || undefined })
  const element = selection.element.value as DiagramElement | null
  const role = roleOf(profile(), code)
  if (element && role && !selection.property('name')) selection.rename(label(role.label, locale.value))
}
</script>

<template>
  <div class="fa-tab-role">
    <template v-if="isContainer">
      <p class="fa-help">{{ t('props.role.help') }}</p>
      <div class="fa-role-grid" role="radiogroup" :aria-label="t('props.role.role')">
        <button
          v-for="role in roles"
          :key="role.code"
          type="button"
          role="radio"
          class="fa-role-option"
          :aria-checked="actor.role === role.code"
          :disabled="readonly()"
          :style="{ '--fa-role-fill': role.color.fill, '--fa-role-stroke': role.color.stroke }"
          @click="choose(actor.role === role.code ? '' : role.code)"
        >
          <FaIcon :name="role.icon" :size="20" />
          <span class="fa-role-option__short">{{ role.short }}</span>
          <span class="fa-role-option__label">{{ label(role.label, locale) }}</span>
        </button>
      </div>
      <label class="fa-field fa-section">
        <span class="fa-label">{{ t('props.role.displayName') }}</span>
        <input class="fa-input" :value="actor.displayName ?? ''" :disabled="readonly()" @change="update({ displayName: ($event.target as HTMLInputElement).value.trim() || undefined })" />
      </label>
    </template>
    <template v-else>
      <p class="fa-help">{{ t('props.role.onlyContainers') }}</p>
      <p v-if="inherited" class="fa-badge fa-badge--info">{{ t('props.role.inherited', inherited) }}</p>
    </template>
  </div>
</template>

<style>
.fa-role-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 6px;
  margin-top: 8px;
}

.fa-role-option {
  display: grid;
  grid-template-columns: 24px auto;
  grid-template-rows: auto auto;
  column-gap: 8px;
  align-items: center;
  padding: 7px 9px;
  border: 1px solid var(--fa-border);
  border-radius: var(--fa-radius-sm);
  background: var(--fa-surface);
  color: var(--fa-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.fa-role-option svg {
  grid-row: 1 / 3;
  color: var(--fa-role-stroke);
}

.fa-role-option[aria-checked='true'] {
  border-color: var(--fa-role-stroke);
  background: var(--fa-role-fill);
  color: #1a202c;
}

.fa-role-option__short {
  font-weight: 700;
  font-size: 12px;
}

.fa-role-option__label {
  font-size: 12px;
  color: inherit;
  opacity: 0.85;
}
</style>
