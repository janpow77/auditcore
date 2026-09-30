<script setup lang="ts">
import FaThemeSwitch from './FaThemeSwitch.vue'

withDefaults(defineProps<{ brand?: string; logo?: string; logoAlt?: string; fishImage?: string; title?: string; subtitle?: string }>(), {
  brand: 'FlowAudit', logo: '', logoAlt: 'Logo', fishImage: '', title: 'Willkommen zurück', subtitle: 'Melden Sie sich an, um fortzufahren.',
})
</script>

<template>
  <main class="fa-login-layout">
    <section class="fa-login-card" aria-labelledby="fa-login-title">
      <a class="fa-app-brand fa-login-brand" href="/" aria-label="Startseite">
        <img v-if="logo" class="fa-app-brand__logo" :src="logo" :alt="logoAlt">
        <span v-else class="fa-app-brand__mark" aria-hidden="true">F</span>
        <span class="fa-app-brand__name">{{ brand }}</span>
      </a>
      <h1 id="fa-login-title">{{ title }}</h1>
      <p class="fa-login-subtitle">{{ subtitle }}</p>
      <slot />
    </section>
    <aside class="fa-login-art" aria-hidden="true">
      <div class="fa-login-art__water" />
      <img v-if="fishImage" class="fa-login-fish fa-login-fish__image" :src="fishImage" alt="">
      <svg v-else class="fa-login-fish" viewBox="0 0 180 112" role="presentation">
        <path class="fa-login-fish__tail" d="M45 57 14 35v44z" />
        <path class="fa-login-fish__body" d="M45 56c19-27 64-30 96 0-32 30-77 27-96 0Z" />
        <path class="fa-login-fish__fin" d="M88 32 103 12l18 27M88 80l15 20 18-27" />
        <circle class="fa-login-fish__eye" cx="122" cy="51" r="3.5" />
        <path class="fa-login-fish__gill" d="M108 42q9 14 0 28" />
      </svg>
      <span class="fa-login-bubble fa-login-bubble--one" />
      <span class="fa-login-bubble fa-login-bubble--two" />
      <p class="fa-login-art__caption">Klarheit in jedem Schritt.</p>
    </aside>
    <div class="fa-login-theme"><slot name="theme"><FaThemeSwitch /></slot></div>
  </main>
</template>
