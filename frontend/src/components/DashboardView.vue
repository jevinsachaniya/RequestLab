<template>
  <div class="dashboard-view pa-4 pa-md-6 h-100 overflow-y-auto">
    <!-- Top Workspace Overview Header -->
    <div class="dashboard-top-bar d-flex align-center justify-space-between flex-wrap gap-3 pb-4 mb-4 border-b">
      <div>
        <div class="d-flex align-center gap-2 mb-1">
          <h1 class="text-h6 font-weight-bold mb-0">Workspace Overview</h1>
          <span class="system-status-pill font-mono">
            <span class="status-dot"></span>
            Ready
          </span>
        </div>
        <p class="text-caption text-secondary mb-0">
          Real-time metrics, execution performance, and recent API runs.
        </p>
      </div>

      <div class="d-flex align-center gap-2">
        <button
          type="button"
          class="dev-primary-btn d-flex align-center px-3 py-1.5 text-caption font-weight-medium"
          @click="openNewRequestInWorkspace"
        >
          <v-icon size="15" class="mr-1.5">mdi-plus</v-icon>
          <span>New Request</span>
        </button>
      </div>
    </div>

    <!-- Guest Mode Callout Banner -->
    <div
      v-if="!isAuthenticated"
      class="guest-callout-panel pa-3 rounded border mb-4 d-flex align-center justify-space-between flex-wrap gap-3"
    >
      <div class="d-flex align-center">
        <v-icon size="20" color="primary" class="mr-3">mdi-shield-outline</v-icon>
        <div>
          <div class="font-weight-bold text-caption">Guest Sandbox Active</div>
          <div class="text-caption text-secondary">
            Requests run live without saving audit logs to cloud storage. Sign in to sync your collections and keep execution history.
          </div>
        </div>
      </div>
      <button
        type="button"
        class="dev-secondary-btn px-3 py-1 text-caption font-weight-medium"
        @click="emit('open-auth', 'Sign in to enable persistent metrics and cloud collections.')"
      >
        Sign In / Register
      </button>
    </div>

    <!-- Key Metrics Cards -->
    <v-row class="mb-4">
      <!-- 1. Collections -->
      <v-col cols="12" sm="6" md="3">
        <div class="metric-card pa-3 rounded border">
          <div class="d-flex align-center justify-space-between text-muted mb-2">
            <span class="metric-label">COLLECTIONS</span>
            <v-icon size="16">mdi-folder-multiple-outline</v-icon>
          </div>
          <div class="metric-value font-mono font-weight-bold mb-1">
            {{ store.collections.length }}
          </div>
          <div class="metric-subtext text-secondary">
            Organized workspace folders
          </div>
        </div>
      </v-col>

      <!-- 2. Saved Endpoints -->
      <v-col cols="12" sm="6" md="3">
        <div class="metric-card pa-3 rounded border">
          <div class="d-flex align-center justify-space-between text-muted mb-2">
            <span class="metric-label">SAVED ENDPOINTS</span>
            <v-icon size="16">mdi-code-tags</v-icon>
          </div>
          <div class="metric-value font-mono font-weight-bold mb-1">
            {{ totalSavedRequestsCount }}
          </div>
          <div class="metric-subtext text-secondary">
            Pre-configured API requests
          </div>
        </div>
      </v-col>

      <!-- 3. Total Executions -->
      <v-col cols="12" sm="6" md="3">
        <div class="metric-card pa-3 rounded border">
          <div class="d-flex align-center justify-space-between text-muted mb-2">
            <span class="metric-label">TOTAL EXECUTIONS</span>
            <v-icon size="16">mdi-play-circle-outline</v-icon>
          </div>
          <div class="metric-value font-mono font-weight-bold mb-1">
            {{ store.historyTotal }}
          </div>
          <div class="metric-subtext text-secondary">
            Dispatched API calls
          </div>
        </div>
      </v-col>

      <!-- 4. Test Pass Rate -->
      <v-col cols="12" sm="6" md="3">
        <div class="metric-card pa-3 rounded border">
          <div class="d-flex align-center justify-space-between text-muted mb-2">
            <span class="metric-label">TEST PASS RATE</span>
            <v-icon size="16">mdi-check-decagram-outline</v-icon>
          </div>
          <div class="metric-value font-mono font-weight-bold mb-1" :style="{ color: testPassRate === 100 ? '#10b981' : testPassRate > 50 ? '#f59e0b' : '#ef4444' }">
            {{ testPassRate }}%
          </div>
          <div class="metric-subtext text-secondary">
            Assertion verification rate
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Recent Executions Section -->
    <div class="recent-section rounded border">
      <div class="section-top px-3 py-2.5 d-flex align-center justify-space-between border-b flex-wrap gap-2">
        <div class="d-flex align-center gap-2">
          <v-icon size="16" class="text-secondary">mdi-clock-outline</v-icon>
          <span class="font-weight-bold text-caption">Recent Execution Traces</span>
        </div>
        <button
          v-if="isAuthenticated && store.history.length > 0"
          type="button"
          class="text-link-btn text-caption font-weight-medium d-flex align-center"
          @click="store.activeView = 'history'"
        >
          <span>View all in History</span>
          <v-icon size="13" class="ml-1">mdi-arrow-right</v-icon>
        </button>
      </div>

      <!-- Executions Table -->
      <div v-if="isAuthenticated && store.history.length > 0" class="executions-table-wrap">
        <table class="dev-table w-100">
          <thead>
            <tr>
              <th style="width: 80px;">METHOD</th>
              <th>ENDPOINT URL</th>
              <th style="width: 100px;">STATUS</th>
              <th style="width: 100px;">LATENCY</th>
              <th style="width: 100px;" class="d-none d-sm-table-cell">TIME</th>
              <th style="width: 80px; text-align: right;">ACTION</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in store.history.slice(0, 8)"
              :key="item.id"
              class="table-row"
            >
              <td>
                <span :class="['dev-method-badge font-mono', item.method.toLowerCase()]">
                  {{ item.method }}
                </span>
              </td>
              <td>
                <span class="endpoint-url font-mono text-truncate d-block" :title="item.url">
                  {{ item.url }}
                </span>
              </td>
              <td>
                <span :class="['status-code-tag font-mono', getStatusClass(item.status_code)]">
                  {{ item.status_code }}
                </span>
              </td>
              <td>
                <span class="font-mono text-caption text-secondary">
                  {{ item.response_time_ms ? `${item.response_time_ms} ms` : '—' }}
                </span>
              </td>
              <td class="d-none d-sm-table-cell">
                <span class="text-caption text-muted font-mono">
                  {{ formatDate(item.created_at) }}
                </span>
              </td>
              <td style="text-align: right;">
                <button
                  type="button"
                  class="table-action-btn font-weight-medium text-caption px-2 py-0.5"
                  @click="loadHistoryIntoWorkspace(item)"
                >
                  Load
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty State -->
      <div v-else class="text-center pa-6 text-secondary">
        <v-icon size="28" color="grey" class="mb-2">mdi-history</v-icon>
        <div class="text-caption font-weight-bold mb-1">
          No execution traces recorded
        </div>
        <div class="text-caption text-muted mb-3" style="max-width: 360px; margin: 0 auto;">
          {{ isAuthenticated ? 'Execute a request in the workspace studio to monitor latency, response headers, and assertions.' : 'Sign in to record execution traces and persist audit logs.' }}
        </div>
        <button
          type="button"
          class="dev-primary-btn px-3 py-1 text-caption font-weight-medium d-inline-flex align-center"
          @click="openNewRequestInWorkspace"
        >
          <v-icon size="14" class="mr-1">mdi-play</v-icon>
          <span>Send First Request</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, defineEmits } from "vue";
import { store, isAuthenticated, resetCurrentRequest, showToast } from "@/stores/appState";

const emit = defineEmits(["open-auth"]);

const totalSavedRequestsCount = computed(() => {
  return store.collections.reduce((acc, col) => acc + (col.requests?.length || 0), 0);
});

const testPassRate = computed(() => {
  let totalTests = 0;
  let passedTests = 0;
  for (const item of store.history) {
    if (item.assertion_results && Array.isArray(item.assertion_results)) {
      for (const res of item.assertion_results) {
        totalTests++;
        if (res.passed) passedTests++;
      }
    }
  }
  if (totalTests === 0) return 100;
  return Math.round((passedTests / totalTests) * 100);
});

function openNewRequestInWorkspace() {
  resetCurrentRequest();
  store.activeView = "workspace";
}

function loadHistoryIntoWorkspace(item) {
  store.currentRequest.id = null;
  store.currentRequest.name = `History (${item.method} ${new URL(item.url).pathname})`;
  store.currentRequest.method = item.method;
  store.currentRequest.url = item.url;
  store.currentRequest.body = item.request_body || "";
  store.currentRequest.assertions = item.assertions || [];

  const hList = [];
  if (item.request_headers && typeof item.request_headers === "object") {
    for (const [k, v] of Object.entries(item.request_headers)) {
      hList.push({ key: k, value: String(v), enabled: true });
    }
  }
  if (hList.length === 0) hList.push({ key: "Accept", value: "application/json", enabled: true });
  store.currentRequest.headersList = hList;

  store.lastResponse = {
    status_code: item.status_code,
    response_time_ms: item.response_time_ms,
    response_headers: item.response_headers || {},
    response_body: item.response_body || "",
    error_message: item.error_message,
    assertion_results: item.assertion_results || [],
  };

  store.activeView = "workspace";
  showToast("Request loaded into Studio", "info");
}

function getStatusClass(code) {
  if (code >= 200 && code < 300) return "status-2xx";
  if (code >= 300 && code < 400) return "status-3xx";
  if (code >= 400 && code < 500) return "status-4xx";
  return "status-5xx";
}

function formatDate(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
</script>

<style scoped>
.dashboard-view {
  background: var(--bg-app);
  color: var(--text-primary);
  font-size: 13px;
}

.dashboard-top-bar {
  border-color: var(--border-color) !important;
}

.system-status-pill {
  font-size: 10px;
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  padding: 1px 6px;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--text-secondary);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
}

/* Developer Buttons */
.dev-primary-btn {
  background: var(--primary);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.dev-primary-btn:hover {
  background: var(--primary-hover);
}

.dev-secondary-btn {
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dev-secondary-btn:hover {
  border-color: var(--primary);
}

.text-link-btn {
  background: transparent;
  border: none;
  color: var(--primary);
  cursor: pointer;
}

.text-link-btn:hover {
  text-decoration: underline;
}

/* Guest Callout */
.guest-callout-panel {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

/* Metric Cards */
.metric-card {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

.metric-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.metric-value {
  font-size: 22px;
  line-height: 1.1;
  color: var(--text-primary);
}

.metric-subtext {
  font-size: 11px;
}

/* Recent Executions Box */
.recent-section {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

.section-top {
  border-color: var(--border-color) !important;
}

/* Dev Table */
.executions-table-wrap {
  overflow-x: auto;
}

.dev-table {
  border-collapse: collapse;
  font-size: 12px;
}

.dev-table th {
  text-align: left;
  padding: 8px 12px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-surface);
}

.dev-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color-subtle);
  vertical-align: middle;
}

.table-row:hover {
  background: var(--bg-hover);
}

.endpoint-url {
  max-width: 420px;
  color: var(--text-primary);
  font-size: 12px;
}

/* Method Badges */
.dev-method-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: 3px;
  min-width: 34px;
  text-align: center;
  display: inline-block;
  line-height: 1.2;
}

.dev-method-badge.get { color: #10b981; background: rgba(16, 185, 129, 0.12); }
.dev-method-badge.post { color: #f59e0b; background: rgba(245, 158, 11, 0.12); }
.dev-method-badge.put { color: #3b82f6; background: rgba(59, 130, 246, 0.12); }
.dev-method-badge.patch { color: #8b5cf6; background: rgba(139, 92, 246, 0.12); }
.dev-method-badge.delete { color: #ef4444; background: rgba(239, 68, 68, 0.12); }

.status-code-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
}

.status-2xx { color: #10b981; background: rgba(16, 185, 129, 0.12); }
.status-3xx { color: #f59e0b; background: rgba(245, 158, 11, 0.12); }
.status-4xx { color: #f97316; background: rgba(249, 115, 22, 0.12); }
.status-5xx { color: #ef4444; background: rgba(239, 68, 68, 0.12); }

.table-action-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.table-action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--primary);
}

.font-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>
