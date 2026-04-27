export interface CookieValue {
  name: string;
  value: string;
}

const jwtPattern = /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/;
const supabaseCookiePattern = /^sb-.*auth-token(?:\.\d+)?$/;

const decodeBase64Url = (value: string): string | null => {
  try {
    const normalizedValue = value.replace(/-/g, "+").replace(/_/g, "/");
    const paddingLength = (4 - (normalizedValue.length % 4 || 4)) % 4;
    const paddedValue = `${normalizedValue}${"=".repeat(paddingLength)}`;

    if (typeof window !== "undefined" && typeof window.atob === "function") {
      return window.atob(paddedValue);
    }

    return Buffer.from(paddedValue, "base64").toString("utf-8");
  } catch {
    return null;
  }
};

const extractAccessToken = (value: unknown, depth = 0): string | null => {
  if (value == null || depth > 6) {
    return null;
  }

  if (typeof value === "string") {
    const normalizedValue = value.trim();

    if (jwtPattern.test(normalizedValue)) {
      return normalizedValue;
    }

    if (normalizedValue.startsWith("base64-")) {
      const decodedValue = decodeBase64Url(normalizedValue.slice("base64-".length));
      if (decodedValue) {
        return extractAccessToken(decodedValue, depth + 1);
      }
    }

    try {
      return extractAccessToken(JSON.parse(normalizedValue), depth + 1);
    } catch {
      return null;
    }
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const token = extractAccessToken(item, depth + 1);
      if (token) {
        return token;
      }
    }

    return null;
  }

  if (typeof value === "object") {
    const record = value as Record<string, unknown>;

    for (const key of ["access_token", "accessToken", "token"]) {
      const token = extractAccessToken(record[key], depth + 1);
      if (token) {
        return token;
      }
    }

    for (const key of ["session", "currentSession", "current_session"]) {
      const token = extractAccessToken(record[key], depth + 1);
      if (token) {
        return token;
      }
    }
  }

  return null;
};

const collectCandidateValues = (cookies: CookieValue[]): string[] => {
  const directMatches: string[] = [];
  const chunkedMatches = new Map<string, Array<{ index: number; value: string }>>();

  for (const cookie of cookies) {
    if (cookie.name === "sb-access-token" || cookie.name === "access_token") {
      directMatches.push(cookie.value);
      continue;
    }

    if (!supabaseCookiePattern.test(cookie.name)) {
      continue;
    }

    const chunkMatch = cookie.name.match(/^(.*)\.(\d+)$/);
    if (!chunkMatch) {
      directMatches.push(cookie.value);
      continue;
    }

    const [, baseName, rawIndex] = chunkMatch;
    const chunks = chunkedMatches.get(baseName) ?? [];
    chunks.push({ index: Number(rawIndex), value: cookie.value });
    chunkedMatches.set(baseName, chunks);
  }

  for (const chunks of chunkedMatches.values()) {
    directMatches.push(
      chunks
        .sort((left, right) => left.index - right.index)
        .map((chunk) => chunk.value)
        .join(""),
    );
  }

  return directMatches;
};

export const extractSupabaseAccessToken = (
  cookies: CookieValue[],
): string | null => {
  for (const candidate of collectCandidateValues(cookies)) {
    const decodedCandidate =
      candidate.includes("%") ? decodeURIComponent(candidate) : candidate;
    const token =
      extractAccessToken(decodedCandidate) ?? extractAccessToken(candidate);

    if (token) {
      return token;
    }
  }

  return null;
};
