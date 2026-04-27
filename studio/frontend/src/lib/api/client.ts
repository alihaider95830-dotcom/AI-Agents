import { env } from "@/lib/env";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

const API_PREFIX = "/api/v1";

const extractErrorMessage = async (response: Response): Promise<string> => {
  try {
    const payload = (await response.json()) as {
      detail?: string;
      error?: string;
      message?: string;
    };

    return (
      payload.error ??
      payload.detail ??
      payload.message ??
      response.statusText ??
      "Request failed."
    );
  } catch {
    return response.statusText || "Request failed.";
  }
};

export const buildApiUrl = (path: string): string =>
  new URL(`${API_PREFIX}${path}`, env.NEXT_PUBLIC_API_URL).toString();

export const apiRequest = async <T>(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<T> => {
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${token}`);

  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(buildApiUrl(path), {
    ...init,
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    throw new ApiError(await extractErrorMessage(response), response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
};
