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

// Helper to parse JWT payload without external dependencies
export function parseJwt(token: string): { exp?: number; [key: string]: unknown } | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    let decodedStr: string;
    if (typeof atob === "function") {
      decodedStr = atob(base64);
    } else if (typeof Buffer !== "undefined") {
      decodedStr = Buffer.from(base64, "base64").toString("binary");
    } else {
      return null;
    }
    try {
      const jsonPayload = decodeURIComponent(
        decodedStr
          .split("")
          .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
          .join("")
      );
      return JSON.parse(jsonPayload);
    } catch {
      return JSON.parse(decodedStr);
    }
  } catch {
    return null;
  }
}

// Proactive expiration check (threshold in seconds, default 30s)
export function isTokenExpiringSoon(token: string, thresholdSeconds: number = 30): boolean {
  const payload = parseJwt(token);
  if (!payload || typeof payload.exp !== "number") return false;
  const currentTime = Math.floor(Date.now() / 1000);
  return payload.exp - currentTime <= thresholdSeconds;
}

// Synchronize tokens across localStorage and sessionStorage so stale tokens never linger
export function syncAuthTokens(
  accessToken: string,
  newRefreshToken?: string,
  isRemembered?: boolean
): void {
  if (typeof window === "undefined") return;

  if (isRemembered === undefined) {
    isRemembered =
      !!localStorage.getItem("asep_user_session") ||
      (!sessionStorage.getItem("asep_user_session") &&
        !!localStorage.getItem("asep_auth_token"));
  }

  const primaryStorage = isRemembered ? localStorage : sessionStorage;
  const secondaryStorage = isRemembered ? sessionStorage : localStorage;

  primaryStorage.setItem("asep_auth_token", accessToken);
  secondaryStorage.removeItem("asep_auth_token");

  if (newRefreshToken) {
    primaryStorage.setItem("asep_refresh_token", newRefreshToken);
    secondaryStorage.removeItem("asep_refresh_token");
  }
}

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

// Proactively or reactively refresh the access token and synchronize storage
export async function refreshAccessToken(): Promise<string | null> {
  if (isRefreshing) {
    return new Promise<string | null>((resolve, reject) => {
      failedQueue.push({
        resolve: (token) => resolve(token as string | null),
        reject,
      });
    });
  }

  isRefreshing = true;

  try {
    const storedRefreshToken =
      typeof window !== "undefined"
        ? localStorage.getItem("asep_refresh_token") ||
          sessionStorage.getItem("asep_refresh_token")
        : null;

    const isRemembered =
      typeof window !== "undefined" && !!localStorage.getItem("asep_user_session");

    const payload: Record<string, unknown> = {
      remember_me: isRemembered,
    };
    if (storedRefreshToken) {
      payload.refresh_token = storedRefreshToken;
    }

    const refreshResponse = await axios.post(
      `${API_URL}/api/v1/auth/refresh`,
      payload,
      { withCredentials: true }
    );
    const { access_token, refresh_token: newRefreshToken } = refreshResponse.data;

    syncAuthTokens(access_token, newRefreshToken, isRemembered);

    processQueue(null, access_token);
    return access_token;
  } catch (refreshError: unknown) {
    processQueue(refreshError, null);
    const errStatus = (refreshError as { response?: { status?: number } })?.response?.status;
    if ((errStatus === 400 || errStatus === 401) && typeof window !== "undefined") {
      window.dispatchEvent(new Event("auth:unauthorized"));
    }
    throw refreshError;
  } finally {
    isRefreshing = false;
  }
}

// Request interceptor to attach token from localStorage or sessionStorage if present
apiClient.interceptors.request.use(async (config) => {
  if (typeof window !== "undefined") {
    // Check if header is already set before overriding (e.g. from retry handler)
    const hasAuthHeader =
      typeof config.headers.has === "function"
        ? config.headers.has("Authorization")
        : Boolean(config.headers["Authorization"] || config.headers["authorization"]);

    let token =
      localStorage.getItem("asep_auth_token") ||
      sessionStorage.getItem("asep_auth_token");

    const isAuthEndpoint =
      config.url?.includes("/api/v1/auth/refresh") ||
      config.url?.includes("/api/v1/auth/logout");

    // Proactive expiry check: if JWT is within 30s of expiring, refresh proactively.
    if (token && !isAuthEndpoint && isTokenExpiringSoon(token, 30)) {
      try {
        const refreshedToken = await refreshAccessToken();
        if (refreshedToken) {
          token = refreshedToken;
        }
      } catch {
        // If proactive refresh fails, fall back to current token and let response interceptor handle 401
      }
    }

    if (!hasAuthHeader && token) {
      if (typeof config.headers.set === "function") {
        config.headers.set("Authorization", `Bearer ${token}`);
      } else {
        config.headers["Authorization"] = `Bearer ${token}`;
      }
    }
  }
  return config;
});

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
      originalRequest._retry = true;

      try {
        const accessToken = await refreshAccessToken();
        if (accessToken) {
          if (typeof originalRequest.headers.set === "function") {
            originalRequest.headers.set("Authorization", "Bearer " + accessToken);
          } else {
            originalRequest.headers["Authorization"] = "Bearer " + accessToken;
          }
        }
        return apiClient(originalRequest);
      } catch (refreshError: unknown) {
        return Promise.reject(new UnauthorizedError(message, data));
      }
    }

    const isSilent = Boolean(
      (originalRequest as unknown as { silent?: boolean; skipGlobalError?: boolean })?.silent ||
      (originalRequest as unknown as { silent?: boolean; skipGlobalError?: boolean })?.skipGlobalError ||
      originalRequest.headers?.["x-silent-error"] === "true"
    );

    if (typeof window !== "undefined" && status !== 401 && !isSilent) {
      window.dispatchEvent(
        new CustomEvent("api:error", {
          detail: {
            message: message,
            status: status,
            retry: () => apiClient(originalRequest),
          },
        })
      );
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
