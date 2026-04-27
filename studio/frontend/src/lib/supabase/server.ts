import { cookies } from "next/headers";

import { extractSupabaseAccessToken } from "@/lib/supabase/token";

export const getServerSupabaseAccessToken = async (): Promise<string | null> => {
  const cookieStore = await cookies();

  return extractSupabaseAccessToken(
    cookieStore.getAll().map((cookie) => ({
      name: cookie.name,
      value: cookie.value,
    })),
  );
};
