import axios, { AxiosError, AxiosRequestConfig } from "axios";
import type { ApiResponse } from "@/types";

// All requests go to Next.js BFF — tokens never touch client JS
export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

// Sem isso, o Content-Type: application/json fixo acima "vence" o FormData nos
// uploads (hero/galeria do CMS, capa do blog) — axios só troca automaticamente
// o header por multipart/form-data quando ele já começa como "multipart/form-data"
// sem boundary; um Content-Type explicitamente diferente (nosso caso) ele deixa
// como está. Resultado sem isto: o Django recebe Content-Type: application/json
// com corpo multipart e responde 415 Unsupported Media Type. Ver node_modules/
// axios/lib/adapters/fetch.js (bloco "delete it so fetch can set it correctly").
api.interceptors.request.use((config) => {
  if (config.data instanceof FormData) {
    config.headers.delete("Content-Type");
  }
  return config;
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
