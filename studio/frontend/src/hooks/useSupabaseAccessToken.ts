"use client";

import { useEffect, useState } from "react";

import { getBrowserSupabaseClient } from "@/lib/supabase/browser";

interface SupabaseAccessTokenState {
  isLoading: boolean;
  token: string | null;
}

export const useSupabaseAccessToken = (): SupabaseAccessTokenState => {
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const supabase = getBrowserSupabaseClient();

    const loadSession = async (): Promise<void> => {
      const { data } = await supabase.auth.getSession();
      if (!isMounted) {
        return;
      }

      setToken(data.session?.access_token ?? null);
      setIsLoading(false);
    };

    void loadSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!isMounted) {
        return;
      }

      setToken(session?.access_token ?? null);
      setIsLoading(false);
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, []);

  return {
    isLoading,
    token,
  };
};
