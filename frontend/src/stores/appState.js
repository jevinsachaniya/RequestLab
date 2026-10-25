import { reactive, computed } from "vue";
import { api } from "@/api/client";

export const store = reactive({
  // Theme State
  theme: localStorage.getItem("api_sentinel_theme") || "dark",

  // Navigation / View State
  activeView: "workspace", // "workspace" | "dashboard" | "history"
  searchFilter: "",

  // User & Auth State
  user: null,
  token: localStorage.getItem("api_sentinel_token") || null,

  // Data Collections & History
  collections: [],
  history: [],
  historyTotal: 0,
  historyPage: 1,
  isLoadingHistory: false,
  isSendingRequest: false,
  isLoadingCollections: false,

  // Active Request in Workspace
  currentRequest: {
    id: null,
    collectionId: null,
    name: "Untitled Request",
    method: "GET",
    url: "https://httpbin.org/get",
    paramsList: [{ key: "", value: "", enabled: true }],
    headersList: [{ key: "Accept", value: "application/json", enabled: true }],
    body: "",
    assertions: [
      { type: "status_code", operator: "equals", expected: 200 },
      { type: "response_time", operator: "less_than", expected: 2000 },
    ],
    followRedirects: false,
    auth: {
      type: "none", // "none" | "bearer" | "basic" | "apikey"
      bearerToken: "",
      basicUser: "",
      basicPass: "",
      apiKeyName: "X-API-Key",
      apiKeyValue: "",
      apiKeyLocation: "header", // "header" | "query"
    },
  },

  // Last execution response
  lastResponse: null,

  // Global toast / snackbar notification
  toast: {
    show: false,
    message: "",
    color: "success",
  },
});

export const isAuthenticated = computed(() => !!store.token && !!store.user);

export function showToast(message, color = "success") {
  store.toast.message = message;
  store.toast.color = color;
  store.toast.show = true;
}

export async function checkAuth() {
  if (!store.token) {
    store.user = null;
    return false;
  }
  try {
    const res = await api.getMe();
    store.user = res.data;
    await loadCollections();
    return true;
  } catch (err) {
    logout();
    return false;
  }
}

export function logout() {
  store.token = null;
  store.user = null;
  store.collections = [];
  store.history = [];
  store.historyTotal = 0;
  localStorage.removeItem("api_sentinel_token");
  showToast("You have been signed out.", "info");
}

export async function loadCollections() {
  if (!store.token) return;
  store.isLoadingCollections = true;
  try {
    const res = await api.getCollections(1, 100);
    const cols = res.data.items || [];

    // Fetch child saved requests for each collection
    for (const col of cols) {
      try {
        const reqRes = await api.getCollectionRequests(col.id, 1, 100);
        col.requests = reqRes.data.items || [];
      } catch (e) {
        col.requests = [];
      }
    }
    store.collections = cols;
  } catch (err) {
    console.error("Failed to load collections:", err);
  } finally {
    store.isLoadingCollections = false;
  }
}

export async function loadHistory(page = 1, statusCode = null, savedRequestId = null) {
  if (!store.token) return;
  store.isLoadingHistory = true;
  store.historyPage = page;
  try {
    const res = await api.getHistory(page, 20, savedRequestId, statusCode);
    store.history = res.data.items || [];
    store.historyTotal = res.data.total || 0;
  } catch (err) {
    console.error("Failed to load history:", err);
  } finally {
    store.isLoadingHistory = false;
  }
}

export function selectSavedRequest(req) {
  store.currentRequest.id = req.id;
  store.currentRequest.collectionId = req.collection_id;
  store.currentRequest.name = req.name;
  store.currentRequest.method = req.method;
  store.currentRequest.url = req.url;
  store.currentRequest.body = req.body || "";
  store.currentRequest.assertions = req.assertions || [];
  store.currentRequest.followRedirects = req.follow_redirects || false;

  // Convert params dict to array for UI
  const pList = [];
  if (req.params && typeof req.params === "object") {
    for (const [k, v] of Object.entries(req.params)) {
      pList.push({ key: k, value: String(v), enabled: true });
    }
  }
  if (pList.length === 0) pList.push({ key: "", value: "", enabled: true });
  store.currentRequest.paramsList = pList;

  // Convert headers dict to array for UI
  const hList = [];
  if (req.headers && typeof req.headers === "object") {
    for (const [k, v] of Object.entries(req.headers)) {
      // Check if header is Basic or Bearer auth
      if (k.toLowerCase() === "authorization") {
        const val = String(v);
        if (val.startsWith("Bearer ")) {
          store.currentRequest.auth.type = "bearer";
          store.currentRequest.auth.bearerToken = val.replace("Bearer ", "");
        } else if (val.startsWith("Basic ")) {
          store.currentRequest.auth.type = "basic";
          try {
            const decoded = atob(val.replace("Basic ", ""));
            const [u, p] = decoded.split(":");
            store.currentRequest.auth.basicUser = u || "";
            store.currentRequest.auth.basicPass = p || "";
          } catch {
            // Keep header as is
          }
        }
      }
      hList.push({ key: k, value: String(v), enabled: true });
    }
  }
  if (hList.length === 0) hList.push({ key: "Accept", value: "application/json", enabled: true });
  store.currentRequest.headersList = hList;

  // Switch to workspace view when selecting a request
  store.activeView = "workspace";
}

export function resetCurrentRequest() {
  store.currentRequest.id = null;
  store.currentRequest.collectionId = null;
  store.currentRequest.name = "Untitled Request";
  store.currentRequest.method = "GET";
  store.currentRequest.url = "https://httpbin.org/get";
  store.currentRequest.paramsList = [{ key: "", value: "", enabled: true }];
  store.currentRequest.headersList = [{ key: "Accept", value: "application/json", enabled: true }];
  store.currentRequest.body = "";
  store.currentRequest.assertions = [
    { type: "status_code", operator: "equals", expected: 200 },
    { type: "response_time", operator: "less_than", expected: 2000 },
  ];
  store.currentRequest.followRedirects = false;
  store.currentRequest.auth = {
    type: "none",
    bearerToken: "",
    basicUser: "",
    basicPass: "",
    apiKeyName: "X-API-Key",
    apiKeyValue: "",
    apiKeyLocation: "header",
  };
  store.lastResponse = null;
  store.activeView = "workspace";
}

// Compute response size in human readable format
export function formatByteSize(bytes) {
  if (!bytes || bytes <= 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

// Calculate byte size of any string
export function getPayloadByteSize(content) {
  if (!content) return 0;
  return new Blob([content]).size;
}

// Parse Set-Cookie header into structured table rows
export function parseResponseCookies(headers) {
  if (!headers || typeof headers !== "object") return [];
  const cookies = [];
  for (const [key, val] of Object.entries(headers)) {
    if (key.toLowerCase() === "set-cookie") {
      const parts = String(val).split(";").map((p) => p.trim());
      const [nameVal, ...attrs] = parts;
      const [cName, ...cValParts] = nameVal.split("=");
      cookies.push({
        name: cName,
        value: cValParts.join("="),
        attributes: attrs.join("; "),
      });
    }
  }
  return cookies;
}
