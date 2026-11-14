<template>
  <div class="response-terminal d-flex flex-column h-100" style="min-height: 0;">
    <!-- Top Response Bar: Tabs on Left + Status Metrics on Right (Postman Style) -->
    <div class="response-tabs-bar d-flex align-center justify-space-between px-2 px-sm-3 border-b flex-shrink-0">
      <!-- Left: Navigation Tabs (Desktop / Tablet) -->
      <div class="d-none d-sm-flex align-center h-100 response-tabs-scroll">
        <button
          type="button"
          :class="['tab-item', { active: responseTab === 'body' }]"
          @click="responseTab = 'body'"
        >
          Body
        </button>

        <button
          type="button"
          :class="['tab-item', { active: responseTab === 'cookies' }]"
          @click="responseTab = 'cookies'"
        >
          Cookies
          <span v-if="parsedCookies.length > 0" class="tab-badge ml-1.5">{{ parsedCookies.length }}</span>
        </button>

        <button
          type="button"
          :class="['tab-item', { active: responseTab === 'headers' }]"
          @click="responseTab = 'headers'"
        >
          Headers
          <span v-if="headersCount > 0" class="tab-badge ml-1.5">{{ headersCount }}</span>
        </button>

        <button
          type="button"
          :class="['tab-item', { active: responseTab === 'assertions' }]"
          @click="responseTab = 'assertions'"
        >
          Test Results
          <span
            v-if="store.lastResponse?.assertion_results?.length"
            :class="['tab-badge ml-1.5', allAssertionsPassed ? 'green' : 'red']"
          >
            {{ passedAssertionsCount }}/{{ store.lastResponse.assertion_results.length }}
          </span>
        </button>
      </div>

      <!-- Left: Navigation Select (Mobile Only) -->
      <div class="d-flex d-sm-none align-center mr-2">
        <select v-model="responseTab" class="mobile-tab-select font-weight-medium">
          <option value="body">Body</option>
          <option value="cookies">Cookies {{ parsedCookies.length > 0 ? `(${parsedCookies.length})` : '' }}</option>
          <option value="headers">Headers {{ headersCount > 0 ? `(${headersCount})` : '' }}</option>
          <option value="assertions">Test Results {{ store.lastResponse?.assertion_results?.length ? `(${passedAssertionsCount}/${store.lastResponse.assertion_results.length})` : '' }}</option>
        </select>
      </div>

      <!-- Right: Postman Status & Timing Line -->
      <div v-if="store.lastResponse" class="response-meta-line d-flex align-center font-mono text-caption flex-shrink-0 ml-1 ml-sm-3">
        <!-- Status Code -->
        <span v-if="store.lastResponse.status_code" class="d-flex align-center">
          <span :class="['status-text font-weight-bold', getStatusClass(store.lastResponse.status_code)]">
            {{ store.lastResponse.status_code }} <span class="d-none d-md-inline">{{ getStatusText(store.lastResponse.status_code) }}</span>
          </span>
        </span>

        <span class="meta-separator mx-1.5 mx-sm-2">•</span>

        <!-- Latency -->
        <span v-if="store.lastResponse.response_time_ms !== undefined" class="meta-item">
          {{ store.lastResponse.response_time_ms }} ms
        </span>

        <span class="meta-separator mx-1.5 mx-sm-2">•</span>

        <!-- Size -->
        <span class="meta-item">
          {{ formattedResponseSize }}
        </span>

        <!-- Test summary if present -->
        <template v-if="store.lastResponse.assertion_results?.length">
          <span class="meta-separator mx-1.5 mx-sm-2 d-none d-md-inline">•</span>
          <span :class="['font-weight-medium d-none d-md-inline', allAssertionsPassed ? 'text-green' : 'text-red']">
            {{ passedAssertionsCount }}/{{ store.lastResponse.assertion_results.length }} passed
          </span>
        </template>
      </div>
    </div>

    <!-- Secondary Toolbar (Mode & Actions: JSON / Raw / Preview / Copy / Search) -->
    <div v-if="store.lastResponse && responseTab === 'body'" class="response-subtoolbar px-3 py-1 d-flex align-center justify-space-between border-b flex-shrink-0">
      <!-- Left: Format Selectors -->
      <div class="d-flex align-center gap-1">
        <button
          type="button"
          :class="['subtool-btn font-mono font-weight-medium d-flex align-center', { active: bodyMode === 'pretty' }]"
          @click="bodyMode = 'pretty'"
        >
          <span class="mr-1">{ }</span>
          <span>JSON</span>
          <v-icon size="12" class="ml-1 text-muted">mdi-chevron-down</v-icon>
        </button>

        <button
          type="button"
          :class="['subtool-btn text-caption', { active: bodyMode === 'raw' }]"
          @click="bodyMode = 'raw'"
        >
          Raw
        </button>
      </div>

      <!-- Right: Utility Actions (Word Wrap, Search, Copy) -->
      <div class="d-flex align-center gap-2">
        <button
          type="button"
          :class="['icon-tool-btn', { active: wrapLines }]"
          :title="wrapLines ? 'Disable line wrap' : 'Enable line wrap'"
          @click="wrapLines = !wrapLines"
        >
          <v-icon size="14">mdi-wrap</v-icon>
        </button>

        <button
          type="button"
          class="icon-tool-btn"
          title="Search in response"
          @click="toggleSearch"
        >
          <v-icon size="14">mdi-magnify</v-icon>
        </button>

        <button
          type="button"
          class="icon-tool-btn"
          title="Copy response body"
          @click="copyBody"
        >
          <v-icon size="14">{{ copied ? 'mdi-check' : 'mdi-content-copy' }}</v-icon>
          <span v-if="copied" class="text-caption ml-1 text-green">Copied</span>
        </button>
      </div>
    </div>

    <!-- In-Response Search Filter Bar -->
    <div v-if="showSearch" class="response-search-bar px-3 py-1 border-b d-flex align-center flex-shrink-0">
      <v-icon size="14" class="text-muted mr-2">mdi-magnify</v-icon>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="Find in response..."
        class="search-input font-mono flex-grow-1"
        @keydown.esc="showSearch = false"
      />
      <button type="button" class="icon-tool-btn" @click="showSearch = false">
        <v-icon size="14">mdi-close</v-icon>
      </button>
    </div>

    <!-- Empty State Experience -->
    <div
      v-if="!store.lastResponse && !store.isSendingRequest"
      class="empty-state-wrap flex-grow-1 d-flex flex-column align-center justify-center pa-4 text-center user-select-none"
      style="min-height: 0;"
    >
      <div class="empty-icon-halo mb-3 d-flex align-center justify-center">
        <svg viewBox="0 0 64 64" fill="none" class="empty-svg">
          <path
            d="M26 14 H38 M28 14 V26 L16 50 C14 53 17 56 21 56 H43 C47 56 50 53 48 50 L36 26 V14"
            stroke="currentColor"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="flask-stroke"
          />
          <polygon points="41,36 21,46 28,42" fill="#38bdf8"/>
          <polygon points="41,36 28,42 32,50" fill="#0b5fff"/>
        </svg>
      </div>
      <h3 class="empty-heading mb-1 font-weight-bold">Ready to Test Your API</h3>
      <p class="empty-subtext mb-3 text-caption text-secondary">
        Enter a request URL above and click <strong>Send</strong>, or press
        <kbd class="shortcut-pill">Ctrl</kbd> + <kbd class="shortcut-pill">Enter</kbd>
      </p>
      <div class="empty-feature-chips d-flex align-center flex-wrap justify-center gap-2">
        <span class="feature-chip"><v-icon size="11" class="mr-1 text-primary">mdi-lightning-bolt</v-icon>High-Speed Engine</span>
        <span class="feature-chip"><v-icon size="11" class="mr-1 text-info">mdi-shield-check</v-icon>SSRF Shield</span>
        <span class="feature-chip"><v-icon size="11" class="mr-1 text-secondary">mdi-check-all</v-icon>Automated Tests</span>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-else-if="store.isSendingRequest"
      class="flex-grow-1 d-flex flex-column align-center justify-center text-grey pa-4"
      style="min-height: 0;"
    >
      <v-progress-circular indeterminate color="primary" size="30" width="2.5" class="mb-2" />
      <div class="text-caption font-weight-medium">Sending request to server...</div>
    </div>

    <!-- Active Response Content Area -->
    <div v-else class="flex-grow-1 d-flex flex-column overflow-hidden" style="min-height: 0;">
      <!-- Error Message Banner -->
      <div v-if="store.lastResponse.error_message" class="error-banner pa-2 mx-3 my-2 rounded border flex-shrink-0">
        <div class="font-weight-bold text-caption text-red d-flex align-center">
          <v-icon size="14" color="red" class="mr-1.5">mdi-alert-circle</v-icon>
          <span>{{ store.lastResponse.error_message }}</span>
        </div>
      </div>

      <!-- Tab Content Area -->
      <div class="flex-grow-1 overflow-hidden" style="min-height: 0;">
        <!-- 1. Postman Code Editor View with Line Numbers & Tree Indent Guides -->
        <div
          v-if="responseTab === 'body'"
          class="code-editor-viewport h-100 font-mono overflow-auto"
        >
          <div class="editor-lines-container">
            <div
              v-for="(lineHtml, idx) in filteredLines"
              :key="idx"
              class="editor-row d-flex"
            >
              <!-- Line Number Column -->
              <span class="line-number user-select-none">{{ idx + 1 }}</span>
              <!-- Code Line with Indent Guide and Postman Syntax Colors -->
              <span :class="['line-content', { 'wrap-enabled': wrapLines }]" v-html="lineHtml"></span>
            </div>
            <div v-if="filteredLines.length === 0" class="pa-3 text-grey text-caption">
              {{ searchQuery ? 'No matching lines found.' : '(empty response body)' }}
            </div>
          </div>
        </div>

        <!-- 2. Response Headers Table -->
        <div
          v-else-if="responseTab === 'headers'"
          class="headers-table-wrap h-100 overflow-y-auto px-3 py-2"
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
                class="table-row-hover"
              >
                <td class="font-weight-medium px-3 py-1.5 text-code">{{ key }}</td>
                <td class="px-3 py-1.5 text-break">{{ val }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!headersCount" class="text-caption text-grey pa-4 text-center">
            No response headers received.
          </div>
        </div>

        <!-- 3. Cookies Table -->
        <div
          v-else-if="responseTab === 'cookies'"
          class="headers-table-wrap h-100 overflow-y-auto px-3 py-2"
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
                class="table-row-hover"
              >
                <td class="font-weight-medium px-3 py-1.5 text-code">{{ cookie.name }}</td>
                <td class="px-3 py-1.5 text-break">{{ cookie.value }}</td>
                <td class="px-3 py-1.5 text-muted">{{ cookie.attributes || 'Session' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 4. Test Results / Assertions -->
        <div
          v-else-if="responseTab === 'assertions'"
          class="h-100 overflow-y-auto px-3 py-2"
        >
          <div
            v-if="!store.lastResponse.assertion_results?.length"
            class="text-caption text-grey pa-4 text-center border rounded"
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
                <div>Expected: <span class="text-primary font-weight-medium">{{ getAssertionExpected(res) }}</span> ({{ getAssertionOperator(res) }})</div>
                <div>Actual: <span class="text-primary font-weight-medium">{{ res.actual !== undefined && res.actual !== null ? res.actual : 'null' }}</span></div>
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
const wrapLines = ref(false);
const showSearch = ref(false);
const searchQuery = ref("");
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

// Postman-Grade JSON Syntax Highlighting
function highlightJson(jsonStr) {
  if (!jsonStr) return "";
  const safe = jsonStr
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return safe.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\\-]?\d+)?)/g,
    (match) => {
      let cls = "json-number";
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = "json-key";
        } else {
          cls = "json-string";
        }
      } else if (/true|false/.test(match)) {
        cls = "json-boolean";
      } else if (/null/.test(match)) {
        cls = "json-null";
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

// Split body into formatted lines
const formattedLines = computed(() => {
  const content = bodyMode.value === "pretty" ? prettyFormattedBody.value : (store.lastResponse?.response_body || "(empty response)");
  if (!content) return [];
  const lines = content.split("\n");
  if (bodyMode.value === "pretty") {
    return lines.map((l) => highlightJson(l));
  }
  return lines.map((l) => l.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"));
});

// Search filter
const filteredLines = computed(() => {
  if (!searchQuery.value.trim()) return formattedLines.value;
  const q = searchQuery.value.toLowerCase();
  return formattedLines.value.filter((l) => l.toLowerCase().includes(q));
});

const passedAssertionsCount = computed(() => {
  return (store.lastResponse?.assertion_results || []).filter((r) => r.passed).length;
});

const allAssertionsPassed = computed(() => {
  const results = store.lastResponse?.assertion_results || [];
  return results.length > 0 && results.every((r) => r.passed);
});

function toggleSearch() {
  showSearch.value = !showSearch.value;
}

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
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    422: "Unprocessable",
    429: "Too Many Requests",
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

/* Postman Top Response Bar */
.response-tabs-bar {
  background: var(--bg-workspace-res);
  border-color: var(--border-color) !important;
  height: 38px;
}

.response-tabs-scroll {
  overflow-x: auto;
  white-space: nowrap;
  scrollbar-width: none;
}

.response-tabs-scroll::-webkit-scrollbar {
  display: none;
}

.mobile-tab-select {
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 0.78rem;
  padding: 3px 22px 3px 8px;
  border-radius: 4px;
  outline: none;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%239aa0a6'%3e%3cpath d='M7 10l5 5 5-5z'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 4px center;
  background-size: 15px;
  max-width: 120px;
}

.mobile-tab-select:focus {
  border-color: var(--primary);
}

.tab-item {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0 12px;
  height: 100%;
  cursor: pointer;
  white-space: nowrap !important;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  transition: all 0.15s ease;
}

.tab-item:hover {
  color: var(--text-primary);
}

.tab-item.active {
  color: var(--text-primary);
  font-weight: 600;
  border-bottom: 2px solid var(--text-primary);
}

.tab-badge {
  font-size: 0.65rem;
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  padding: 0 5px;
  border-radius: 9px;
  color: var(--text-secondary);
}

.tab-badge.green { color: #10b981; }
.tab-badge.red { color: #ef4444; }

/* Status & Timing Line (Postman Style) */
.response-meta-line {
  font-size: 0.76rem;
  color: var(--text-secondary);
}

.status-text.status-2xx { color: #10b981; }
.status-text.status-3xx { color: #f59e0b; }
.status-text.status-4xx { color: #fb923c; }
.status-text.status-5xx { color: #ef4444; }

.meta-separator {
  color: var(--text-muted);
  opacity: 0.6;
}

.meta-item {
  color: var(--text-secondary);
}

/* Secondary Subtoolbar */
.response-subtoolbar {
  background: var(--bg-terminal);
  border-color: var(--border-color) !important;
  min-height: 30px;
}

.subtool-btn {
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  border-radius: 4px;
  padding: 2px 7px;
  font-size: 0.72rem;
  cursor: pointer;
}

.subtool-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.subtool-btn.active {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-color);
}

.icon-tool-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 3px 6px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
}

.icon-tool-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.icon-tool-btn.active {
  color: var(--primary);
  background: var(--primary-bg);
}

.response-search-bar {
  background: var(--bg-surface-elevated);
  border-color: var(--border-color) !important;
  height: 30px;
}

.search-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.78rem;
}

/* Postman Code Editor View */
.code-editor-viewport {
  background: var(--bg-terminal);
  height: 100%;
}

.editor-lines-container {
  padding: 6px 0;
}

.editor-row {
  min-height: 20px;
  line-height: 20px;
  font-size: 0.8rem;
  white-space: pre;
  transition: background 0.1s ease;
}

.editor-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.line-number {
  width: 48px;
  min-width: 48px;
  text-align: right;
  padding-right: 14px;
  color: var(--text-muted);
  border-right: 1px solid var(--border-color-subtle);
  opacity: 0.7;
  user-select: none;
  font-size: 0.75rem;
}

.line-content {
  padding-left: 14px;
  flex-grow: 1;
  color: var(--text-terminal);
  tab-size: 2;
}

.line-content.wrap-enabled {
  white-space: pre-wrap;
  word-break: break-all;
}

/* Postman Official Dark Syntax Highlight Colors */
:deep(.json-key) {
  color: #79c0ff; /* Postman Ice Cyan/Blue */
  font-weight: 500;
}

:deep(.json-string) {
  color: #ffab70; /* Postman Coral/Peach */
}

:deep(.json-number) {
  color: #7ee787; /* Postman Mint Green */
}

:deep(.json-boolean) {
  color: #d2a8ff; /* Postman Lavender */
  font-weight: 600;
}

:deep(.json-null) {
  color: #8b949e;
  font-style: italic;
}

/* Empty State Experience */
.empty-state-wrap {
  animation: fadeIn 0.25s ease-out;
}

.empty-icon-halo {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(11, 95, 255, 0.06);
  border: 1px solid rgba(11, 95, 255, 0.2);
  box-shadow: 0 0 28px rgba(11, 95, 255, 0.1);
}

.empty-svg {
  width: 34px;
  height: 34px;
}

.flask-stroke {
  stroke: var(--text-muted);
}

.empty-heading {
  font-size: 0.95rem;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.empty-subtext {
  max-width: 400px;
  line-height: 1.5;
}

.shortcut-pill {
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-color);
  padding: 1px 6px;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.7rem;
  color: var(--text-primary);
  font-weight: 600;
}

.feature-chip {
  font-size: 0.68rem;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-color-subtle);
  padding: 2px 9px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
}

/* Tables */
.headers-table-wrap {
  border-color: var(--border-color) !important;
}

.grid-table {
  border-collapse: collapse;
  font-size: 0.78rem;
}

.grid-table th {
  background: var(--bg-surface-elevated);
  border-bottom: 1px solid var(--border-color);
  padding: 6px 12px;
  font-size: 0.7rem;
  color: var(--text-secondary);
  text-align: left;
}

.grid-table td {
  border-bottom: 1px solid var(--border-color-subtle);
}

.table-row-hover:hover {
  background: rgba(255, 255, 255, 0.03);
}

.assertion-result-item {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

.result-badge {
  font-size: 0.65rem;
  padding: 1px 6px;
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

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(3px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
