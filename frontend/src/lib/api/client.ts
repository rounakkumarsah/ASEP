import axios from "axios";

// Assume the FastAPI backend is running on port 8000
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor for attaching JWT tokens
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("asep_access_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response interceptor for handling 401s (Future: refresh token logic)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Future: Implement refresh token logic here
      // For now, clear token and optionally redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("asep_access_token");
        // We'll handle redirecting in the auth provider or middleware
      }
    }
    return Promise.reject(error);
  }
);
