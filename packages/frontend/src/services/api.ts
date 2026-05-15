import axios from "axios";

import { useAuthStore } from "../stores/authStore";
import type { MeResponse, RegisterRequestBody, RegisterResponse, TokenPairResponse } from "../types/auth";

/** Shared JSON client (`/api/...`). */
export const api = axios.create({
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) {
    throw new Error("Missing refresh token");
  }
  if (!refreshPromise) {
    refreshPromise = axios
      .post<{ access: string }>("/api/auth/refresh/", { refresh: refreshToken })
      .then((res) => {
        useAuthStore.getState().setAccessToken(res.data.access);
        return res.data.access;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const cfg = error.config;
    const status = error.response?.status as number | undefined;
    if (!cfg || cfg._retry === true || status !== 401) {
      throw error;
    }

    const url = String(cfg.url ?? "");
    if (url.includes("/api/auth/login/") || url.includes("/api/auth/register/") || url.includes("/api/auth/refresh/") || url.includes("/api/auth/logout/")) {
      throw error;
    }

    cfg._retry = true;
    try {
      const next = await refreshAccessToken();
      cfg.headers.Authorization = `Bearer ${next}`;
      return api.request(cfg);
    } catch {
      useAuthStore.getState().clearSession();
      if (typeof window !== "undefined") {
        const p = window.location.pathname;
        if (p !== "/login" && p !== "/register") {
          window.location.assign("/login");
        }
      }
      throw error;
    }
  },
);

export async function loginRequest(username: string, password: string) {
  const { data } = await axios.post<TokenPairResponse>(
    "/api/auth/login/",
    { username, password },
    {
      headers: { "Content-Type": "application/json", Accept: "application/json" },
    },
  );
  useAuthStore.getState().setTokens(data.access, data.refresh);
}

export async function registerRequest(body: RegisterRequestBody) {
  const { data } = await axios.post<RegisterResponse>("/api/auth/register/", body, {
    headers: { "Content-Type": "application/json", Accept: "application/json" },
  });
  useAuthStore.getState().setTokens(data.access, data.refresh);
  useAuthStore.getState().setUser(data.user);
}

export async function fetchMe(): Promise<MeResponse> {
  const { data } = await api.get<MeResponse>("/api/auth/me/");
  useAuthStore.getState().setUser(data);
  return data;
}

export async function logoutRequest() {
  const refreshToken = useAuthStore.getState().refreshToken;
  try {
    if (refreshToken) {
      await api.post("/api/auth/logout/", { refresh: refreshToken });
    }
  } finally {
    useAuthStore.getState().clearSession();
  }
}
