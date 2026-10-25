import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export const apiClient = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 25000,
});

// Attach JWT access token to every outgoing request if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("api_sentinel_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle expired or invalid tokens automatically
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Do not clear on auth/login failure
      if (!error.config.url.includes("/auth/login") && !error.config.url.includes("/auth/register")) {
        localStorage.removeItem("api_sentinel_token");
        window.dispatchEvent(new CustomEvent("api-sentinel-unauthorized"));
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  // Auth
  register: (email, password) => apiClient.post("/auth/register", { email, password }),
  login: (email, password) => apiClient.post("/auth/login", { email, password }),
  getMe: () => apiClient.get("/auth/me"),

  // Collections
  getCollections: (page = 1, pageSize = 50) =>
    apiClient.get(`/collections/?page=${page}&page_size=${pageSize}`),
  createCollection: (name, description) =>
    apiClient.post("/collections/", { name, description }),
  updateCollection: (id, name, description) =>
    apiClient.put(`/collections/${id}`, { name, description }),
  deleteCollection: (id) => apiClient.delete(`/collections/${id}`),

  // Saved Requests
  getCollectionRequests: (collectionId, page = 1, pageSize = 50) =>
    apiClient.get(`/collections/${collectionId}/requests?page=${page}&page_size=${pageSize}`),
  createSavedRequest: (collectionId, data) =>
    apiClient.post(`/collections/${collectionId}/requests`, data),
  getSavedRequest: (id) => apiClient.get(`/requests/${id}`),
  updateSavedRequest: (id, data) => apiClient.put(`/requests/${id}`, data),
  deleteSavedRequest: (id) => apiClient.delete(`/requests/${id}`),

  // Request Execution
  executeTemporary: (data) => apiClient.post("/requests/execute", data),
  executeSaved: (requestId) => apiClient.post(`/requests/${requestId}/execute`),

  // Execution History
  getHistory: (page = 1, pageSize = 20, savedRequestId = null, statusCode = null) => {
    let url = `/history/?page=${page}&page_size=${pageSize}`;
    if (savedRequestId) url += `&saved_request_id=${savedRequestId}`;
    if (statusCode) url += `&status_code=${statusCode}`;
    return apiClient.get(url);
  },
  getHistoryDetail: (id) => apiClient.get(`/history/${id}`),
  deleteHistoryItem: (id) => apiClient.delete(`/history/${id}`),
};
