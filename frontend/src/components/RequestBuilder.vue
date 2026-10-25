<template>
  <div class="request-console pa-3 d-flex flex-column" style="min-height: 0;">
    <!-- Top Action Bar: Request Title & Save -->
    <div class="d-flex align-center justify-space-between mb-2 flex-wrap gap-2 flex-shrink-0">
      <div class="d-flex align-center flex-grow-1 mr-2" style="min-width: 0;">
        <input
          v-model="store.currentRequest.name"
          class="request-title-input"
          placeholder="Untitled Request"
        />
        <span
          v-if="store.currentRequest.id"
          class="saved-badge ml-2 font-mono"
        >
          #{{ store.currentRequest.id }}
        </span>
      </div>

      <div class="d-flex align-center gap-2">
        <button
          type="button"
          class="btn-secondary text-caption font-weight-medium d-flex align-center px-3 py-1"
          @click="emit('open-save-dialog')"
        >
          <v-icon size="14" class="mr-1">mdi-content-save-outline</v-icon>
          <span>Save</span>
        </button>
      </div>
    </div>

    <!-- Omni Request Bar (Postman Style) -->
    <div class="omni-request-bar d-flex align-center mb-2 flex-shrink-0">
      <!-- Method Selector -->
      <select
        v-model="store.currentRequest.method"
        :class="['method-select font-mono font-weight-bold', store.currentRequest.method.toLowerCase()]"
      >
        <option value="GET">GET</option>
        <option value="POST">POST</option>
        <option value="PUT">PUT</option>
        <option value="PATCH">PATCH</option>
        <option value="DELETE">DELETE</option>
      </select>

      <!-- URL Input Field -->
      <input
        v-model="store.currentRequest.url"
        placeholder="Enter request URL (e.g. https://httpbin.org/get)"
        class="url-input font-mono flex-grow-1 px-3"
        @keyup.enter="handleSendRequest"
      />

      <!-- Send Button -->
      <button
        type="button"
        class="send-btn font-weight-bold d-flex align-center px-4"
        :disabled="store.isSendingRequest"
        title="Send Request (Ctrl + Enter)"
        @click="handleSendRequest"
      >
        <v-progress-circular
          v-if="store.isSendingRequest"
          indeterminate
          size="14"
          width="2"
          color="white"
          class="mr-2"
        />
        <span v-else class="mr-1">Send</span>
        <span class="shortcut-hint d-none d-lg-inline ml-1">⌘↵</span>
      </button>
    </div>

    <!-- Authentic Postman Style Tabs -->
    <div class="tab-bar border-b d-flex align-center mb-2 flex-shrink-0">
      <button
        type="button"
        :class="['tab-item', { active: activeTab === 'params' }]"
        @click="activeTab = 'params'"
      >
        <span>Params</span>
        <span v-if="validParamsCount > 0" class="badge-count ml-1">{{ validParamsCount }}</span>
      </button>

      <button
        type="button"
        :class="['tab-item', { active: activeTab === 'auth' }]"
        @click="activeTab = 'auth'"
      >
        <span>Authorization</span>
        <span v-if="store.currentRequest.auth.type !== 'none'" class="badge-dot ml-1">●</span>
      </button>

      <button
        type="button"
        :class="['tab-item', { active: activeTab === 'headers' }]"
        @click="activeTab = 'headers'"
      >
        <span>Headers</span>
        <span v-if="validHeadersCount > 0" class="badge-count ml-1">{{ validHeadersCount }}</span>
      </button>

      <button
        type="button"
        :class="['tab-item', { active: activeTab === 'body' }]"
        @click="activeTab = 'body'"
      >
        <span>Body</span>
        <span v-if="hasBodyContent" class="badge-dot ml-1 green">●</span>
      </button>

      <button
        type="button"
        :class="['tab-item', { active: activeTab === 'tests' }]"
        @click="activeTab = 'tests'"
      >
        <span>Tests</span>
        <span v-if="store.currentRequest.assertions?.length > 0" class="badge-count ml-1">
          {{ store.currentRequest.assertions.length }}
        </span>
      </button>
    </div>

    <!-- Scrollable Tab Content Container -->
    <div class="tab-content-area overflow-y-auto" style="min-height: 0; max-height: 280px;">
      <!-- 1. Query Params Tab -->
      <div v-if="activeTab === 'params'" class="pr-1">
        <div class="d-flex align-center justify-space-between mb-2">
          <span class="text-caption text-grey font-weight-medium">Query Parameters</span>
          <button
            type="button"
            class="text-btn text-caption font-weight-medium"
            @click="addParamRow"
          >
            + Add Row
          </button>
        </div>

        <div class="table-responsive-wrapper">
          <table class="grid-table w-100">
            <thead>
              <tr>
                <th style="width: 30px;"></th>
                <th>KEY</th>
                <th>VALUE</th>
                <th style="width: 30px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, idx) in store.currentRequest.paramsList"
                :key="idx"
              >
                <td class="text-center">
                  <input
                    v-model="item.enabled"
                    type="checkbox"
                    class="native-chk"
                  />
                </td>
                <td>
                  <input
                    v-model="item.key"
                    placeholder="Key"
                    class="grid-input font-mono"
                    @input="onParamInput(idx)"
                  />
                </td>
                <td>
                  <input
                    v-model="item.value"
                    placeholder="Value"
                    class="grid-input font-mono"
                  />
                </td>
                <td class="text-center">
                  <button
                    type="button"
                    class="icon-del-btn"
                    title="Delete Row"
                    @click="removeParamRow(idx)"
                  >
                    <v-icon size="13" color="grey">mdi-close</v-icon>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 2. Headers Tab -->
      <div v-else-if="activeTab === 'headers'" class="pr-1">
        <div class="d-flex align-center justify-space-between mb-2">
          <span class="text-caption text-grey font-weight-medium">HTTP Request Headers</span>
          <div class="d-flex align-center gap-2">
            <button
              type="button"
              class="text-btn text-caption font-weight-medium"
              @click="addHeaderPreset('Content-Type', 'application/json')"
            >
              + application/json
            </button>
            <button
              type="button"
              class="text-btn text-caption font-weight-medium"
              @click="addHeaderRow"
            >
              + Add Row
            </button>
          </div>
        </div>

        <div class="table-responsive-wrapper">
          <table class="grid-table w-100">
            <thead>
              <tr>
                <th style="width: 30px;"></th>
                <th>HEADER</th>
                <th>VALUE</th>
                <th style="width: 30px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(item, idx) in store.currentRequest.headersList"
                :key="idx"
              >
                <td class="text-center">
                  <input
                    v-model="item.enabled"
                    type="checkbox"
                    class="native-chk"
                  />
                </td>
                <td>
                  <input
                    v-model="item.key"
                    placeholder="Header Name"
                    class="grid-input font-mono"
                    @input="onHeaderInput(idx)"
                  />
                </td>
                <td>
                  <input
                    v-model="item.value"
                    placeholder="Value"
                    class="grid-input font-mono"
                  />
                </td>
                <td class="text-center">
                  <button
                    type="button"
                    class="icon-del-btn"
                    title="Delete Header"
                    @click="removeHeaderRow(idx)"
                  >
                    <v-icon size="13" color="grey">mdi-close</v-icon>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 3. Authorization Tab -->
      <div v-else-if="activeTab === 'auth'" class="pa-1">
        <div class="auth-section pa-3 rounded border mb-3">
          <div class="d-flex align-center gap-3 mb-3">
            <label class="text-caption font-weight-bold" style="min-width: 90px;">Type</label>
            <select
              v-model="store.currentRequest.auth.type"
              class="auth-select font-weight-medium text-caption"
            >
              <option value="none">No Auth</option>
              <option value="bearer">Bearer Token</option>
              <option value="basic">Basic Auth</option>
              <option value="apikey">API Key</option>
            </select>
          </div>

          <!-- Bearer Token -->
          <div v-if="store.currentRequest.auth.type === 'bearer'" class="auth-fields">
            <div class="d-flex align-center gap-3 mb-2">
              <label class="text-caption font-weight-medium text-grey" style="min-width: 90px;">Token</label>
              <input
                v-model="store.currentRequest.auth.bearerToken"
                type="password"
                placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                class="field-input font-mono flex-grow-1"
              />
            </div>
            <div class="text-caption text-grey ml-12 pl-11">
              Token is automatically added to the <code>Authorization: Bearer</code> header.
            </div>
          </div>

          <!-- Basic Auth -->
          <div v-else-if="store.currentRequest.auth.type === 'basic'" class="auth-fields">
            <div class="d-flex align-center gap-3 mb-2">
              <label class="text-caption font-weight-medium text-grey" style="min-width: 90px;">Username</label>
              <input
                v-model="store.currentRequest.auth.basicUser"
                placeholder="admin"
                class="field-input font-mono flex-grow-1"
              />
            </div>
            <div class="d-flex align-center gap-3 mb-2">
              <label class="text-caption font-weight-medium text-grey" style="min-width: 90px;">Password</label>
              <input
                v-model="store.currentRequest.auth.basicPass"
                type="password"
                placeholder="••••••••"
                class="field-input font-mono flex-grow-1"
              />
            </div>
            <div class="text-caption text-grey ml-12 pl-11">
              Credentials are base64-encoded into the <code>Authorization: Basic</code> header.
            </div>
          </div>

          <!-- API Key -->
          <div v-else-if="store.currentRequest.auth.type === 'apikey'" class="auth-fields">
            <div class="d-flex align-center gap-3 mb-2">
              <label class="text-caption font-weight-medium text-grey" style="min-width: 90px;">Key</label>
              <input
                v-model="store.currentRequest.auth.apiKeyName"
                placeholder="X-API-Key"
                class="field-input font-mono flex-grow-1"
              />
            </div>
            <div class="d-flex align-center gap-3 mb-2">
              <label class="text-caption font-weight-medium text-grey" style="min-width: 90px;">Value</label>
              <input
                v-model="store.currentRequest.auth.apiKeyValue"
                type="password"
                placeholder="secret_key"
                class="field-input font-mono flex-grow-1"
              />
            </div>
            <div class="d-flex align-center gap-3">
              <label class="text-caption font-weight-medium text-grey" style="min-width: 90px;">Add to</label>
              <select
                v-model="store.currentRequest.auth.apiKeyLocation"
                class="auth-select text-caption"
              >
                <option value="header">Header</option>
                <option value="query">Query Params</option>
              </select>
            </div>
          </div>

          <div v-else class="text-caption text-grey">
            This request will not carry any injected authorization headers.
          </div>
        </div>
      </div>

      <!-- 4. JSON Request Body Tab -->
      <div v-else-if="activeTab === 'body'" class="d-flex flex-column pr-1" style="min-height: 0;">
        <div class="d-flex align-center justify-space-between mb-2 flex-shrink-0">
          <div class="d-flex align-center">
            <span class="text-caption text-grey mr-2">Body Content Type: <strong class="text-primary">JSON (application/json)</strong></span>
            <span v-if="jsonValidation.valid && store.currentRequest.body.trim()" class="status-tag valid">
              JSON Valid
            </span>
            <span v-else-if="!jsonValidation.valid" class="status-tag invalid">
              {{ jsonValidation.error }}
            </span>
          </div>
          <button
            type="button"
            class="text-btn text-caption font-weight-medium"
            @click="prettifyJson"
          >
            Beautify
          </button>
        </div>

        <textarea
          v-model="store.currentRequest.body"
          placeholder='{\n  "key": "value"\n}'
          class="code-textarea w-100 font-mono pa-2 rounded"
          style="height: 150px; min-height: 100px; max-height: 250px; resize: vertical;"
          spellcheck="false"
        />
      </div>

      <!-- 5. Assertions / Tests Tab -->
      <div v-else-if="activeTab === 'tests'" class="pr-1">
        <div class="d-flex align-center justify-space-between mb-2">
          <span class="text-caption text-grey font-weight-medium">Response Assertions & Tests</span>
          <button
            type="button"
            class="text-btn text-caption font-weight-medium"
            @click="addAssertionRow"
          >
            + Add Test Assertion
          </button>
        </div>

        <div v-if="!store.currentRequest.assertions?.length" class="text-caption text-grey pa-4 text-center border rounded">
          No tests defined. Click "+ Add Test Assertion" to assert status code, latency, or JSON values.
        </div>

        <div v-else class="assertion-list">
          <div
            v-for="(ass, idx) in store.currentRequest.assertions"
            :key="idx"
            class="assertion-row pa-2 rounded mb-2 border d-flex align-center flex-wrap gap-2"
          >
            <select
              v-model="ass.type"
              class="auth-select text-caption"
              style="width: 140px;"
            >
              <option value="status_code">Status Code</option>
              <option value="response_time">Response Time (ms)</option>
              <option value="json_field">JSON Field</option>
            </select>

            <input
              v-if="ass.type === 'json_field'"
              v-model="ass.field_path"
              placeholder="field.path"
              class="field-input font-mono flex-grow-1 text-caption"
              style="min-width: 110px;"
            />

            <select
              v-model="ass.operator"
              class="auth-select text-caption"
              style="width: 120px;"
            >
              <option v-for="op in getOperatorsForType(ass.type)" :key="op" :value="op">{{ op }}</option>
            </select>

            <input
              v-model="ass.expected"
              placeholder="Expected Value"
              class="field-input font-mono flex-grow-1 text-caption"
              style="min-width: 90px;"
            />

            <button
              type="button"
              class="icon-del-btn"
              title="Remove Assertion"
              @click="removeAssertionRow(idx)"
            >
              <v-icon size="14" color="grey">mdi-close</v-icon>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineEmits } from "vue";
import { store, showToast } from "@/stores/appState";
import { api } from "@/api/client";

const emit = defineEmits(["open-save-dialog"]);

const activeTab = ref("params");

const validParamsCount = computed(() => {
  return store.currentRequest.paramsList.filter((p) => p.enabled && p.key.trim()).length;
});

const validHeadersCount = computed(() => {
  return store.currentRequest.headersList.filter((h) => h.enabled && h.key.trim()).length;
});

const hasBodyContent = computed(() => {
  return !!store.currentRequest.body && store.currentRequest.body.trim().length > 0;
});

const jsonValidation = computed(() => {
  const text = store.currentRequest.body?.trim();
  if (!text) return { valid: true };
  try {
    JSON.parse(text);
    return { valid: true };
  } catch (err) {
    return { valid: false, error: err.message.replace(/^JSON\.parse:\s*/, "") };
  }
});

function prettifyJson() {
  if (!store.currentRequest.body?.trim()) return;
  try {
    const parsed = JSON.parse(store.currentRequest.body);
    store.currentRequest.body = JSON.stringify(parsed, null, 2);
    showToast("JSON formatted", "success");
  } catch {
    showToast("Invalid JSON syntax, cannot format", "error");
  }
}

function onParamInput(index) {
  if (index === store.currentRequest.paramsList.length - 1 && store.currentRequest.paramsList[index].key) {
    addParamRow();
  }
}

function addParamRow() {
  store.currentRequest.paramsList.push({ key: "", value: "", enabled: true });
}

function removeParamRow(idx) {
  if (store.currentRequest.paramsList.length > 1) {
    store.currentRequest.paramsList.splice(idx, 1);
  } else {
    store.currentRequest.paramsList[0].key = "";
    store.currentRequest.paramsList[0].value = "";
  }
}

function onHeaderInput(index) {
  if (index === store.currentRequest.headersList.length - 1 && store.currentRequest.headersList[index].key) {
    addHeaderRow();
  }
}

function addHeaderRow() {
  store.currentRequest.headersList.push({ key: "", value: "", enabled: true });
}

function removeHeaderRow(idx) {
  if (store.currentRequest.headersList.length > 1) {
    store.currentRequest.headersList.splice(idx, 1);
  } else {
    store.currentRequest.headersList[0].key = "";
    store.currentRequest.headersList[0].value = "";
  }
}

function addHeaderPreset(key, value) {
  const existing = store.currentRequest.headersList.find((h) => h.key.toLowerCase() === key.toLowerCase());
  if (existing) {
    existing.value = value;
    existing.enabled = true;
  } else {
    store.currentRequest.headersList.unshift({ key, value, enabled: true });
  }
}

function getOperatorsForType(type) {
  if (type === "response_time") {
    return ["less_than", "greater_than", "equals"];
  }
  return ["equals", "not_equals", "contains", "exists"];
}

function addAssertionRow() {
  if (!store.currentRequest.assertions) store.currentRequest.assertions = [];
  store.currentRequest.assertions.push({
    type: "status_code",
    operator: "equals",
    expected: 200,
  });
}

function removeAssertionRow(idx) {
  store.currentRequest.assertions.splice(idx, 1);
}

// Send Request logic
async function handleSendRequest() {
  if (!store.currentRequest.url) {
    showToast("Please enter a request URL", "warning");
    return;
  }

  store.isSendingRequest = true;
  store.lastResponse = null;

  const paramsDict = {};
  for (const p of store.currentRequest.paramsList) {
    if (p.enabled && p.key.trim()) {
      paramsDict[p.key.trim()] = p.value;
    }
  }

  const headersDict = {};
  for (const h of store.currentRequest.headersList) {
    if (h.enabled && h.key.trim()) {
      headersDict[h.key.trim()] = h.value;
    }
  }

  const auth = store.currentRequest.auth;
  if (auth.type === "bearer" && auth.bearerToken) {
    headersDict["Authorization"] = `Bearer ${auth.bearerToken.trim()}`;
  } else if (auth.type === "basic" && (auth.basicUser || auth.basicPass)) {
    const creds = btoa(`${auth.basicUser}:${auth.basicPass}`);
    headersDict["Authorization"] = `Basic ${creds}`;
  } else if (auth.type === "apikey" && auth.apiKeyName && auth.apiKeyValue) {
    if (auth.apiKeyLocation === "query") {
      paramsDict[auth.apiKeyName.trim()] = auth.apiKeyValue;
    } else {
      headersDict[auth.apiKeyName.trim()] = auth.apiKeyValue;
    }
  }

  let bodyPayload = store.currentRequest.body?.trim() || null;

  const cleanAssertions = (store.currentRequest.assertions || []).map((a) => {
    let expVal = a.expected;
    if (a.type === "status_code" || a.type === "response_time") {
      const num = Number(expVal);
      if (!isNaN(num)) expVal = num;
    }
    return {
      type: a.type,
      operator: a.operator,
      expected: expVal,
      field_path: a.field_path || null,
    };
  });

  const payload = {
    method: store.currentRequest.method,
    url: store.currentRequest.url,
    headers: Object.keys(headersDict).length > 0 ? headersDict : null,
    params: Object.keys(paramsDict).length > 0 ? paramsDict : null,
    body: bodyPayload,
    assertions: cleanAssertions.length > 0 ? cleanAssertions : null,
    follow_redirects: store.currentRequest.followRedirects || false,
  };

  try {
    const res = await api.executeTemporary(payload);
    store.lastResponse = res.data;
  } catch (err) {
    if (err.response?.data?.detail) {
      store.lastResponse = {
        status_code: err.response.status || 500,
        response_time_ms: 0,
        response_headers: {},
        response_body: JSON.stringify(err.response.data, null, 2),
        error_message: typeof err.response.data.detail === "string"
          ? err.response.data.detail
          : JSON.stringify(err.response.data.detail),
        assertion_results: [],
      };
    } else {
      store.lastResponse = {
        status_code: 0,
        response_time_ms: 0,
        response_headers: {},
        response_body: "",
        error_message: err.message || "Network Error: Could not connect to RequestLab backend.",
        assertion_results: [],
      };
    }
  } finally {
    store.isSendingRequest = false;
  }
}
</script>

<style scoped>
.request-console {
  background: var(--bg-workspace-req);
  max-width: 100%;
  overflow-x: hidden;
  box-sizing: border-box;
}

.request-title-input {
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  color: var(--text-primary);
  font-weight: 600;
  font-size: 0.92rem;
  padding: 2px 6px;
  outline: none;
}

.request-title-input:hover,
.request-title-input:focus {
  background: var(--bg-hover);
  border-color: var(--border-color);
}

.saved-badge {
  font-size: 0.7rem;
  color: var(--text-muted);
  background: var(--bg-hover);
  padding: 1px 6px;
  border-radius: 3px;
}

.btn-secondary {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 4px;
  cursor: pointer;
}

.btn-secondary:hover {
  background: var(--bg-hover);
}

/* Postman Omni Request Bar */
.omni-request-bar {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  height: 36px;
}

.method-select {
  background: transparent;
  border: none;
  border-right: 1px solid var(--border-color);
  padding: 0 10px;
  height: 100%;
  outline: none;
  font-size: 0.8rem;
  cursor: pointer;
}

.method-select.get { color: #10b981; }
.method-select.post { color: #f59e0b; }
.method-select.put { color: #3b82f6; }
.method-select.patch { color: #a855f7; }
.method-select.delete { color: #ef4444; }

.url-input {
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 0.82rem;
  height: 100%;
  min-width: 0 !important;
}

.url-input::placeholder {
  color: var(--text-muted);
}

.send-btn {
  background: var(--primary);
  color: white;
  border: none;
  height: 100%;
  border-radius: 0 3px 3px 0;
  cursor: pointer;
  font-size: 0.82rem;
}

.send-btn:hover {
  background: var(--primary-hover);
}

.shortcut-hint {
  font-size: 0.7rem;
  opacity: 0.8;
}

/* Horizontal Tabs (Underline Active) */
.tab-bar {
  border-color: var(--border-color) !important;
  height: 34px;
  overflow-x: auto;
  white-space: nowrap;
  scrollbar-width: none;
  -webkit-overflow-scrolling: touch;
}

.tab-bar::-webkit-scrollbar {
  display: none;
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
}

.table-responsive-wrapper {
  overflow-x: auto;
  max-width: 100%;
  -webkit-overflow-scrolling: touch;
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

.badge-dot {
  font-size: 0.65rem;
  color: var(--primary);
}

.badge-dot.green {
  color: #10b981;
}

/* Spreadsheet Grid Table */
.grid-table {
  border-collapse: collapse;
  font-size: 0.78rem;
}

.grid-table th {
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-color);
  padding: 4px 8px;
  font-size: 0.7rem;
  color: var(--text-secondary);
  text-align: left;
}

.grid-table td {
  border: 1px solid var(--border-color);
  padding: 0;
}

.grid-input {
  background: transparent;
  border: none;
  outline: none;
  width: 100%;
  padding: 6px 8px;
  color: var(--text-primary);
  font-size: 0.8rem;
}

.native-chk {
  cursor: pointer;
  accent-color: var(--primary);
}

.icon-del-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 2px;
}

.text-btn {
  background: transparent;
  border: none;
  color: var(--primary);
  cursor: pointer;
}

.text-btn:hover {
  text-decoration: underline;
}

/* Auth / Fields */
.auth-section {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

.auth-select {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 4px 8px;
  color: var(--text-primary);
  outline: none;
}

.field-input {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 5px 8px;
  color: var(--text-primary);
  font-size: 0.8rem;
  outline: none;
}

.field-input:focus {
  border-color: var(--primary);
}

/* Code Editor */
.code-textarea {
  background: var(--bg-terminal);
  border: 1px solid var(--border-color);
  color: var(--text-terminal);
  font-size: 0.82rem;
  line-height: 1.5;
  outline: none;
  resize: none;
}

.status-tag {
  font-size: 0.7rem;
  padding: 1px 6px;
  border-radius: 3px;
}

.status-tag.valid {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.status-tag.invalid {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.assertion-row {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

.font-mono {
  font-family: Consolas, "Courier New", monospace;
}
</style>
