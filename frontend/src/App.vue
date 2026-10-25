<template>
  <v-app class="api-sentinel-app">
    <!-- Top Navigation Bar -->
    <TopNavBar
      :sidebar-open="sidebarOpen"
      @toggle-sidebar="sidebarOpen = !sidebarOpen"
      @open-auth="promptSignIn"
    />

    <!-- Navigation Drawer for Collections (Left Sidebar) -->
    <v-navigation-drawer
      v-model="sidebarOpen"
      :temporary="isMobile"
      :permanent="!isMobile"
      width="260"
      class="sentinel-sidebar"
    >
      <CollectionsSidebar
        @request-selected="onMobileRequestSelected"
        @require-auth="promptSignIn"
        @toggle-sidebar="sidebarOpen = !sidebarOpen"
      />
    </v-navigation-drawer>

    <!-- Main Workspace Viewport -->
    <v-main class="sentinel-viewport">
      <!-- 1. API Studio Workspace View -->
      <div v-if="store.activeView === 'workspace'" class="h-100 overflow-hidden">
        <!-- Desktop Layout: Solid Developer Split Panes -->
        <div v-if="!isMobile" class="studio-desktop-split">
          <div class="studio-pane studio-request-pane">
            <RequestBuilder
              @open-save-dialog="handleSaveClicked"
            />
          </div>
          <div class="studio-pane studio-response-pane">
            <ResponseViewer />
          </div>
        </div>

        <!-- Mobile Layout: Clean Screen Switcher -->
        <div v-else class="h-100 d-flex flex-column overflow-hidden">
          <div class="mobile-nav-toggle-bar pa-2 d-flex justify-center border-b">
            <v-btn-toggle
              v-model="mobileView"
              mandatory
              density="compact"
              color="primary"
              variant="outlined"
            >
              <v-btn value="request" size="small" class="px-3">
                <v-icon start size="14">mdi-console-line</v-icon>
                Request
              </v-btn>
              <v-btn value="response" size="small" class="px-3 d-flex align-center">
                <v-icon start size="14">mdi-code-braces</v-icon>
                <span>Response</span>
                <span
                  v-if="store.lastResponse?.status_code"
                  class="mobile-status-dot ml-1.5"
                  :style="{ backgroundColor: getStatusColor(store.lastResponse.status_code) }"
                ></span>
              </v-btn>
            </v-btn-toggle>
          </div>

          <div class="flex-grow-1 overflow-hidden">
            <div v-show="mobileView === 'request'" class="h-100 overflow-y-auto">
              <RequestBuilder @open-save-dialog="handleSaveClicked" />
            </div>
            <div v-show="mobileView === 'response'" class="h-100 overflow-y-auto">
              <ResponseViewer />
            </div>
          </div>
        </div>
      </div>

      <!-- 2. Dashboard View -->
      <DashboardView
        v-else-if="store.activeView === 'dashboard'"
        @open-auth="promptSignIn"
      />

      <!-- 3. History View -->
      <HistoryView
        v-else-if="store.activeView === 'history'"
        @open-auth="promptSignIn"
      />
    </v-main>

    <!-- Global Toast / Snackbar -->
    <v-snackbar
      v-model="store.toast.show"
      :color="store.toast.color"
      timeout="3000"
      density="compact"
      location="bottom right"
      class="toast-snackbar"
    >
      <div class="d-flex align-center">
        <span class="text-caption font-weight-medium">{{ store.toast.message }}</span>
      </div>
      <template #actions>
        <v-btn variant="text" size="small" @click="store.toast.show = false">
          Dismiss
        </v-btn>
      </template>
    </v-snackbar>

    <!-- Modals -->
    <AuthDialog
      v-model="showAuthDialog"
      :prompt-message="authPromptMessage"
      @authenticated="onAuthenticated"
    />

    <SaveRequestDialog v-model="showSaveDialog" />
  </v-app>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { useDisplay } from "vuetify";
import TopNavBar from "@/components/TopNavBar.vue";
import CollectionsSidebar from "@/components/CollectionsSidebar.vue";
import RequestBuilder from "@/components/RequestBuilder.vue";
import ResponseViewer from "@/components/ResponseViewer.vue";
import DashboardView from "@/components/DashboardView.vue";
import HistoryView from "@/components/HistoryView.vue";
import AuthDialog from "@/components/AuthDialog.vue";
import SaveRequestDialog from "@/components/SaveRequestDialog.vue";
import { store, isAuthenticated, checkAuth, loadHistory } from "@/stores/appState";

const { smAndDown } = useDisplay();
const isMobile = computed(() => smAndDown.value);

const sidebarOpen = ref(!smAndDown.value);
const mobileView = ref("request");
const showAuthDialog = ref(false);
const showSaveDialog = ref(false);
const authPromptMessage = ref("");

watch(() => store.lastResponse, (val) => {
  if (val && isMobile.value) {
    mobileView.value = "response";
  }
});

watch(isMobile, (mobile) => {
  sidebarOpen.value = !mobile;
});

function handleGlobalKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
    e.preventDefault();
    sidebarOpen.value = !sidebarOpen.value;
  }
}

onMounted(async () => {
  window.addEventListener("keydown", handleGlobalKeydown);

  const savedTheme = localStorage.getItem("api_sentinel_theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);

  if (store.token) {
    const isAuth = await checkAuth();
    if (isAuth) {
      await loadHistory();
    }
  }

  window.addEventListener("api-sentinel-unauthorized", () => {
    promptSignIn("Your session expired. Sign in again to access cloud collections.");
  });
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleGlobalKeydown);
});

function promptSignIn(message = "") {
  authPromptMessage.value = message;
  showAuthDialog.value = true;
}

function handleSaveClicked() {
  if (!isAuthenticated.value) {
    promptSignIn("Sign in to save this request into your personal collections.");
    return;
  }
  showSaveDialog.value = true;
}

function onMobileRequestSelected() {
  if (isMobile.value) {
    sidebarOpen.value = false;
    mobileView.value = "request";
  }
}

function onAuthenticated() {
  if (authPromptMessage.value.includes("save")) {
    showSaveDialog.value = true;
  }
}

function getStatusColor(code) {
  if (code >= 200 && code < 300) return "#10b981";
  if (code >= 300 && code < 400) return "#f59e0b";
  if (code >= 400 && code < 500) return "#fb923c";
  return "#ef4444";
}
</script>

<style>
/* ====================================================
   AUTHENTIC DEVELOPER TOOL DESIGN TOKENS
   Grounded, tactile, purposeful — like VS Code & Postman
   ==================================================== */
:root,
[data-theme="dark"],
.v-theme--dark {
  --bg-app: #181818;
  --bg-sidebar: #212121;
  --bg-header: #212121;
  --bg-workspace-req: #1e1e1e;
  --bg-workspace-res: #181818;
  --bg-surface: #252526;
  --bg-surface-elevated: #2d2d2d;
  --bg-terminal: #141414;
  --bg-code-editor: #181818;
  --bg-input: #282828;
  --bg-omni: #252526;
  --bg-dialog: #252526;
  --bg-hover: #2f2f2f;
  --border-color: #333333;
  --border-color-subtle: #2b2b2b;
  --text-primary: #ededed;
  --text-secondary: #aaaaaa;
  --text-muted: #757575;
  --text-terminal: #e1e1e1;
  --text-code: #58a6ff;
  --primary: #ff6c37; /* Authentic developer action accent (Postman orange / clean energetic) */
  --primary-hover: #e05a28;
  --primary-bg: rgba(255, 108, 55, 0.12);
  --scrollbar-thumb: #3e3e3e;
  --scrollbar-track: #1e1e1e;
}

[data-theme="light"],
.v-theme--light {
  --bg-app: #f4f4f4;
  --bg-sidebar: #fcfcfc;
  --bg-header: #ffffff;
  --bg-workspace-req: #ffffff;
  --bg-workspace-res: #fafafa;
  --bg-surface: #ffffff;
  --bg-surface-elevated: #f0f0f0;
  --bg-terminal: #ffffff;
  --bg-code-editor: #ffffff;
  --bg-input: #ffffff;
  --bg-omni: #ffffff;
  --bg-dialog: #ffffff;
  --bg-hover: #f0f0f0;
  --border-color: #dcdcdc;
  --border-color-subtle: #e8e8e8;
  --text-primary: #1f1f1f;
  --text-secondary: #5f5f5f;
  --text-muted: #8c8c8c;
  --text-terminal: #24292f;
  --text-code: #0969da;
  --primary: #ff6c37;
  --primary-hover: #e05a28;
  --primary-bg: rgba(255, 108, 55, 0.1);
  --scrollbar-thumb: #c1c1c1;
  --scrollbar-track: #f1f1f1;
}

/* Strict Layout Reset */
html, body {
  margin: 0;
  padding: 0;
  height: 100vh;
  overflow: hidden !important;
  background-color: var(--bg-app);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  font-size: 13px;
}

.api-sentinel-app {
  background-color: var(--bg-app) !important;
  height: 100vh !important;
  overflow: hidden !important;
}

.sentinel-sidebar {
  background: var(--bg-sidebar) !important;
  border-right: 1px solid var(--border-color) !important;
}

.sentinel-viewport {
  height: 100vh !important;
  overflow: hidden !important;
  background: var(--bg-app);
}

.sentinel-viewport :deep(.v-main__wrap) {
  height: 100%;
  overflow: hidden;
}

/* Split Pane */
.studio-desktop-split {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.studio-pane {
  overflow: hidden;
}

.studio-request-pane {
  flex: 0 0 auto;
  max-height: 52%;
  background: var(--bg-workspace-req);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.studio-response-pane {
  flex: 1 1 0;
  min-height: 0;
  background: var(--bg-workspace-res);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.mobile-nav-toggle-bar {
  background: var(--bg-header);
  border-color: var(--border-color) !important;
}

.mobile-status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}

.toast-snackbar :deep(.v-snackbar__wrapper) {
  background: var(--bg-surface-elevated) !important;
  border: 1px solid var(--border-color);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  color: var(--text-primary);
}

/* Developer Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--scrollbar-track);
}

::-webkit-scrollbar-thumb {
  background: var(--scrollbar-thumb);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555555;
}

* {
  scrollbar-width: thin;
  scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
}
</style>
