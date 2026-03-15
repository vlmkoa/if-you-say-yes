"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { PagedSubstances, SubstanceProfile } from "@/lib/substance-types";

const API_BASE = process.env.NEXT_PUBLIC_SPRING_API_URL ?? "http://localhost:8080";
const PAGE_SIZE = 24;

type RawProfile = SubstanceProfile & { half_life_hours?: number };

function normalizeProfile(raw: RawProfile): SubstanceProfile & { halfLifeNum: number | null; bioavailabilityNum: number | null } {
  const halfLife = raw.halfLife ?? (raw as unknown as Record<string, unknown>).half_life_hours;
  const bioavailability = raw.bioavailability;
  return {
    ...raw,
    halfLife: halfLife ?? 0,
    bioavailability: bioavailability ?? 0,
    halfLifeNum: halfLife != null ? Number(halfLife) : null,
    bioavailabilityNum: bioavailability != null ? Number(bioavailability) : null,
  };
}

function formatHalfLife(value: number | null | undefined): string {
  if (value == null || value === 0) return "Not set";
  return `${value} h`;
}

function formatBioavailability(value: number | null | undefined): string {
  if (value == null || value === 0) return "Not set";
  return `${value}%`;
}

function formatDosageSummary(dosageJson: string | undefined | null): string | null {
  if (!dosageJson?.trim()) return null;
  try {
    const d = JSON.parse(dosageJson) as { roas?: Array<{ name?: string; dose?: unknown }> };
    const roas = d?.roas;
    if (!Array.isArray(roas) || roas.length === 0) return null;
    const first = roas[0];
    const route = first?.name ?? "Oral";
    const dose = first?.dose;
    if (typeof dose === "object" && dose !== null) {
      const common = (dose as { common?: { min?: number; max?: number; units?: string } }).common;
      if (common && (common.min != null || common.max != null)) {
        const lo = common.min ?? common.max;
        const hi = common.max ?? common.min;
        const unit = common.units ?? "mg";
        return lo !== hi ? `${route}: ${lo}–${hi} ${unit}` : `${route}: ${lo} ${unit}`;
      }
    }
    return route;
  } catch {
    return null;
  }
}

function formatAdverseSummary(topAdverseEventsJson: string | undefined | null): string | null {
  if (!topAdverseEventsJson?.trim()) return null;
  try {
    const arr = JSON.parse(topAdverseEventsJson) as Array<{ term?: string; count?: number }>;
    if (!Array.isArray(arr) || arr.length === 0) return null;
    return arr.slice(0, 3).map((e) => e.term ?? "").filter(Boolean).join(", ");
  } catch {
    return null;
  }
}

function SubstanceCard({ profile }: { profile: ReturnType<typeof normalizeProfile> }) {
  const dosageSummary = formatDosageSummary(profile.dosageJson);
  const adverseSummary = formatAdverseSummary(profile.topAdverseEventsJson);
  const hasKnownData =
    (profile.halfLifeNum != null && profile.halfLifeNum > 0) ||
    (profile.bioavailabilityNum != null && profile.bioavailabilityNum > 0) ||
    profile.standardDosage ||
    dosageSummary ||
    adverseSummary;

  return (
    <Link href={`/dashboard/${profile.id}`} className="block">
      <article className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md hover:border-stone-300">
        <h2 className="text-base font-semibold text-stone-800 capitalize">{profile.name}</h2>
      <dl className="mt-3 space-y-2 text-sm">
        <div className="flex justify-between gap-2">
          <dt className="text-stone-500">Half-life</dt>
          <dd className="font-medium text-stone-700">{formatHalfLife(profile.halfLifeNum)}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-stone-500">Bioavailability</dt>
          <dd className="font-medium text-stone-700">{formatBioavailability(profile.bioavailabilityNum)}</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-stone-500">Classification</dt>
          <dd className="font-medium text-stone-700">{profile.classification ?? "—"}</dd>
        </div>
        {profile.standardDosage && (
          <div>
            <dt className="text-stone-500">Standard dosage</dt>
            <dd className="mt-0.5 font-medium text-stone-700">{profile.standardDosage}</dd>
          </div>
        )}
        {dosageSummary && (
          <div>
            <dt className="text-stone-500">Dosage (reference)</dt>
            <dd className="mt-0.5 font-medium text-stone-700">{dosageSummary}</dd>
          </div>
        )}
        {adverseSummary && (
          <div>
            <dt className="text-stone-500">Top adverse events</dt>
            <dd className="mt-0.5 font-medium text-stone-700">{adverseSummary}</dd>
          </div>
        )}
        <div className="flex justify-between gap-2">
          <dt className="text-stone-500">Effects</dt>
          <dd className="font-medium text-stone-700">{profile.effects ?? "—"}</dd>
        </div>
      </dl>
      {!hasKnownData && (
        <p className="mt-2 text-xs text-stone-400">Sync dosage/adverse data via sync script for more detail.</p>
      )}
      </article>
    </Link>
  );
}

export function DashboardClient() {
  const searchParams = useSearchParams();
  const pageParam = searchParams.get("page");
  const page = Math.max(0, parseInt(pageParam ?? "0", 10) || 0);

  const [data, setData] = useState<PagedSubstances | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const url = new URL("/api/substances", API_BASE);
    url.searchParams.set("page", String(page));
    url.searchParams.set("size", String(PAGE_SIZE));
    url.searchParams.set("sortBy", "name");
    url.searchParams.set("sortDir", "asc");
    fetch(url.toString(), { signal: AbortSignal.timeout(20000) })
      .then((res) => {
        if (!res.ok) {
          if (res.status === 503 || res.status === 500) {
            throw new Error("Substance list temporarily unavailable. The database may be offline.");
          }
          throw new Error(`API error: ${res.status}`);
        }
        return res.json();
      })
      .then((json: PagedSubstances) => {
        if (!cancelled) setData(json);
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to load substances.");
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page]);

  function retry() {
    setLoading(true);
    setError(null);
    const url = new URL("/api/substances", API_BASE);
    url.searchParams.set("page", String(page));
    url.searchParams.set("size", String(PAGE_SIZE));
    url.searchParams.set("sortBy", "name");
    url.searchParams.set("sortDir", "asc");
    fetch(url.toString(), { signal: AbortSignal.timeout(20000) })
      .then((res) => {
        if (!res.ok) {
          throw new Error(
            res.status === 503 || res.status === 500 ? "Substance list temporarily unavailable." : `API error: ${res.status}`
          );
        }
        return res.json();
      })
      .then((json: PagedSubstances) => setData(json))
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load substances.");
        setData(null);
      })
      .finally(() => setLoading(false));
  }

  const totalElements = data?.totalElements ?? 0;
  const totalPages = data?.totalPages ?? 0;
  const number = data?.number ?? 0;
  const size = data?.size ?? PAGE_SIZE;
  const content = data?.content ?? [];

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-6xl">
          <h1 className="text-xl font-semibold text-stone-800">Substance profiles</h1>
          <p className="text-sm text-stone-500">Pharmacological reference — not for clinical decision-making</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        {loading && !data && (
          <div className="rounded-lg border border-stone-200 bg-white p-8 text-center text-stone-500">
            Loading…
          </div>
        )}

        {error && !data && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
            <p className="font-medium">Error loading data</p>
            <p className="mt-1 text-sm">{error}</p>
            <button
              type="button"
              onClick={retry}
              className="mt-3 rounded bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        )}

        {data && (
          <>
            <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
              <p className="text-sm text-stone-600">
                Showing {content.length > 0 ? `${number * size + 1}–${Math.min((number + 1) * size, totalElements)}` : "0"} of {totalElements}
                {totalPages > 1 && ` (page ${number + 1} of ${totalPages})`}
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {content.map((profile) => (
                <SubstanceCard key={profile.id} profile={normalizeProfile(profile as RawProfile)} />
              ))}
            </div>

            {content.length === 0 && !loading && (
              <div className="rounded-lg border border-stone-200 bg-white p-8 text-center text-stone-500">
                No substance profiles found. Run <code className="bg-stone-100 px-1 rounded">python scripts/sync_substances_to_core_api.py</code> to populate.
              </div>
            )}

            {totalPages > 1 && (
              <nav className="mt-8 flex flex-wrap items-center justify-center gap-2" aria-label="Pagination">
                <Link
                  href={page <= 0 ? "/dashboard" : `/dashboard?page=${page - 1}`}
                  className={`rounded border px-3 py-1.5 text-sm ${page <= 0 ? "pointer-events-none border-stone-200 text-stone-400" : "border-stone-300 text-stone-700 hover:bg-stone-100"}`}
                  aria-disabled={page <= 0}
                >
                  Previous
                </Link>
                <span className="px-2 text-sm text-stone-600">
                  Page {number + 1} of {totalPages}
                </span>
                <Link
                  href={page >= totalPages - 1 ? `/dashboard?page=${totalPages - 1}` : `/dashboard?page=${page + 1}`}
                  className={`rounded border px-3 py-1.5 text-sm ${page >= totalPages - 1 ? "pointer-events-none border-stone-200 text-stone-400" : "border-stone-300 text-stone-700 hover:bg-stone-100"}`}
                  aria-disabled={page >= totalPages - 1}
                >
                  Next
                </Link>
              </nav>
            )}
          </>
        )}
      </main>
    </div>
  );
}
