<template>
  <div class="response-terminal pa-3 d-flex flex-column h-100" style="min-height: 0;">
    <!-- Terminal Header Bar (Postman Style) -->
    <div class="response-header-bar d-flex align-center justify-space-between mb-2 pb-1 border-b flex-wrap gap-2 flex-shrink-0">
      <!-- Left: Title -->
      <div class="d-flex align-center">
        <span class="response-title font-weight-bold text-caption text-uppercase">
          Response
        </span>
      </div>

      <!-- Right: Standard Postman Status Badges -->
      <div v-if="store.lastResponse" class="d-flex align-center flex-wrap gap-3 font-mono text-caption">
        <!-- Status Code -->
        <span v-if="store.lastResponse.status_code" class="d-flex align-center">
          <span class="text-grey mr-1">Status:</span>
          <span :class="['status-code-text font-weight-bold', getStatusClass(store.lastResponse.status_code)]">
            {{ store.lastResponse.status_code }} {{ getStatusText(store.lastResponse.status_code) }}
          </span>
        </span>

        <!-- Latency -->
        <span v-if="store.lastResponse.response_time_ms !== undefined" class="d-flex align-center">
          <span class="text-grey mr-1">Time:</span>
          <span class="text-white">{{ store.lastResponse.response_time_ms }} ms</span>
        </span>

        <!-- Size -->
        <span class="d-flex align-center">
          <span class="text-grey mr-1">Size:</span>
          <span class="text-white">{{ formattedResponseSize }}</span>
        </span>

        <!-- Test Results Summary -->
        <span v-if="store.lastResponse.assertion_results?.length" class="d-flex align-center">
          <span class="text-grey mr-1">Tests:</span>
          <span :class="['font-weight-bold', allAssertionsPassed ? 'text-green' : 'text-red']">
            {{ passedAssertionsCount }}/{{ store.lastResponse.assertion_results.length }} passed
          </span>
        </span>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="!store.lastResponse && !store.isSendingRequest"
      class="flex-grow-1 d-flex flex-column align-center justify-center text-grey pa-4 text-center"
      style="min-height: 0;"
    >
      <div class="text-caption font-weight-medium mb-1">Enter a URL and click <strong>Send</strong> to get a response</div>
      <div class="text-caption text-muted">Awaiting request execution...</div>
    </div>

    <!-- Loading State -->
    <div
      v-else-if="store.isSendingRequest"
      class="flex-grow-1 d-flex flex-column align-center justify-center text-grey pa-4"
      style="min-height: 0;"
    >
      <v-progress-circular indeterminate color="primary" size="28" width="2" class="mb-2" />
      <div class="text-caption font-weight-medium">Sending request...</div>
    </div>

    <!-- Active Response Content -->
    <div v-else class="flex-grow-1 d-flex flex-column overflow-hidden" style="min-height: 0;">
      <!-- Error Message Banner -->
      <div v-if="store.lastResponse.error_message" class="error-banner pa-2 mb-2 rounded border flex-shrink-0">
        <div class="font-weight-bold text-caption text-red">
          <v-icon size="14" color="red" class="mr-1">mdi-alert-circle</v-icon>
          {{ store.lastResponse.error_message }}
        </div>
      </div>

      <!-- Response Tabs Navigation -->
      <div class="tab-bar border-b d-flex align-center justify-space-between mb-2 flex-shrink-0">
        <div class="response-tabs-scroll d-flex align-center h-100">
          <button
            type="button"
            :class="['tab-item', { active: responseTab === 'body' }]"
            @click="responseTab = 'body'"
          >
            Body
          </button>

          <button
            type="button"
            :class="['tab-item', { active: responseTab === 'headers' }]"
            @click="responseTab = 'headers'"
          >
            Headers <span v-if="headersCount > 0" class="badge-count ml-1">{{ headersCount }}</span>
          </button>

          <button
            type="button"
            :class="['tab-item', { active: responseTab === 'cookies' }]"
            @click="responseTab = 'cookies'"
          >
            Cookies <span v-if="parsedCookies.length > 0" class="badge-count ml-1">{{ parsedCookies.length }}</span>
          </button>

          <button
            type="button"
            :class="['tab-item', { active: responseTab === 'assertions' }]"
            @click="responseTab = 'assertions'"
          >
            Test Results
            <span
              v-if="store.lastResponse.assertion_results?.length"
              :class="['badge-count ml-1', allAssertionsPassed ? 'green' : 'red']"
            >
              {{ passedAssertionsCount }}/{{ store.lastResponse.assertion_results.length }}
            </span>
          </button>
        </div>

        <!-- Right: Actions for active tab (Pretty / Raw / Copy) -->
        <div v-if="responseTab === 'body'" class="d-flex align-center gap-2 flex-shrink-0 ml-2">
          <div class="d-flex align-center mode-toggle-group">
            <button
              type="button"
              :class="['mode-btn text-caption', { active: bodyMode === 'pretty' }]"
              @click="bodyMode = 'pretty'"
            >
              Pretty
            </button>
            <button
              type="button"
              :class="['mode-btn text-caption', { active: bodyMode === 'raw' }]"
              @click="bodyMode = 'raw'"
            >
              Raw
            </button>
          </div>

          <button
            type="button"
            class="text-btn text-caption font-weight-medium d-flex align-center"
            title="Copy to Clipboard"
            @click="copyBody"
          >
            <v-icon size="13" class="mr-1">{{ copied ? 'mdi-check' : 'mdi-content-copy' }}</v-icon>
            <span>{{ copied ? 'Copied' : 'Copy' }}</span>
          </button>
        </div>
      </div>

      <!-- Tab Content Area -->
      <div class="flex-grow-1 overflow-hidden" style="min-height: 0;">
        <!-- 1. Body View -->
        <div
          v-if="responseTab === 'body'"
          class="code-container h-100 pa-2 rounded border font-mono"
        >
          <pre class="code-pre">{{ bodyMode === 'pretty' ? prettyFormattedBody : (store.lastResponse.response_body || "(empty response)") }}</pre>
        </div>

        <!-- 2. Response Headers -->
        <div
          v-else-if="responseTab === 'headers'"
          class="headers-table-wrap h-100 overflow-y-auto"
        >
          <table class="grid-table w-100 font-mono">
            <thead>
              <tr>
                <th style="width: 240px;">HEADER</th>
                <th>VALUE</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(val, key) in store.lastResponse.response_headers || {}"
                :key="key"
              >
                <td class="font-weight-medium px-2 py-1 text-primary">{{ key }}</td>
                <td class="px-2 py-1 text-break">{{ val }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!headersCount" class="text-caption text-grey pa-4 text-center">
            No response headers received.
          </div>
        </div>

        <!-- 3. Cookies -->
        <div
          v-else-if="responseTab === 'cookies'"
          class="h-100 overflow-y-auto"
        >
          <div v-if="parsedCookies.length === 0" class="text-caption text-grey pa-4 text-center">
            No cookies were sent by the server.
          </div>
          <table v-else class="grid-table w-100 font-mono">
            <thead>
              <tr>
                <th style="width: 180px;">NAME</th>
                <th>VALUE</th>
                <th>ATTRIBUTES</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(cookie, idx) in parsedCookies"
                :key="idx"
              >
                <td class="font-weight-medium px-2 py-1 text-primary">{{ cookie.name }}</td>
                <td class="px-2 py-1 text-break">{{ cookie.value }}</td>
                <td class="px-2 py-1 text-grey">{{ cookie.attributes || 'Session' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 4. Test Results / Assertions -->
        <div
          v-else-if="responseTab === 'assertions'"
          class="h-100 overflow-y-auto pa-1"
        >
          <div
            v-if="!store.lastResponse.assertion_results?.length"
            class="text-caption text-grey pa-4 text-center"
          >
            No tests were configured for this request.
          </div>
          <div v-else class="d-flex flex-column gap-2">
            <div
              v-for="(res, idx) in store.lastResponse.assertion_results"
              :key="idx"
              class="assertion-result-item pa-2.5 rounded border"
            >
              <div class="d-flex align-center justify-space-between mb-1">
                <div class="d-flex align-center flex-wrap gap-1">
                  <span :class="['result-badge mr-2 font-weight-bold', res.passed ? 'pass' : 'fail']">
                    {{ res.passed ? 'PASS' : 'FAIL' }}
                  </span>
                  <span class="font-weight-bold text-caption text-uppercase">
                    {{ getAssertionType(res) }}
                  </span>
                  <span v-if="getAssertionField(res)" class="text-caption text-secondary font-mono ml-1">
                    ({{ getAssertionField(res) }})
                  </span>
                </div>
              </div>

              <div class="d-flex align-center text-caption text-secondary gap-3 font-mono mt-1">
                <div>Expected: <span class="text-primary">{{ getAssertionExpected(res) }}</span> ({{ getAssertionOperator(res) }})</div>
                <div>Actual: <span class="text-primary">{{ res.actual !== undefined && res.actual !== null ? res.actual : 'null' }}</span></div>
              </div>

              <div v-if="getAssertionMessage(res)" class="mt-1 text-caption text-secondary">
                {{ getAssertionMessage(res) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { store, formatByteSize, getPayloadByteSize, parseResponseCookies, showToast } from "@/stores/appState";

const responseTab = ref("body");
const bodyMode = ref("pretty");
const copied = ref(false);

const headersCount = computed(() => {
  return Object.keys(store.lastResponse?.response_headers || {}).length;
});

const parsedCookies = computed(() => {
  return parseResponseCookies(store.lastResponse?.response_headers);
});

const formattedResponseSize = computed(() => {
  const body = store.lastResponse?.response_body;
  if (!body) return "0 B";
  return formatByteSize(getPayloadByteSize(body));
});

const prettyFormattedBody = computed(() => {
  const body = store.lastResponse?.response_body;
  if (!body) return "(empty response)";
  try {
    const parsed = JSON.parse(body);
    return JSON.stringify(parsed, null, 2);
  } catch {
    return body;
  }
});

const passedAssertionsCount = computed(() => {
  return (store.lastResponse?.assertion_results || []).filter((r) => r.passed).length;
});

const allAssertionsPassed = computed(() => {
  const results = store.lastResponse?.assertion_results || [];
  return results.length > 0 && results.every((r) => r.passed);
});

function copyBody() {
  const text = store.lastResponse?.response_body;
  if (!text) return;
  navigator.clipboard.writeText(text);
  copied.value = true;
  showToast("Response body copied to clipboard", "success");
  setTimeout(() => {
    copied.value = false;
  }, 2000);
}

function getStatusClass(code) {
  if (code >= 200 && code < 300) return "status-2xx";
  if (code >= 300 && code < 400) return "status-3xx";
  if (code >= 400 && code < 500) return "status-4xx";
  return "status-5xx";
}

function getStatusText(code) {
  const map = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    422: "Unprocessable Entity",
    500: "Internal Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
  };
  return map[code] || "";
}

function getAssertionType(res) {
  const t = res?.type || res?.rule?.type || "assertion";
  return String(t).replace(/_/g, " ");
}

function getAssertionOperator(res) {
  return res?.operator || res?.rule?.operator || "equals";
}

function getAssertionExpected(res) {
  if (res?.expected !== undefined) return res.expected;
  if (res?.rule?.expected !== undefined) return res.rule.expected;
  return "—";
}

function getAssertionField(res) {
  return res?.field_path || res?.rule?.field_path || res?.rule?.target || "";
}

function getAssertionMessage(res) {
  return res?.message || res?.error_message || "";
}
</script>

<style scoped>
.response-terminal {
  background: var(--bg-workspace-res);
}

.response-header-bar {
  border-color: var(--border-color) !important;
}

.response-title {
  color: var(--text-secondary);
  letter-spacing: 0.05em;
}

.status-code-text.status-2xx { color: #10b981; }
.status-code-text.status-3xx { color: #f59e0b; }
.status-code-text.status-4xx { color: #fb923c; }
.status-code-text.status-5xx { color: #ef4444; }

/* Tabs (Postman Underline) */
.tab-bar {
  border-color: var(--border-color) !important;
  height: 34px;
}

.response-tabs-scroll {
  overflow-x: auto;
  white-space: nowrap;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
  flex: 1 1 auto;
  min-width: 0;
}

.response-tabs-scroll::-webkit-scrollbar {
  display: none;
}

.tab-item {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0 10px;
  height: 100%;
  cursor: pointer;
  white-space: nowrap !important;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
}

.tab-item:hover {
  color: var(--text-primary);
}

.tab-item.active {
  color: var(--text-primary);
  font-weight: 600;
  border-bottom: 2px solid var(--primary);
}

.badge-count {
  font-size: 0.65rem;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  padding: 0 5px;
  border-radius: 9px;
  color: var(--text-secondary);
}

.badge-count.green { color: #10b981; }
.badge-count.red { color: #ef4444; }

.mode-toggle-group {
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.mode-btn {
  background: transparent;
  border: none;
  padding: 2px 8px;
  font-size: 0.74rem;
  color: var(--text-secondary);
  cursor: pointer;
}

.mode-btn.active {
  background: var(--bg-hover);
  color: var(--text-primary);
  font-weight: 600;
}

.text-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
}

.text-btn:hover {
  color: var(--text-primary);
}

.code-container {
  background: var(--bg-terminal);
  border-color: var(--border-color) !important;
  height: 100%;
  overflow-y: auto !important;
  overflow-x: auto !important;
}

.code-pre {
  margin: 0;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--text-terminal);
  white-space: pre-wrap;
  word-break: break-word;
}

.headers-table-wrap {
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.grid-table {
  border-collapse: collapse;
  font-size: 0.78rem;
}

.grid-table th {
  background: var(--bg-surface-elevated);
  border-bottom: 1px solid var(--border-color);
  padding: 4px 8px;
  font-size: 0.7rem;
  color: var(--text-secondary);
  text-align: left;
}

.grid-table td {
  border-bottom: 1px solid var(--border-color-subtle);
}

.assertion-result-item {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

.result-badge {
  font-size: 0.65rem;
  padding: 1px 5px;
  border-radius: 3px;
}

.result-badge.pass { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.result-badge.fail { background: rgba(239, 68, 68, 0.15); color: #ef4444; }

.error-banner {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.25) !important;
}

.font-mono {
  font-family: Consolas, "Courier New", monospace;
}
</style>
