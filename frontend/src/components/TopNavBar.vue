<template>
  <v-app-bar :height="50" flat class="top-nav-bar" :order="-1">
    <div class="d-flex align-center w-100 h-100 px-3 px-md-4">
      <!-- Left: Logo & Workspace Dropdown -->
      <div class="d-flex align-center flex-shrink-0">
        <!-- Brand Logo -->
        <div class="d-flex align-center cursor-pointer mr-3 brand-wrap" @click="store.activeView = 'workspace'">
          <RequestLabLogo :size="26" />
        </div>

        <!-- Vertical Divider -->
        <div class="nav-divider d-none d-md-block mr-3"></div>

        <!-- Workspace Selector Chip -->
        <div class="workspace-chip d-none d-md-flex align-center rounded">
          <v-icon size="14" class="mr-1.5 text-muted">mdi-account-group-outline</v-icon>
          <span class="text-caption font-weight-medium text-truncate" style="max-width: 160px;">
            {{ isAuthenticated ? `${store.user?.email.split('@')[0]}'s Workspace` : 'Default Workspace' }}
          </span>
          <v-icon size="14" class="ml-1.5 text-secondary">mdi-chevron-down</v-icon>
        </div>
      </div>

      <!-- Center: Postman-style Rounded Pill Search Bar -->
      <div class="center-search-section flex-grow-1 d-flex justify-center px-4">
        <div class="nav-search-wrap d-none d-sm-flex align-center px-3">
          <v-icon size="14" class="text-muted mr-2">mdi-magnify</v-icon>
          <input
            v-model="store.searchFilter"
            type="text"
            placeholder="Search RequestLab..."
            class="nav-search-input"
          />
          <button
            v-if="store.searchFilter"
            type="button"
            class="search-clear-btn"
            @click="store.searchFilter = ''"
          >
            <v-icon size="12">mdi-close</v-icon>
          </button>
        </div>
      </div>

      <!-- Right: Navigation Links & Controls -->
      <div class="right-controls-group d-flex align-center flex-shrink-0">
        <!-- Navigation Tool Tabs -->
        <div class="nav-links d-none d-md-flex align-center mr-2">
          <button
            type="button"
            :class="['nav-link-item', { active: store.activeView === 'workspace' }]"
            @click="store.activeView = 'workspace'"
          >
            Workspace
          </button>
          <button
            type="button"
            :class="['nav-link-item', { active: store.activeView === 'dashboard' }]"
            @click="store.activeView = 'dashboard'"
          >
            Dashboard
          </button>
          <button
            type="button"
            :class="['nav-link-item', { active: store.activeView === 'history' }]"
            @click="handleHistoryClick"
          >
            History
          </button>
        </div>

        <div class="nav-divider d-none d-md-block mr-2"></div>

        <!-- Sidebar Toggle Button -->
        <button
          type="button"
          class="nav-icon-btn"
          :class="{ active: sidebarOpen }"
          :title="sidebarOpen ? 'Hide Collections Sidebar (Ctrl+B)' : 'Show Collections Sidebar (Ctrl+B)'"
          @click="emit('toggle-sidebar')"
        >
          <v-icon size="16">{{ sidebarOpen ? 'mdi-dock-left' : 'mdi-dock-window' }}</v-icon>
        </button>

        <!-- Guest Indicator Pill -->
        <div
          v-if="!isAuthenticated"
          class="guest-status-tag d-none d-lg-flex align-center px-3 py-1 rounded cursor-pointer"
          title="Guest Mode: Free instant testing. Sign in to save collections."
          @click="emit('open-auth', 'Sign in to save your requests and view history across sessions.')"
        >
          <span class="guest-dot mr-2"></span>
          <span class="text-caption font-weight-medium">Guest Mode</span>
        </div>

        <!-- Authenticated User Menu -->
        <div v-if="isAuthenticated" class="d-flex align-center">
          <v-menu location="bottom end">
            <template #activator="{ props }">
              <button v-bind="props" type="button" class="user-btn d-flex align-center px-2 py-1 rounded">
                <span class="user-avatar mr-1.5">{{ userInitial }}</span>
                <span class="text-caption font-weight-medium text-truncate mr-1" style="max-width: 120px;">
                  {{ store.user?.email }}
                </span>
                <v-icon size="14" class="text-secondary">mdi-chevron-down</v-icon>
              </button>
            </template>
            <v-list density="compact" class="user-menu-list pa-1" elevation="4">
              <v-list-item class="px-3 py-2">
                <v-list-item-title class="text-caption text-secondary">Signed in as</v-list-item-title>
                <v-list-item-subtitle class="font-weight-bold text-caption mt-1">{{ store.user?.email }}</v-list-item-subtitle>
              </v-list-item>
              <v-divider class="my-1" />
              <v-list-item
                prepend-icon="mdi-view-dashboard-outline"
                title="Dashboard"
                class="rounded text-caption"
                @click="store.activeView = 'dashboard'"
              />
              <v-list-item
                prepend-icon="mdi-history"
                title="History"
                class="rounded text-caption"
                @click="store.activeView = 'history'"
              />
              <v-divider class="my-1" />
              <v-list-item
                prepend-icon="mdi-logout"
                title="Sign Out"
                class="rounded text-caption text-red"
                @click="logout"
              />
            </v-list>
          </v-menu>
        </div>

        <!-- Sign In Button for Guests (Postman Style Accent) -->
        <button
          v-else
          type="button"
          class="signin-btn font-weight-bold rounded"
          @click="emit('open-auth', 'Sign in to save requests into personal collections.')"
        >
          Sign In
        </button>
      </div>
    </div>
  </v-app-bar>
</template>

<script setup>
import { computed, defineProps, defineEmits } from "vue";
import RequestLabLogo from "@/components/RequestLabLogo.vue";
import { store, isAuthenticated, logout } from "@/stores/appState";

defineProps({
  sidebarOpen: { type: Boolean, default: true },
});

const emit = defineEmits(["toggle-sidebar", "open-auth"]);

const userInitial = computed(() => {
  if (!store.user?.email) return "U";
  return store.user.email.charAt(0).toUpperCase();
});

function handleHistoryClick() {
  if (!isAuthenticated.value) {
    emit("open-auth", "Sign in to view your past API execution history.");
    return;
  }
  store.activeView = "history";
}
</script>

<style scoped>
.top-nav-bar {
  background: var(--bg-header) !important;
  border-bottom: 1px solid var(--border-color) !important;
  color: var(--text-primary) !important;
  user-select: none;
  z-index: 1006 !important;
}

.top-nav-bar :deep(.v-toolbar__content) {
  padding: 0 !important;
  height: 52px !important;
}

.brand-wrap {
  transition: opacity 0.15s ease;
}

.brand-wrap:hover {
  opacity: 0.9;
}

.nav-divider {
  width: 1px;
  height: 20px;
  background: var(--border-color);
}

.right-controls-group {
  gap: 12px;
}

@media (min-width: 960px) {
  .right-controls-group {
    gap: 14px;
  }
}

.workspace-chip {
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-color);
  font-size: 0.8rem;
  color: var(--text-secondary);
  height: 32px;
  padding: 0 14px;
  border-radius: 6px;
  transition: all 0.15s ease;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}

.workspace-chip:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-color-subtle);
}

.nav-links {
  height: 100%;
}

.nav-link-item {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 0.82rem;
  font-weight: 500;
  padding: 0 14px;
  height: 52px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s ease;
}

.nav-link-item:hover {
  color: var(--text-primary);
}

.nav-link-item.active {
  color: var(--text-primary);
  font-weight: 600;
  border-bottom: 2px solid var(--primary);
}

.nav-search-wrap {
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  height: 30px;
  width: 320px;
  max-width: 100%;
  transition: all 0.15s ease;
}

.nav-search-wrap:focus-within {
  border-color: var(--primary);
  background: var(--bg-surface);
}

.nav-search-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.8rem;
  width: 100%;
}

.nav-search-input::placeholder {
  color: var(--text-muted);
}

.search-clear-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 2px;
}

.search-clear-btn:hover {
  color: var(--text-primary);
}

.nav-icon-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 5px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.15s ease;
}

.nav-icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-color-subtle);
}

.nav-icon-btn.active {
  color: var(--primary);
}

.guest-status-tag {
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-color);
  font-size: 0.75rem;
  color: var(--text-secondary);
  height: 32px;
  transition: all 0.15s ease;
}

.guest-status-tag:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.guest-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
}

.signin-btn {
  background: var(--primary);
  color: var(--primary-fg, #042416);
  font-weight: 700;
  border: none;
  height: 32px;
  padding: 0 16px;
  border-radius: 5px;
  font-size: 0.8rem;
  letter-spacing: 0.01em;
  cursor: pointer;
  transition: background 0.15s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.signin-btn:hover {
  background: var(--primary-hover);
}

.user-btn {
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  height: 34px;
  padding: 0 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.user-btn:hover {
  background: var(--bg-hover);
}

.user-avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--primary);
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-menu-list {
  background: var(--bg-surface-elevated) !important;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}
</style>
