import axios, { AxiosError, AxiosRequestConfig } from "axios";
import type { ApiResponse } from "@/types";

// All requests go to Next.js BFF — tokens never touch client JS
export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// On 401 from BFF proxy routes, the session has fully expired (BFF already attempted refresh).
// Auth endpoints (/auth/*) returning 401 mean bad credentials — let them propagate as errors.
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const url = (error.config as AxiosRequestConfig)?.url ?? "";
    const isAuthEndpoint = url.startsWith("/auth/");
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry && !isAuthEndpoint) {
      original._retry = true;
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export function unwrap<T>(response: { data: ApiResponse<T> }): T {
  if (!response.data.success || response.data.data === null) {
    throw new Error(response.data.error?.message ?? "Unknown error");
  }
  return response.data.data;
}
