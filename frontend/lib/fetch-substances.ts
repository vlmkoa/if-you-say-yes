import type { PagedSubstances } from "./substance-types";

// Server-side (e.g. Docker: http://core-api:8080); client/browser uses NEXT_PUBLIC_*
const DEFAULT_API_BASE = process.env.SPRING_API_URL ?? process.env.NEXT_PUBLIC_SPRING_API_URL ?? "http://localhost:8080";

const FETCH_TIMEOUT_MS = 20000;
const RETRY_DELAY_MS = 1500;
const MAX_ATTEMPTS = 3;

export async function fetchSubstances(options?: {
  apiBase?: string;
  page?: number;
  size?: number;
  sortBy?: string;
  sortDir?: "asc" | "desc";
}): Promise<PagedSubstances> {
  const { apiBase = DEFAULT_API_BASE, page = 0, size = 20, sortBy = "name", sortDir = "asc" } = options ?? {};
  const url = new URL("/api/substances", apiBase);
  url.searchParams.set("page", String(page));
  url.searchParams.set("size", String(size));
  url.searchParams.set("sortBy", sortBy);
  url.searchParams.set("sortDir", sortDir);

  let lastError: Error | null = null;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    try {
      const res = await fetch(url.toString(), {
        next: { revalidate: 30 },
        signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
      });

      if (!res.ok) {
        if (res.status === 503 || res.status === 500) {
          lastError = new Error("Substance list temporarily unavailable. The database may be offline.");
          if (attempt < MAX_ATTEMPTS) {
            await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
            continue;
          }
          throw lastError;
        }
        throw new Error(`Substances API error: ${res.status}`);
      }

      return await res.json();
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e));
      lastError = err;
      const isRetryable =
        err.name === "TimeoutError" ||
        err.message.includes("fetch") ||
        err.message.includes("ECONNREFUSED") ||
        err.message.includes("temporarily unavailable");
      if (isRetryable && attempt < MAX_ATTEMPTS) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
        continue;
      }
      throw new Error(
        `Dashboard could not reach core-api at ${url.origin}. ${err.message}. Ensure core-api is running (e.g. docker compose ps).`
      );
    }
  }
  throw lastError ?? new Error("Failed to load substances.");
}
