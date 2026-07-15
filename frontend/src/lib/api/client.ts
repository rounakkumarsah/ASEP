import axios, { AxiosError } from "axios";
import { env } from "../config/env";
import { 
  ApiError, 
  UnauthorizedError, 
  ForbiddenError, 
  NotFoundError, 
  ValidationError, 
  ServerError 
} from "./errors";

const API_URL = env.NEXT_PUBLIC_API_URL;

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000, // 10 second timeout
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

// Response interceptor for unified error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (!error.response) {
      // Network error or timeout
      return Promise.reject(new ApiError(0, error.message));
    }

    const { status, data } = error.response;
    const message = (data as Record<string, unknown>)?.message as string || error.message;

    switch (status) {
      case 401:
        if (typeof window !== "undefined") {
          localStorage.removeItem("asep_access_token");
          // The AuthProvider and Route Guards will automatically detect the missing token 
          // and redirect to /login on next render or location change.
          window.dispatchEvent(new Event("auth:unauthorized"));
        }
        return Promise.reject(new UnauthorizedError(message, data));
      case 403:
        return Promise.reject(new ForbiddenError(message, data));
      case 404:
        return Promise.reject(new NotFoundError(message, data));
      case 422:
        return Promise.reject(new ValidationError(message, data));
      case 500:
      default:
        return Promise.reject(new ServerError(message, data));
    }
  }
);
