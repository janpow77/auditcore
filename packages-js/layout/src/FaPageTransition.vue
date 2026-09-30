<script setup lang="ts">
withDefaults(defineProps<{ name?: string; mode?: 'in-out' | 'out-in' | 'default'; appear?: boolean }>(), {
  name: 'fa-page', mode: 'out-in', appear: true,
})
</script>

<template>
  <Transition :name="name" :mode="mode" :appear="appear">
    <slot />
  </Transition>
</template>
