"use client";

import { create } from "zustand";

import {
  AUTH_TOKEN_STORAGE_KEY,
  DEMO_ACCESS_TOKEN,
  DEMO_USER,
  authApi,
  redirectToLogin,
  isDemoLoginCredentials,
  type User,
} from "@/lib/api";

interface AuthStoreState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  adjustCredits: (delta: number) => void;
  login: (email: string, password: string) => Promise<void>;
  register: (
    email: string,
    password: string,
    full_name: string,
  ) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  initAuth: () => Promise<void>;
}

const setStoredToken = (token: string | null): void => {
  if (typeof window === "undefined") {
    return;
  }

  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
    return;
  }

  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
};

export const useAuthStore = create<AuthStoreState>((set, get) => ({
  user: null,
  token: null,
  isLoading: true,
  isAuthenticated: false,
  adjustCredits: (delta) => {
    const user = get().user;
    if (!user) {
      return;
    }

    set({
      user: {
        ...user,
        credits: Math.max(user.credits + delta, 0),
      },
    });
  },
  login: async (email, password) => {
    set({ isLoading: true });

    try {
      if (isDemoLoginCredentials(email, password)) {
        setStoredToken(DEMO_ACCESS_TOKEN);
        set({
          user: DEMO_USER,
          token: DEMO_ACCESS_TOKEN,
          isAuthenticated: true,
        });
        return;
      }

      const { access_token } = await authApi.login(email, password);
      setStoredToken(access_token);
      set({
        token: access_token,
        isAuthenticated: true,
      });
      await get().fetchUser();
    } catch (error) {
      setStoredToken(null);
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },
  register: async (email, password, full_name) => {
    set({ isLoading: true });

    try {
      const { access_token } = await authApi.register(email, password, full_name);
      setStoredToken(access_token);
      set({
        token: access_token,
        isAuthenticated: true,
      });
      await get().fetchUser();
    } catch (error) {
      setStoredToken(null);
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },
  logout: () => {
    setStoredToken(null);
    set({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
    });
    redirectToLogin();
  },
  fetchUser: async () => {
    set({ isLoading: true });

    try {
      if (get().token === DEMO_ACCESS_TOKEN) {
        set({
          user: DEMO_USER,
          isAuthenticated: true,
        });
        return;
      }

      const user = await authApi.me();
      set({
        user,
        isAuthenticated: Boolean(get().token),
      });
    } catch (error) {
      setStoredToken(null);
      set({
        user: null,
        token: null,
        isAuthenticated: false,
      });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },
  initAuth: async () => {
    if (typeof window === "undefined") {
      set({ isLoading: false });
      return;
    }

    set({ isLoading: true });

    const storedToken = window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (!storedToken) {
      set({
        user: null,
        token: null,
        isLoading: false,
        isAuthenticated: false,
      });
      return;
    }

    if (storedToken === DEMO_ACCESS_TOKEN) {
      set({
        user: DEMO_USER,
        token: DEMO_ACCESS_TOKEN,
        isLoading: false,
        isAuthenticated: true,
      });
      return;
    }

    set({
      token: storedToken,
      isAuthenticated: true,
    });

    try {
      await get().fetchUser();
    } catch {
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      });
    } finally {
      set({ isLoading: false });
    }
  },
}));
