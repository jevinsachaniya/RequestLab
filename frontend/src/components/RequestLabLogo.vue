<template>
  <div class="requestlab-logo-lockup d-inline-flex align-center cursor-pointer user-select-none">
    <!-- Vector Flask + Paper Airplane Icon -->
    <div class="logo-icon-wrap d-flex align-center justify-center flex-shrink-0" :style="{ width: `${size}px`, height: `${size}px` }">
      <svg
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        class="w-100 h-100 logo-svg"
      >
        <!-- Flask Outline -->
        <path
          d="M26 12 H38 M28 12 V24 L14 50 C12 54 15 58 19 58 H45 C49 58 52 54 50 50 L36 24 V12"
          class="flask-stroke"
          stroke-width="4.5"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
        <!-- Paper Airplane (Tilted Flight inside beaker) -->
        <polygon points="41,36 21,46 28,42" fill="#5eead4"/>
        <polygon points="41,36 28,42 32,50" fill="#14b8a6"/>
        <polygon points="28,42 32,50 31,44" fill="#0f766e"/>
      </svg>
    </div>

    <!-- Typography -->
    <div v-if="showText" class="logo-text-block d-flex flex-column ml-2">
      <div class="brand-name d-flex align-baseline">
        <span class="request-part font-weight-bold">Request</span>
        <span class="lab-part font-weight-bold">Lab</span>
      </div>
      <span v-if="showTagline" class="brand-tagline">Your API Testing Workspace</span>
    </div>
  </div>
</template>

<script setup>
import { defineProps } from "vue";

defineProps({
  size: {
    type: [Number, String],
    default: 26,
  },
  showText: {
    type: Boolean,
    default: true,
  },
  showTagline: {
    type: Boolean,
    default: false,
  },
});
</script>

<style scoped>
.requestlab-logo-lockup {
  line-height: 1;
  text-decoration: none;
}

.logo-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-svg {
  display: block;
}

.flask-stroke {
  stroke: var(--text-primary);
  transition: stroke 0.2s ease;
}

.brand-name {
  font-size: 1.05rem;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.request-part {
  color: var(--text-primary);
}

.lab-part {
  color: #2dd4bf;
}

.brand-tagline {
  font-size: 0.62rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--text-muted);
  margin-top: 1px;
}
</style>

