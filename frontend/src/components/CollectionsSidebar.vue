<template>
  <div class="collections-sidebar d-flex flex-column h-100">
    <!-- Top Action Header -->
    <div class="sidebar-header px-3 py-2 d-flex align-center justify-space-between border-b flex-shrink-0">
      <div class="d-flex align-center text-caption font-weight-bold text-secondary">
        <v-icon size="16" class="mr-3" color="secondary">mdi-folder-multiple-outline</v-icon>
        <span>COLLECTIONS</span>
      </div>
      <div class="d-flex align-center gap-1">
        <button
          v-if="isAuthenticated"
          type="button"
          class="sidebar-action-btn"
          title="New Collection"
          @click="showCreateColDialog = true"
        >
          <v-icon size="16">mdi-plus</v-icon>
        </button>
        <button
          v-if="isAuthenticated"
          type="button"
          class="sidebar-action-btn"
          title="Refresh Collections"
          :disabled="store.isLoadingCollections"
          @click="loadCollections"
        >
          <v-progress-circular
            v-if="store.isLoadingCollections"
            indeterminate
            size="12"
            width="2"
            color="primary"
          />
          <v-icon v-else size="15">mdi-refresh</v-icon>
        </button>
        <button
          type="button"
          class="sidebar-action-btn"
          title="Collapse Sidebar (Ctrl+B)"
          @click="emit('toggle-sidebar')"
        >
          <v-icon size="16">mdi-dock-left</v-icon>
        </button>
      </div>
    </div>

    <!-- Quick Action: New Blank Request -->
    <div class="px-3 py-2 flex-shrink-0 border-b">
      <button
        type="button"
        class="new-request-bar-btn w-100 d-flex align-center justify-center py-1.5 px-3"
        @click="handleNewRequest"
      >
        <v-icon size="15" class="mr-1.5">mdi-plus</v-icon>
        <span class="font-weight-medium text-caption">New Blank Request</span>
      </button>
    </div>

    <!-- Scrollable Sidebar Content -->
    <div class="sidebar-scrollable flex-grow-1 overflow-y-auto">
      <!-- Section: Quick Starters -->
      <div class="sidebar-section px-3 py-2">
        <div class="sidebar-section-header d-flex align-center justify-space-between mb-1">
          <span class="section-label">STARTER TEMPLATES</span>
        </div>
        <div class="template-list d-flex flex-column gap-1">
          <div
            v-for="tpl in quickTemplates"
            :key="tpl.name"
            class="template-row d-flex align-center justify-space-between px-2 py-1.5 rounded cursor-pointer"
            @click="loadTemplate(tpl)"
          >
            <div class="d-flex align-center text-truncate mr-1">
              <span :class="['dev-method-badge mr-2 font-mono', tpl.method.toLowerCase()]">
                {{ tpl.method }}
              </span>
              <span class="text-caption text-truncate item-name">{{ tpl.name }}</span>
            </div>
            <v-icon size="13" class="text-muted row-arrow">mdi-chevron-right</v-icon>
          </div>
        </div>
      </div>

      <!-- Divider -->
      <div class="section-divider"></div>

      <!-- Section: Collections & Saved Requests -->
      <div class="sidebar-section px-3 py-2">
        <div class="sidebar-section-header d-flex align-center justify-space-between mb-2">
          <span class="section-label">SAVED REQUESTS</span>
          <span v-if="store.searchFilter" class="filter-indicator font-mono">Filtered</span>
        </div>

        <!-- Guest Prompt Box -->
        <div
          v-if="!isAuthenticated"
          class="guest-callout-box p-3 pa-3 rounded border text-left my-1"
        >
          <div class="d-flex align-center mb-1">
            <v-icon size="16" class="mr-1.5" color="primary">mdi-cloud-outline</v-icon>
            <span class="text-caption font-weight-bold">Cloud Sync</span>
          </div>
          <p class="text-caption text-muted mb-2 lh-sm">
            Sign in to organize endpoints into collections and sync across sessions.
          </p>
          <button
            type="button"
            class="guest-signin-btn w-100 py-1 text-caption font-weight-medium"
            @click="emit('require-auth', 'Sign in to create and manage personal API collections.')"
          >
            Sign In to Save
          </button>
        </div>

        <!-- Authenticated Loading State -->
        <div v-else-if="store.isLoadingCollections" class="text-center pa-4 text-muted">
          <v-progress-circular indeterminate size="18" width="2" color="primary" class="mb-2" />
          <div class="text-caption">Loading collections...</div>
        </div>

        <!-- Authenticated Empty State -->
        <div
          v-else-if="filteredCollections.length === 0"
          class="empty-collections-box pa-4 text-center rounded border"
        >
          <v-icon size="24" color="grey" class="mb-1">mdi-folder-outline</v-icon>
          <div class="text-caption text-secondary font-weight-medium mb-1">
            {{ store.searchFilter ? 'No matching requests' : 'No collections created' }}
          </div>
          <div class="text-caption text-muted mb-3" style="font-size: 0.75rem;">
            {{ store.searchFilter ? 'Try clearing your search query.' : 'Group and organize your API endpoints here.' }}
          </div>
          <button
            v-if="!store.searchFilter"
            type="button"
            class="create-col-inline-btn text-caption font-weight-medium py-1 px-3"
            @click="showCreateColDialog = true"
          >
            <v-icon size="14" class="mr-1">mdi-plus</v-icon>
            Create Collection
          </button>
        </div>

        <!-- User Collections Tree -->
        <div v-else class="collections-tree d-flex flex-column gap-1">
          <div
            v-for="col in filteredCollections"
            :key="col.id"
            class="collection-node rounded"
          >
            <!-- Folder Header Row -->
            <div
              class="folder-row d-flex align-center justify-space-between px-2 py-1.5 cursor-pointer"
              @click="toggleFolder(col.id)"
            >
              <div class="d-flex align-center text-truncate mr-2">
                <v-icon size="14" class="mr-1.5 text-muted folder-caret">
                  {{ isFolderOpen(col.id) ? 'mdi-chevron-down' : 'mdi-chevron-right' }}
                </v-icon>
                <v-icon size="15" class="mr-1.5 folder-icon" color="amber-darken-1">
                  {{ isFolderOpen(col.id) ? 'mdi-folder-open' : 'mdi-folder' }}
                </v-icon>
                <span class="text-caption text-truncate font-weight-medium folder-name">
                  {{ col.name }}
                </span>
                <span v-if="col.requests?.length" class="folder-count font-mono ml-1.5">
                  {{ col.requests.length }}
                </span>
              </div>

              <div class="folder-actions d-flex align-center gap-1">
                <button
                  type="button"
                  class="node-icon-btn"
                  title="Delete collection"
                  @click.stop="confirmDeleteCollection(col)"
                >
                  <v-icon size="13">mdi-delete-outline</v-icon>
                </button>
              </div>
            </div>

            <!-- Folder Children (Requests) -->
            <div v-if="isFolderOpen(col.id)" class="folder-items pl-4 pr-1 py-1">
              <div
                v-if="!col.requests || col.requests.length === 0"
                class="empty-folder-hint py-1 px-2 text-caption text-muted"
              >
                Empty collection
              </div>

              <div
                v-for="req in col.requests"
                :key="req.id"
                :class="['request-tree-item d-flex align-center justify-space-between px-2 py-1 rounded cursor-pointer mb-0.5', { active: store.currentRequest.id === req.id }]"
                @click="onRequestClicked(req)"
              >
                <div class="d-flex align-center text-truncate mr-2">
                  <span :class="['dev-method-badge mr-2 font-mono', req.method.toLowerCase()]">
                    {{ req.method }}
                  </span>
                  <span class="text-caption text-truncate req-title">
                    {{ req.name }}
                  </span>
                </div>

                <button
                  type="button"
                  class="node-icon-btn req-del"
                  title="Delete request"
                  @click.stop="confirmDeleteRequest(req)"
                >
                  <v-icon size="12">mdi-close</v-icon>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Collection Dialog (Crisp Human Developer Modal) -->
    <v-dialog v-model="showCreateColDialog" max-width="400">
      <div class="dev-modal-card pa-4 rounded border">
        <div class="d-flex align-center justify-space-between pb-3 border-b mb-3">
          <div class="d-flex align-center font-weight-bold text-subtitle-2">
            <v-icon size="18" color="primary" class="mr-2">mdi-folder-plus-outline</v-icon>
            <span>New Collection</span>
          </div>
          <button type="button" class="modal-close-btn" @click="showCreateColDialog = false">
            <v-icon size="16">mdi-close</v-icon>
          </button>
        </div>

        <div class="mb-3">
          <label class="dev-field-label">NAME</label>
          <input
            v-model="newColName"
            type="text"
            placeholder="e.g. Authentication APIs"
            class="dev-input w-100"
            autofocus
          />
        </div>

        <div class="mb-4">
          <label class="dev-field-label">DESCRIPTION (OPTIONAL)</label>
          <textarea
            v-model="newColDesc"
            rows="2"
            placeholder="Brief purpose of endpoints in this folder"
            class="dev-input w-100"
            style="resize: none;"
          ></textarea>
        </div>

        <div class="d-flex align-center justify-end gap-2 pt-2 border-t">
          <button
            type="button"
            class="dev-btn-secondary px-3 py-1.5 text-caption font-weight-medium"
            @click="showCreateColDialog = false"
          >
            Cancel
          </button>
          <button
            type="button"
            class="dev-btn-primary px-3 py-1.5 text-caption font-weight-medium d-flex align-center"
            :disabled="!newColName.trim() || isCreatingCol"
            @click="handleCreateCollection"
          >
            <v-progress-circular
              v-if="isCreatingCol"
              indeterminate
              size="12"
              width="2"
              color="white"
              class="mr-1.5"
            />
            <span>Create</span>
          </button>
        </div>
      </div>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, defineEmits } from "vue";
import { api } from "@/api/client";
import {
  store,
  isAuthenticated,
  loadCollections,
  selectSavedRequest,
  resetCurrentRequest,
  showToast,
} from "@/stores/appState";

const emit = defineEmits(["request-selected", "require-auth", "toggle-sidebar"]);

const showCreateColDialog = ref(false);
const newColName = ref("");
const newColDesc = ref("");
const isCreatingCol = ref(false);

// Folder open/closed state tracking
const openFolders = ref(new Set());

function toggleFolder(colId) {
  if (openFolders.value.has(colId)) {
    openFolders.value.delete(colId);
  } else {
    openFolders.value.add(colId);
  }
}

function isFolderOpen(colId) {
  // If search is active or set contains it, keep open
  if (store.searchFilter) return true;
  return openFolders.value.has(colId);
}

const quickTemplates = [
  {
    name: "HTTP GET Echo",
    method: "GET",
    url: "https://httpbin.org/get",
    paramsList: [{ key: "source", value: "requestlab", enabled: true }],
    headersList: [{ key: "Accept", value: "application/json", enabled: true }],
    body: "",
    assertions: [
      { type: "status_code", operator: "equals", expected: 200 },
      { type: "response_time", operator: "less_than", expected: 2000 },
    ],
  },
  {
    name: "POST JSON Payload",
    method: "POST",
    url: "https://httpbin.org/post",
    paramsList: [],
    headersList: [{ key: "Content-Type", value: "application/json", enabled: true }],
    body: JSON.stringify({ item: "Developer Toolkit", version: "1.0.0" }, null, 2),
    assertions: [
      { type: "status_code", operator: "equals", expected: 200 },
      { type: "json_field", field_path: "json.item", operator: "equals", expected: "Developer Toolkit" },
    ],
  },
  {
    name: "404 Error Status Test",
    method: "GET",
    url: "https://httpbin.org/status/404",
    paramsList: [],
    headersList: [],
    body: "",
    assertions: [
      { type: "status_code", operator: "equals", expected: 404 },
    ],
  },
  {
    name: "Latency Check (1s)",
    method: "GET",
    url: "https://httpbin.org/delay/1",
    paramsList: [],
    headersList: [],
    body: "",
    assertions: [
      { type: "status_code", operator: "equals", expected: 200 },
      { type: "response_time", operator: "less_than", expected: 3000 },
    ],
  },
];

const filteredCollections = computed(() => {
  const query = store.searchFilter?.trim().toLowerCase();
  if (!query) return store.collections;

  return store.collections.filter((col) => {
    if (col.name.toLowerCase().includes(query)) return true;
    if (col.requests?.some((r) => r.name.toLowerCase().includes(query) || r.url.toLowerCase().includes(query))) {
      return true;
    }
    return false;
  });
});

function handleNewRequest() {
  resetCurrentRequest();
  emit("request-selected");
}

function loadTemplate(tpl) {
  resetCurrentRequest();
  store.currentRequest.name = tpl.name;
  store.currentRequest.method = tpl.method;
  store.currentRequest.url = tpl.url;
  store.currentRequest.paramsList = tpl.paramsList.length ? [...tpl.paramsList] : [{ key: "", value: "", enabled: true }];
  store.currentRequest.headersList = tpl.headersList.length ? [...tpl.headersList] : [{ key: "", value: "", enabled: true }];
  store.currentRequest.body = tpl.body;
  store.currentRequest.assertions = [...tpl.assertions];
  emit("request-selected");
}

function onRequestClicked(req) {
  selectSavedRequest(req);
  emit("request-selected", req);
}

async function handleCreateCollection() {
  if (!newColName.value.trim()) return;
  isCreatingCol.value = true;
  try {
    const res = await api.createCollection(newColName.value.trim(), newColDesc.value.trim());
    newColName.value = "";
    newColDesc.value = "";
    showCreateColDialog.value = false;
    showToast("Collection created", "success");
    await loadCollections();
    if (res?.data?.id) {
      openFolders.value.add(res.data.id);
    }
  } catch (err) {
    showToast("Failed to create collection: " + (err.response?.data?.detail || err.message), "error");
  } finally {
    isCreatingCol.value = false;
  }
}

async function confirmDeleteCollection(col) {
  if (confirm(`Delete collection "${col.name}" and all its saved requests?`)) {
    try {
      await api.deleteCollection(col.id);
      showToast("Collection deleted", "info");
      openFolders.value.delete(col.id);
      await loadCollections();
    } catch (err) {
      showToast("Failed to delete collection: " + (err.response?.data?.detail || err.message), "error");
    }
  }
}

async function confirmDeleteRequest(req) {
  if (confirm(`Delete saved request "${req.name}"?`)) {
    try {
      await api.deleteSavedRequest(req.id);
      showToast("Request deleted", "info");
      if (store.currentRequest.id === req.id) {
        resetCurrentRequest();
      }
      await loadCollections();
    } catch (err) {
      showToast("Failed to delete request: " + (err.response?.data?.detail || err.message), "error");
    }
  }
}
</script>

<style scoped>
.collections-sidebar {
  background: var(--bg-sidebar);
  color: var(--text-primary);
  font-size: 13px;
}

.sidebar-header {
  height: 38px;
  border-color: var(--border-color) !important;
}

.sidebar-action-btn {
  background: transparent;
  border: none;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.sidebar-action-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

/* Postman Style New Request Button */
.new-request-bar-btn {
  background: transparent;
  border: 1px dashed var(--border-color);
  border-radius: 5px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.new-request-bar-btn:hover {
  background: var(--bg-hover);
  border-color: var(--primary);
  color: var(--text-primary);
}

.section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.section-divider {
  height: 1px;
  background: var(--border-color-subtle);
  margin: 4px 12px;
}

/* Template Rows */
.template-row {
  border: 1px solid transparent;
  transition: all 0.12s ease;
}

.template-row:hover {
  background: var(--bg-hover);
  border-color: var(--border-color-subtle);
}

.template-row .row-arrow {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.template-row:hover .row-arrow {
  opacity: 1;
}

.item-name {
  color: var(--text-primary);
  font-size: 12px;
}

/* Developer Method Badges */
.dev-method-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
  min-width: 32px;
  text-align: center;
  display: inline-block;
  line-height: 1.2;
}

.dev-method-badge.get { color: #10b981; background: rgba(16, 185, 129, 0.12); }
.dev-method-badge.post { color: #f59e0b; background: rgba(245, 158, 11, 0.12); }
.dev-method-badge.put { color: #3b82f6; background: rgba(59, 130, 246, 0.12); }
.dev-method-badge.patch { color: #8b5cf6; background: rgba(139, 92, 246, 0.12); }
.dev-method-badge.delete { color: #ef4444; background: rgba(239, 68, 68, 0.12); }

/* Guest Callout Box */
.guest-callout-box {
  background: var(--bg-surface);
  border-color: var(--border-color) !important;
}

.guest-signin-btn {
  background: var(--bg-hover);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.guest-signin-btn:hover {
  background: var(--primary);
  color: #ffffff;
  border-color: transparent;
}

/* Empty State */
.empty-collections-box {
  background: var(--bg-surface);
  border-color: var(--border-color-subtle) !important;
}

.create-col-inline-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 4px;
  cursor: pointer;
}

.create-col-inline-btn:hover {
  background: var(--bg-hover);
  border-color: var(--primary);
}

/* Tree Nodes */
.folder-row {
  border-radius: 4px;
  user-select: none;
  transition: background 0.12s ease;
}

.folder-row:hover {
  background: var(--bg-hover);
}

.folder-name {
  color: var(--text-primary);
  font-size: 12px;
}

.folder-count {
  font-size: 10px;
  color: var(--text-muted);
  background: var(--bg-surface);
  border: 1px solid var(--border-color-subtle);
  padding: 0 4px;
  border-radius: 9999px;
}

.folder-actions {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.folder-row:hover .folder-actions {
  opacity: 1;
}

.node-icon-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  width: 20px;
  height: 20px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.node-icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.node-icon-btn.req-del:hover {
  color: #ef4444;
}

.request-tree-item {
  border-left: 2px solid transparent;
  transition: all 0.12s ease;
}

.request-tree-item:hover {
  background: var(--bg-hover);
}

.request-tree-item.active {
  background: var(--bg-surface-elevated);
  border-left-color: var(--primary);
}

.request-tree-item .req-del {
  opacity: 0;
}

.request-tree-item:hover .req-del {
  opacity: 1;
}

.req-title {
  color: var(--text-primary);
  font-size: 12px;
}

.filter-indicator {
  font-size: 10px;
  color: var(--primary);
}

/* Developer Dialog */
.dev-modal-card {
  background: var(--bg-dialog);
  border-color: var(--border-color) !important;
  color: var(--text-primary);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
}

.modal-close-btn:hover {
  color: var(--text-primary);
}

.dev-field-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.dev-input {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 6px 8px;
  font-size: 12px;
  border-radius: 4px;
  outline: none;
}

.dev-input:focus {
  border-color: var(--primary);
}

.dev-btn-secondary {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: 4px;
  cursor: pointer;
}

.dev-btn-secondary:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.dev-btn-primary {
  background: var(--primary);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.dev-btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.dev-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.font-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>
