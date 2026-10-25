<template>
  <v-dialog v-model="visible" max-width="400" persistent>
    <div class="auth-modal-card pa-4 rounded border">
      <!-- Top Brand & Close Button -->
      <div class="d-flex align-center justify-space-between pb-3 mb-3 border-b">
        <RequestLabLogo :size="26" :show-tagline="true" />
        <button
          type="button"
          class="modal-close-btn"
          @click="visible = false"
        >
          <v-icon size="16">mdi-close</v-icon>
        </button>
      </div>

      <!-- Contextual Prompt Message (if triggered from Guest save/history) -->
      <div
        v-if="promptMessage"
        class="auth-prompt-callout pa-2.5 rounded mb-3 text-caption d-flex align-center"
      >
        <v-icon size="15" color="primary" class="mr-1.5 flex-shrink-0">mdi-information-outline</v-icon>
        <span>{{ promptMessage }}</span>
      </div>

      <!-- Segmented Tab Switcher -->
      <div class="auth-tab-bar d-flex align-center mb-3 border-b">
        <button
          type="button"
          :class="['auth-tab-btn flex-grow-1 text-caption font-weight-medium pb-2', { active: tab === 'login' }]"
          @click="tab = 'login'"
        >
          Sign In
        </button>
        <button
          type="button"
          :class="['auth-tab-btn flex-grow-1 text-caption font-weight-medium pb-2', { active: tab === 'register' }]"
          @click="tab = 'register'"
        >
          Create Account
        </button>
      </div>

      <!-- Error Message Banner -->
      <div v-if="errorMessage" class="error-banner pa-2 rounded mb-3 d-flex align-center justify-space-between text-caption">
        <div class="d-flex align-center mr-2">
          <v-icon size="14" color="error" class="mr-1.5 flex-shrink-0">mdi-alert-circle-outline</v-icon>
          <span>{{ errorMessage }}</span>
        </div>
        <button type="button" class="clear-err-btn" @click="errorMessage = ''">
          <v-icon size="12">mdi-close</v-icon>
        </button>
      </div>

      <!-- Success Message Banner -->
      <div v-if="successMessage" class="success-banner pa-2 rounded mb-3 d-flex align-center text-caption">
        <v-icon size="14" color="success" class="mr-1.5 flex-shrink-0">mdi-check-circle-outline</v-icon>
        <span>{{ successMessage }}</span>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="mb-3">
          <label class="dev-field-label">EMAIL ADDRESS</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="developer@example.com"
            class="dev-input w-100"
            autofocus
          />
        </div>

        <div class="mb-3">
          <div class="d-flex align-center justify-space-between mb-1">
            <label class="dev-field-label mb-0">PASSWORD</label>
            <span class="password-hint text-muted">Min 8 chars</span>
          </div>
          <div class="password-input-wrap d-flex align-center">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              minlength="8"
              placeholder="••••••••"
              class="dev-input flex-grow-1 border-0"
            />
            <button
              type="button"
              class="pwd-toggle-btn px-2 text-muted"
              @click="showPassword = !showPassword"
            >
              <v-icon size="15">{{ showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline' }}</v-icon>
            </button>
          </div>
        </div>

        <button
          type="submit"
          class="dev-primary-btn w-100 py-2 text-caption font-weight-medium d-flex align-center justify-center mt-3"
          :disabled="loading"
        >
          <v-progress-circular
            v-if="loading"
            indeterminate
            size="14"
            width="2"
            color="white"
            class="mr-2"
          />
          <span>{{ tab === 'login' ? 'Sign In to Workspace' : 'Create Free Account' }}</span>
        </button>

        <!-- Continue as Guest link -->
        <div class="text-center mt-3">
          <button
            type="button"
            class="guest-return-btn text-caption text-secondary"
            @click="visible = false"
          >
            ← Continue testing in Guest Mode
          </button>
        </div>
      </form>
    </div>
  </v-dialog>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from "vue";
import RequestLabLogo from "@/components/RequestLabLogo.vue";
import { api } from "@/api/client";
import { store, loadCollections, loadHistory, showToast } from "@/stores/appState";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  promptMessage: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue", "authenticated"]);

const visible = ref(props.modelValue);
watch(() => props.modelValue, (val) => (visible.value = val));
watch(visible, (val) => emit("update:modelValue", val));

const tab = ref("login");
const email = ref("");
const password = ref("");
const showPassword = ref(false);
const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

async function handleSubmit() {
  errorMessage.value = "";
  successMessage.value = "";
  loading.value = true;

  try {
    if (tab.value === "register") {
      await api.register(email.value, password.value);
      successMessage.value = "Account created! Signing you in...";
    }

    // Login
    const loginRes = await api.login(email.value, password.value);
    const token = loginRes.data.access_token;
    localStorage.setItem("api_sentinel_token", token);
    store.token = token;

    const meRes = await api.getMe();
    store.user = meRes.data;

    await loadCollections();
    await loadHistory();
    visible.value = false;
    showToast(`Welcome back, ${store.user.email}!`, "success");
    emit("authenticated");
  } catch (err) {
    if (err.response && err.response.data) {
      const d = err.response.data.detail;
      if (typeof d === "string") {
        errorMessage.value = d;
      } else if (Array.isArray(d)) {
        errorMessage.value = d.map((x) => x.msg || JSON.stringify(x)).join("; ");
      } else if (typeof d === "object") {
        errorMessage.value = JSON.stringify(d);
      } else {
        errorMessage.value = `Server error (${err.response.status}).`;
      }
    } else {
      errorMessage.value =
        "Failed to connect to backend server. Make sure FastAPI is running on port 8000.";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.auth-modal-card {
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

.auth-prompt-callout {
  background: var(--bg-surface);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.auth-tab-bar {
  border-color: var(--border-color) !important;
  gap: 12px;
}

.auth-tab-btn {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  cursor: pointer;
  text-align: center;
  transition: all 0.15s ease;
}

.auth-tab-btn:hover {
  color: var(--text-primary);
}

.auth-tab-btn.active {
  color: var(--text-primary);
  border-bottom-color: var(--primary);
  font-weight: 700 !important;
}

.error-banner {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.25);
  color: #ef4444;
}

.clear-err-btn {
  background: transparent;
  border: none;
  color: #ef4444;
  cursor: pointer;
}

.success-banner {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  color: #10b981;
}

.dev-field-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.password-hint {
  font-size: 10px;
}

.dev-input {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 6px 10px;
  font-size: 12px;
  border-radius: 4px;
  outline: none;
}

.dev-input:focus {
  border-color: var(--primary);
}

.password-input-wrap {
  background: var(--bg-input);
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.password-input-wrap:focus-within {
  border-color: var(--primary);
}

.pwd-toggle-btn {
  background: transparent;
  border: none;
  cursor: pointer;
}

.dev-primary-btn {
  background: var(--primary);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.dev-primary-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.dev-primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.guest-return-btn {
  background: transparent;
  border: none;
  cursor: pointer;
}

.guest-return-btn:hover {
  text-decoration: underline;
  color: var(--text-primary);
}
</style>
