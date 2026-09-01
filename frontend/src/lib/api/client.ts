import axios, { AxiosError } from "axios";
import { env } from "../config/env";
import {
  ApiError,
  UnauthorizedError,
  ForbiddenError,
  NotFoundError,
  ValidationError,
  ServerError,
} from "./errors";

const API_URL = env.NEXT_PUBLIC_API_URL;

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 second timeout to handle Serverless cold starts
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // Enable cookie transmission across cross-origin requests
});

// Request interceptor to attach token from localStorage if present
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("asep_auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Flag to prevent multiple simultaneous refresh requests
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor for unified error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as import("axios").InternalAxiosRequestConfig & { _retry?: boolean };

    if (!error.response) {
      return Promise.reject(new ApiError(0, error.message));
    }

    const { status, data } = error.response;
    const message =
      ((data as Record<string, unknown>)?.detail as string) ||
      ((data as Record<string, unknown>)?.message as string) ||
      error.message;

    if (status === 401 && originalRequest && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (token) originalRequest.headers["Authorization"] = "Bearer " + token;
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshResponse = await axios.post(
          `${API_URL}/api/v1/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const { access_token } = refreshResponse.data;
        if (typeof window !== "undefined") {
          localStorage.setItem("asep_auth_token", access_token);
        }
        originalRequest.headers["Authorization"] = "Bearer " + access_token;
        processQueue(null, access_token);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("auth:unauthorized"));
        }
        return Promise.reject(new UnauthorizedError(message, data));
      } finally {
        isRefreshing = false;
      }
    }

    switch (status) {
      case 401:
        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("auth:unauthorized"));
        }
        return Promise.reject(new UnauthorizedError(message, data));
      case 403:
        return Promise.reject(new ForbiddenError(message, data));
      case 429:
        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("auth:rate_limit"));
        }
        return Promise.reject(new ApiError(429, message, data));
      case 404:
        return Promise.reject(new NotFoundError(message, data));
      case 422:
        return Promise.reject(new ValidationError(message, data));
      case 500:
      default:
        return Promise.reject(new ServerError(message, data));
    }
  },
);
