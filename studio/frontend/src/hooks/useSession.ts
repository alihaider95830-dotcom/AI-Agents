"use client";

import { useEffect } from "react";

import { useAuthStore } from "@/store/authStore";

interface SessionState {
  user: ReturnType<typeof useAuthStore.getState>["user"];
  token: ReturnType<typeof useAuthStore.getState>["token"];
  isLoading: boolean;
  isAuthenticated: boolean;
  logout: () => void;
}

export const useSession = (): SessionState => {
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);
  const isLoading = useAuthStore((state) => state.isLoading);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const logout = useAuthStore((state) => state.logout);
  const initAuth = useAuthStore((state) => state.initAuth);

  useEffect(() => {
    void initAuth();
  }, [initAuth]);

  return {
    user,
    token,
    isLoading,
    isAuthenticated,
    logout,
  };
};
