import type { PagedSubstances } from "./substance-types";

const DEFAULT_API_BASE = process.env.NEXT_PUBLIC_SPRING_API_URL ?? "http://localhost:8080";

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

  const res = await fetch(url.toString(), {
    next: { revalidate: 30 },
  });

  if (!res.ok) {
    throw new Error(`Substances API error: ${res.status}`);
  }

  return res.json();
}
