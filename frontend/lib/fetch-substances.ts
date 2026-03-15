import type { PagedSubstances } from "./substance-types";

// Server-side (e.g. Docker: http://core-api:8080); client/browser uses NEXT_PUBLIC_*
const DEFAULT_API_BASE = process.env.SPRING_API_URL ?? process.env.NEXT_PUBLIC_SPRING_API_URL ?? "http://localhost:8080";

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

  let res: Response;
  try {
    res = await fetch(url.toString(), {
      next: { revalidate: 30 },
      signal: AbortSignal.timeout(15000),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new Error(
      `Dashboard could not reach core-api at ${url.origin}. ${msg}. Ensure core-api is running (e.g. docker compose ps).`
    );
  }

  if (!res.ok) {
    if (res.status === 503 || res.status === 500) {
      throw new Error("Substance list temporarily unavailable. The database may be offline.");
    }
    throw new Error(`Substances API error: ${res.status}`);
  }

  return res.json();
}
