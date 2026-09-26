<script setup lang="ts">
/**
 * Role tab: `flowaudit:akteur` at pools and lanes (role from the profile's
 * catalogue plus free display name). For flow nodes it shows the role
 * inherited from the lane or pool.
 */
import { computed } from 'vue'
import { label, roleOf, rolesFor, type Actor } from '@auditcore/bpmn-flowaudit'
import { actorAfter, inheritedRole, isContainerType } from '@auditcore/bpmn-flowaudit/ui'
import FaIcon from '../../components/base/FaIcon.vue'
import { useI18n } from '../../i18n/useI18n'
import { useEditorContext } from '../../stores/context'

const { selection, editor, profile, readonly } = useEditorContext()
const { t, locale } = useI18n()

const type = computed(() => selection.type.value ?? '')
const isContainer = computed(() => isContainerType(type.value))
const actor = computed(() => selection.extensions.value.actor ?? {})
const roles = computed(() => rolesFor(profile(), editor.state.info?.programmingPeriod))

const inherited = computed(() => {
  void selection.version.value
  const element = selection.element.value
  if (!element || isContainer.value) return null
  return inheritedRole(editor.model(), element.id, profile(), locale.value, t)
})

const update = (patch: Partial<Actor>) => selection.write({ actor: actorAfter(actor.value, patch) })

function choose(code: string): void {
  update({ role: code || undefined })
  const role = roleOf(profile(), code)
  if (selection.element.value && role && !selection.property('name')) selection.rename(label(role.label, locale.value))
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
