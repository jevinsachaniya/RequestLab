<template>
  <v-dialog v-model="visible" max-width="420">
    <div class="dev-modal-card pa-4 rounded border">
      <!-- Modal Header -->
      <div class="d-flex align-center justify-space-between pb-3 mb-3 border-b">
        <div class="d-flex align-center font-weight-bold text-subtitle-2">
          <v-icon size="17" color="primary" class="mr-2">mdi-content-save-outline</v-icon>
          <span>Save Request to Workspace</span>
        </div>
        <button type="button" class="modal-close-btn" @click="visible = false">
          <v-icon size="16">mdi-close</v-icon>
        </button>
      </div>

      <!-- Fields -->
      <div class="mb-3">
        <label class="dev-field-label">REQUEST NAME</label>
        <input
          v-model="requestName"
          type="text"
          placeholder="e.g. Fetch User Profile"
          class="dev-input w-100"
          autofocus
        />
      </div>

      <div v-if="store.collections.length === 0" class="mb-3">
        <div class="info-banner pa-2 rounded mb-2 text-caption">
          No collections found. Enter a name to create your first collection.
        </div>
        <label class="dev-field-label">NEW COLLECTION NAME</label>
        <input
          v-model="newCollectionName"
          type="text"
          placeholder="e.g. User APIs"
          class="dev-input w-100"
        />
      </div>

      <div v-else class="mb-3">
        <label class="dev-field-label">TARGET COLLECTION</label>
        <select v-model="selectedCollectionId" class="dev-select w-100">
          <option
            v-for="col in collectionOptions"
            :key="col.id"
            :value="col.id"
          >
            {{ col.name }}
          </option>
        </select>
      </div>

      <!-- Modal Actions -->
      <div class="d-flex align-center justify-end gap-2 pt-3 border-t mt-4">
        <button
          type="button"
          class="dev-btn-secondary px-3 py-1.5 text-caption font-weight-medium"
          @click="visible = false"
        >
          Cancel
        </button>
        <button
          type="button"
          class="dev-btn-primary px-3 py-1.5 text-caption font-weight-medium d-flex align-center"
          :disabled="!isValid || isSaving"
          @click="handleSave"
        >
          <v-progress-circular
            v-if="isSaving"
            indeterminate
            size="12"
            width="2"
            color="white"
            class="mr-1.5"
          />
          <span>Save</span>
        </button>
      </div>
    </div>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, defineProps, defineEmits } from "vue";
import { api } from "@/api/client";
import { store, loadCollections, showToast } from "@/stores/appState";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue", "saved"]);

const visible = ref(props.modelValue);
watch(() => props.modelValue, (val) => {
  visible.value = val;
  if (val) {
    requestName.value = store.currentRequest.name || "Untitled Request";
    selectedCollectionId.value = store.currentRequest.collectionId || (store.collections[0]?.id ?? null);
  }
});
watch(visible, (val) => emit("update:modelValue", val));

const requestName = ref("");
const selectedCollectionId = ref(null);
const newCollectionName = ref("");
const isSaving = ref(false);

const collectionOptions = computed(() => store.collections);

const isValid = computed(() => {
  if (!requestName.value.trim()) return false;
  if (store.collections.length === 0) {
    return !!newCollectionName.value.trim();
  }
  return !!selectedCollectionId.value;
});

async function handleSave() {
  isSaving.value = true;
  try {
    let targetCollectionId = selectedCollectionId.value;

    if (store.collections.length === 0 && newCollectionName.value.trim()) {
      const colRes = await api.createCollection(newCollectionName.value.trim());
      targetCollectionId = colRes.data.id;
    }

    const params = {};
    for (const p of store.currentRequest.paramsList) {
      if (p.enabled && p.key.trim()) params[p.key.trim()] = p.value;
    }
    const headers = {};
    for (const h of store.currentRequest.headersList) {
      if (h.enabled && h.key.trim()) headers[h.key.trim()] = h.value;
    }

    const payload = {
      name: requestName.value.trim(),
      method: store.currentRequest.method,
      url: store.currentRequest.url.trim(),
      headers,
      params,
      body: store.currentRequest.body || null,
      assertions: store.currentRequest.assertions || [],
    };

    let savedReq;
    if (store.currentRequest.id && store.currentRequest.collectionId === targetCollectionId) {
      const res = await api.updateSavedRequest(store.currentRequest.id, payload);
      savedReq = res.data;
    } else {
      const res = await api.createSavedRequest(targetCollectionId, payload);
      savedReq = res.data;
    }

    store.currentRequest.id = savedReq.id;
    store.currentRequest.collectionId = savedReq.collection_id;
    store.currentRequest.name = savedReq.name;

    await loadCollections();
    visible.value = false;
    showToast(`Request "${savedReq.name}" saved successfully`, "success");
    emit("saved", savedReq);
  } catch (err) {
    showToast("Failed to save request: " + (err.response?.data?.detail || err.message), "error");
  } finally {
    isSaving.value = false;
  }
}
</script>

<style scoped>
.dev-modal-card {
  background: var(--bg-dialog);
  border-color: var(--border-color) !important;
  color: var(--text-primary);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px;
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

.dev-input,
.dev-select {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 6px 10px;
  font-size: 12px;
  border-radius: 4px;
  outline: none;
}

.dev-input:focus,
.dev-select:focus {
  border-color: var(--primary);
}

.info-banner {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
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
  transition: background 0.15s ease;
}

.dev-btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.dev-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
