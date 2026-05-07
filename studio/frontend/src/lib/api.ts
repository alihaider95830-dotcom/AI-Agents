import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

import { env } from "@/lib/env";
import { getBrowserSupabaseClient } from "@/lib/supabase/browser";
import type { FinalReport, JobStatus } from "@/types/jobs";

export interface User {
  id: string;
  email: string;
  full_name: string;
  tier: "free" | "pro" | "agency";
  credits: number;
}

export const DEMO_LOGIN_EMAIL = "demo@studio.local";
export const DEMO_LOGIN_PASSWORD = "DemoPassword123!";
export const DEMO_ACCESS_TOKEN = "demo-access-token";
export const DEMO_USER: User = {
  id: "demo-user",
  email: DEMO_LOGIN_EMAIL,
  full_name: "Demo User",
  tier: "pro",
  credits: 999,
};

export const isDemoLoginCredentials = (
  email: string,
  password: string,
): boolean =>
  email.trim().toLowerCase() === DEMO_LOGIN_EMAIL &&
  password === DEMO_LOGIN_PASSWORD;

const isPlaceholderSupabaseConfig = (): boolean => {
  const url = env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  return (
    url.includes("example.supabase.co") ||
    url.includes("your-project.supabase.co") ||
    anonKey === "supabase-anon-key" ||
    anonKey === "replace_me"
  );
};

const throwSupabaseSetupError = (): never => {
  throw new Error(
    "Supabase is not configured for this frontend yet. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to real Supabase project values, then restart the dev server.",
  );
};

interface AuthResponse {
  access_token: string;
  token_type: string;
}

interface ApiErrorPayload {
  detail?: string;
  message?: string;
}

interface JobCreateResponse {
  job_id: string;
  status: string;
  credits_deducted: number;
}

export const AUTH_TOKEN_STORAGE_KEY = "ai-report-token";

export const redirectToLogin = (): void => {
  if (typeof window === "undefined") {
    return;
  }

  if (window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
};

const getStoredToken = (): string | null => {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
};

export const extractApiErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError<ApiErrorPayload>(error)) {
    const payload = error.response?.data;
    return (
      payload?.detail ??
      payload?.message ??
      error.message ??
      "Something went wrong."
    );
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong.";
};

export const api = axios.create({
  baseURL: env.NEXT_PUBLIC_API_URL,
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const token = getStoredToken();
    if (!token) {
      return config;
    }

    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;

    return config;
  },
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorPayload>) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
      redirectToLogin();
    }

    return Promise.reject(error);
  },
);

export const authApi = {
  register: async (
    email: string,
    password: string,
    full_name: string,
  ): Promise<{ access_token: string }> => {
    try {
      if (isPlaceholderSupabaseConfig()) {
        throwSupabaseSetupError();
      }

      const supabase = getBrowserSupabaseClient();
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name,
          },
        },
      });

      if (error) {
        throw new Error(error.message);
      }

      const access_token = data.session?.access_token;
      if (!access_token) {
        throw new Error(
          "Account created, but no session was returned. Check your email and sign in again.",
        );
      }

      return { access_token };
    } catch (error) {
      throw new Error(
        error instanceof Error ? error.message : "Something went wrong.",
      );
    }
  },
  login: async (
    email: string,
    password: string,
  ): Promise<{ access_token: string }> => {
    try {
      if (isPlaceholderSupabaseConfig()) {
        throwSupabaseSetupError();
      }

      const supabase = getBrowserSupabaseClient();
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        throw new Error(error.message);
      }

      const access_token = data.session?.access_token;
      if (!access_token) {
        throw new Error("Unable to create a session right now.");
      }

      return { access_token };
    } catch (error) {
      throw new Error(
        error instanceof Error ? error.message : "Something went wrong.",
      );
    }
  },
  me: async (): Promise<User> => {
    try {
      const { data } = await api.get<User>("/auth/me");
      return data;
    } catch (error) {
      throw new Error(extractApiErrorMessage(error));
    }
  },
};

export const jobsApi = {
  create: async (
    topic: string,
    report_type: string,
  ): Promise<JobCreateResponse> => {
    try {
      const { data } = await api.post<JobCreateResponse>("/jobs/create", {
        topic,
        report_type,
      });

      return data;
    } catch (error) {
      throw new Error(extractApiErrorMessage(error));
    }
  },
  getStatus: async (job_id: string): Promise<JobStatus> => {
    try {
      const { data } = await api.get<JobStatus>(`/jobs/${job_id}/status`);
      return data;
    } catch (error) {
      throw new Error(extractApiErrorMessage(error));
    }
  },
};

export const reportsApi = {
  get: async (report_id: string): Promise<FinalReport> => {
    try {
      const { data } = await api.get<FinalReport>(`/reports/${report_id}`);
      return data;
    } catch (error) {
      throw new Error(extractApiErrorMessage(error));
    }
  },
};
