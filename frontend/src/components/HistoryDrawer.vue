<template>
  <v-navigation-drawer
    v-model="visible"
    location="right"
    temporary
    width="380"
    class="history-drawer"
  >
    <div class="pa-3 d-flex align-center justify-space-between border-b">
      <div class="text-subtitle-1 font-weight-bold d-flex align-center">
        <v-icon color="primary" class="mr-2" size="small">mdi-history</v-icon>
        Execution History
      </div>
      <div>
        <v-btn
          icon="mdi-refresh"
          size="x-small"
          variant="text"
          :loading="store.isLoadingHistory"
          @click="loadHistory(1)"
        />
        <v-btn
          icon="mdi-close"
          size="x-small"
          variant="text"
          @click="visible = false"
        />
      </div>
    </div>

    <div v-if="store.isLoadingHistory" class="text-center pa-4 text-grey">
      <v-progress-circular indeterminate size="24" color="primary" class="mb-2" />
      <div class="text-caption">Loading history...</div>
    </div>

    <div
      v-else-if="store.history.length === 0"
      class="text-center pa-6 text-grey text-caption"
    >
      No execution history yet. Sent requests will be logged here.
    </div>

    <v-list v-else density="compact" class="pa-2">
      <v-card
        v-for="item in store.history"
        :key="item.id"
        variant="outlined"
        class="mb-2 pa-2 rounded-lg history-card"
        @click="loadHistoryItem(item)"
      >
        <div class="d-flex align-center justify-space-between mb-1">
          <div class="d-flex align-center">
            <v-chip
              size="x-small"
              label
              :color="getMethodColor(item.method)"
              class="font-weight-bold mr-2 text-uppercase"
            >
              {{ item.method }}
            </v-chip>
            <v-chip
              v-if="item.status_code"
              size="x-small"
              :color="getStatusColor(item.status_code)"
              class="font-weight-bold"
            >
              {{ item.status_code }}
            </v-chip>
            <v-chip
              v-else
              size="x-small"
              color="error"
              class="font-weight-bold"
            >
              ERROR
            </v-chip>
          </div>

          <div class="d-flex align-center">
            <span v-if="item.response_time_ms" class="text-caption text-grey mr-2">
              {{ item.response_time_ms }}ms
            </span>
            <v-btn
              icon="mdi-delete-outline"
              size="x-small"
              variant="text"
              color="grey"
              @click.stop="deleteHistoryItem(item.id)"
            />
          </div>
        </div>

        <div class="text-caption font-weight-medium text-truncate text-grey-lighten-1">
          {{ item.url }}
        </div>

        <div class="text-caption text-grey-darken-1 mt-1">
          {{ formatDate(item.created_at) }}
        </div>
      </v-card>
    </v-list>
  </v-navigation-drawer>
</template>

<script setup>
import { ref, watch } from "vue";
import { api } from "@/api/client";
import { store, loadHistory } from "@/stores/appState";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const visible = ref(props.modelValue);
watch(() => props.modelValue, (val) => (visible.value = val));
watch(visible, (val) => emit("update:modelValue", val));

function getMethodColor(method) {
  switch (method?.toUpperCase()) {
    case "GET": return "emerald";
    case "POST": return "amber-darken-2";
    case "PUT": return "indigo";
    case "PATCH": return "cyan";
    case "DELETE": return "red";
    default: return "grey";
  }
}

function getStatusColor(code) {
  if (code >= 200 && code < 300) return "emerald";
  if (code >= 300 && code < 400) return "amber";
  if (code >= 400 && code < 500) return "orange-darken-1";
  return "red";
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function loadHistoryItem(item) {
  store.currentRequest.method = item.method;
  store.currentRequest.url = item.url;
  store.currentRequest.body = item.request_body || "";
  store.lastResponse = {
    execution_id: item.id,
    status_code: item.status_code,
    response_time_ms: item.response_time_ms,
    response_headers: item.response_headers || {},
    response_body: item.response_body,
    assertion_results: item.assertion_results || [],
    error_message: item.error_message,
  };
  visible.value = false;
}

async function deleteHistoryItem(id) {
  try {
    await api.deleteHistoryItem(id);
    await loadHistory();
  } catch (err) {
    alert("Failed to delete history item: " + (err.response?.data?.detail || err.message));
  }
}
</script>

<style scoped>
.history-drawer {
  background-color: #111827 !important;
}
.history-card {
  cursor: pointer;
  background-color: #1e293b;
  border-color: rgba(255, 255, 255, 0.08) !important;
}
.history-card:hover {
  border-color: #6366f1 !important;
}
</style>

