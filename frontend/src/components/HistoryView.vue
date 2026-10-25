<template>
  <div class="history-view pa-4 pa-md-6 h-100 overflow-y-auto">
    <!-- Header -->
    <div class="d-flex align-center justify-space-between pb-3 mb-3 border-b flex-wrap gap-2">
      <div>
        <div class="d-flex align-center gap-2 mb-1">
          <v-icon size="18" color="primary">mdi-history</v-icon>
          <h1 class="text-subtitle-1 font-weight-bold mb-0">Execution History & Audit Trail</h1>
        </div>
        <p class="text-caption text-secondary mb-0">
          Inspect dispatched API requests, execution durations, response payloads, and assertion results.
        </p>
      </div>

      <div class="d-flex align-center gap-2">
        <button
          type="button"
          class="dev-icon-btn"
          title="Refresh history"
          :disabled="store.isLoadingHistory"
          @click="fetchHistoryData"
        >
          <v-progress-circular
            v-if="store.isLoadingHistory"
            indeterminate
            size="14"
            width="2"
            color="primary"
          />
          <v-icon v-else size="15">mdi-refresh</v-icon>
        </button>
      </div>
    </div>

    <!-- Guest Mode Callout -->
    <div
      v-if="!isAuthenticated"
      class="guest-callout-panel pa-3 rounded border mb-3 d-flex align-center justify-space-between flex-wrap gap-3"
    >
      <div class="d-flex align-center">
        <v-icon size="20" color="primary" class="mr-3">mdi-cloud-outline</v-icon>
        <div>
          <div class="font-weight-bold text-caption">Guest History Notice</div>
          <div class="text-caption text-secondary">
            In guest mode, executions are performed in live sandbox and are not saved to the database. Sign in to record your audit trail across sessions.
          </div>
        </div>
      </div>
      <button
        type="button"
        class="dev-primary-btn px-3 py-1 text-caption font-weight-medium"
        @click="emit('open-auth', 'Sign in to access your persistent execution history.')"
      >
        Sign In to Enable
      </button>
    </div>

    <!-- Filter Bar -->
    <div class="history-filter-bar pa-2 rounded border mb-3 d-flex align-center flex-wrap gap-2">
      <!-- Search URL Filter -->
      <div class="search-input-wrap d-flex align-center flex-grow-1 px-2" style="min-width: 220px;">
        <v-icon size="15" class="text-muted mr-1.5">mdi-magnify</v-icon>
        <input
          v-model="urlFilter"
          type="text"
          placeholder="Filter by URL or path..."
          class="dev-filter-input font-mono"
        />
        <button
          v-if="urlFilter"
          type="button"
          class="clear-btn"
          @click="urlFilter = ''"
        >
          <v-icon size="13">mdi-close</v-icon>
        </button>
      </div>

      <!-- Method Filter -->
      <select v-model="selectedMethod" class="dev-filter-select">
        <option value="ALL">All Methods</option>
        <option value="GET">GET</option>
        <option value="POST">POST</option>
        <option value="PUT">PUT</option>
        <option value="PATCH">PATCH</option>
        <option value="DELETE">DELETE</option>
      </select>

      <!-- Status Code Filter -->
      <select
        v-model="selectedStatusCode"
        class="dev-filter-select"
        @change="fetchHistoryData"
      >
        <option :value="null">All Statuses</option>
        <option :value="200">200 OK</option>
        <option :value="201">201 Created</option>
        <option :value="400">400 Bad Request</option>
        <option :value="401">401 Unauthorized</option>
        <option :value="403">403 Forbidden</option>
        <option :value="404">404 Not Found</option>
        <option :value="500">500 Server Error</option>
      </select>
    </div>

    <!-- History Data Table Container -->
    <div class="history-table-card rounded border">
      <div v-if="filteredHistory.length === 0" class="text-center pa-6 text-secondary">
        <v-icon size="28" color="grey" class="mb-2">mdi-database-search-outline</v-icon>
        <div class="text-caption font-weight-bold mb-1">No execution records found</div>
        <div class="text-caption text-muted">
          {{ isAuthenticated ? 'Try adjusting your filters or execute requests in the workspace studio.' : 'Sign in to record execution history.' }}
        </div>
      </div>

      <div v-else class="table-wrap">
        <table class="dev-table w-100">
          <thead>
            <tr>
              <th style="width: 80px;">METHOD</th>
              <th>ENDPOINT URL</th>
              <th style="width: 90px;">STATUS</th>
              <th style="width: 90px;">LATENCY</th>
              <th style="width: 90px;">TESTS</th>
              <th style="width: 140px;">TIMESTAMP</th>
              <th style="width: 100px; text-align: right;">ACTIONS</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in filteredHistory"
              :key="item.id"
              class="table-row"
            >
              <td>
                <span :class="['dev-method-badge font-mono', item.method.toLowerCase()]">
                  {{ item.method }}
                </span>
              </td>

              <td>
                <span class="url-text font-mono text-truncate d-block" :title="item.url">
                  {{ item.url }}
                </span>
              </td>

              <td>
                <span :class="['status-code-tag font-mono', getStatusClass(item.status_code)]">
                  {{ item.status_code }}
                </span>
              </td>

              <td>
                <span class="text-caption text-secondary font-mono">
                  {{ item.response_time_ms ? `${item.response_time_ms} ms` : '—' }}
                </span>
              </td>

              <td>
                <span
                  v-if="item.assertion_results?.length"
                  :class="['assertion-pill font-mono', areAllPassed(item.assertion_results) ? 'pass' : 'fail']"
                >
                  {{ getPassedCount(item.assertion_results) }}/{{ item.assertion_results.length }}
                </span>
                <span v-else class="text-caption text-muted">—</span>
              </td>

              <td>
                <span class="text-caption text-muted font-mono">
                  {{ formatDateTime(item.created_at) }}
                </span>
              </td>

              <td style="text-align: right;">
                <div class="d-flex align-center justify-end gap-1">
                  <button
                    type="button"
                    class="action-btn-small"
                    title="Load into Studio Workspace"
                    @click="openInWorkspace(item)"
                  >
                    Load
                  </button>
                  <button
                    type="button"
                    class="action-icon-small"
                    title="Delete record"
                    @click="deleteRecord(item.id)"
                  >
                    <v-icon size="13">mdi-delete-outline</v-icon>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Footer -->
      <div v-if="store.historyTotal > 0" class="table-footer px-3 py-2 border-t d-flex align-center justify-space-between flex-wrap gap-2">
        <div class="text-caption text-muted font-mono">
          Showing {{ store.history.length }} of {{ store.historyTotal }} records
        </div>
        <div class="d-flex align-center gap-1">
          <button
            type="button"
            class="page-nav-btn text-caption"
            :disabled="currentPage <= 1"
            @click="changePage(currentPage - 1)"
          >
            Prev
          </button>
          <span class="page-current font-mono text-caption px-2">Page {{ currentPage }}</span>
          <button
            type="button"
            class="page-nav-btn text-caption"
            :disabled="currentPage * 20 >= store.historyTotal"
            @click="changePage(currentPage + 1)"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineEmits, onMounted } from "vue";
import { store, isAuthenticated, loadHistory, showToast } from "@/stores/appState";
import { api } from "@/api/client";

const emit = defineEmits(["open-auth"]);

const urlFilter = ref("");
const selectedMethod = ref("ALL");
const selectedStatusCode = ref(null);
const currentPage = ref(1);

onMounted(() => {
  if (isAuthenticated.value) {
    fetchHistoryData();
  }
});

function fetchHistoryData() {
  if (!isAuthenticated.value) return;
  loadHistory(currentPage.value, selectedStatusCode.value);
}

function changePage(page) {
  currentPage.value = page;
  fetchHistoryData();
}

const filteredHistory = computed(() => {
  return store.history.filter((item) => {
    if (selectedMethod.value !== "ALL" && item.method.toUpperCase() !== selectedMethod.value) {
      return false;
    }
    if (urlFilter.value && !item.url.toLowerCase().includes(urlFilter.value.toLowerCase())) {
      return false;
    }
    return true;
  });
});

async function deleteRecord(id) {
  try {
    await api.deleteHistoryItem(id);
    showToast("Execution record deleted", "info");
    store.history = store.history.filter((h) => h.id !== id);
    store.historyTotal = Math.max(0, store.historyTotal - 1);
  } catch (err) {
    showToast("Failed to delete execution record", "error");
  }
}

function openInWorkspace(item) {
  store.currentRequest.id = null;
  store.currentRequest.name = `History (${item.method} ${item.url})`;
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
  showToast("Loaded execution into workspace", "info");
}

function areAllPassed(results) {
  return results && results.length > 0 && results.every((r) => r.passed);
}

function getPassedCount(results) {
  return (results || []).filter((r) => r.passed).length;
}

function getStatusClass(code) {
  if (code >= 200 && code < 300) return "status-2xx";
  if (code >= 300 && code < 400) return "status-3xx";
  if (code >= 400 && code < 500) return "status-4xx";
  return "status-5xx";
}

function formatDateTime(isoStr) {
  if (!isoStr) return "";
  const d = new Date(isoStr);
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}
</script>

<style scoped>
.history-view {
  background: var(--bg-app);
  color: var(--text-primary);
  font-size: 13px;
}

.dev-icon-btn {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  width: 28px;
  height: 28px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.dev-icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--primary);
}

.dev-primary-btn {
  background: var(--primary);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.dev-primary-btn:hover {
  background: var(--primary-hover);
}

.guest-callout-panel {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

/* Filter Bar */
.history-filter-bar {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

.search-input-wrap {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  height: 30px;
}

.dev-filter-input {
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 12px;
  outline: none;
  width: 100%;
}

.clear-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
}

.dev-filter-select {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  height: 30px;
  padding: 0 8px;
  font-size: 12px;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
}

.dev-filter-select:focus {
  border-color: var(--primary);
}

/* Table */
.history-table-card {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

.table-wrap {
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
  background: var(--bg-surface-elevated);
}

.dev-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color-subtle);
  vertical-align: middle;
}

.table-row:hover {
  background: var(--bg-hover);
}

.url-text {
  max-width: 380px;
  color: var(--text-primary);
  font-size: 12px;
}

/* Badges */
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

.assertion-pill {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
}

.assertion-pill.pass { color: #10b981; background: rgba(16, 185, 129, 0.12); }
.assertion-pill.fail { color: #ef4444; background: rgba(239, 68, 68, 0.12); }

.action-btn-small {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: 3px;
  padding: 2px 7px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn-small:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--primary);
}

.action-icon-small {
  background: transparent;
  border: none;
  color: var(--text-muted);
  width: 22px;
  height: 22px;
  border-radius: 3px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-icon-small:hover {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

/* Pagination */
.table-footer {
  border-color: var(--border-color) !important;
  background: var(--bg-surface-elevated);
}

.page-nav-btn {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 2px 8px;
  border-radius: 3px;
  cursor: pointer;
}

.page-nav-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.page-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.font-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>
