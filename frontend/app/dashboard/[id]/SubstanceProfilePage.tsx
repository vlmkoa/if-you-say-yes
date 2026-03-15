"use client";

import * as React from "react";
import Link from "next/link";
import { RiskWarning } from "@/components/RiskWarning";
import { Button } from "@/components/ui/button";
import type { SubstanceProfile } from "@/lib/substance-types";

const API_BASE = process.env.NEXT_PUBLIC_SPRING_API_URL ?? "http://localhost:8080";
const ADDICTION_THRESHOLD = 7;

function parseAdverseEffects(topAdverseEventsJson: string | undefined | null): string[] {
  if (!topAdverseEventsJson?.trim()) return [];
  try {
    const arr = JSON.parse(topAdverseEventsJson) as Array<{ term?: string }>;
    if (!Array.isArray(arr)) return [];
    return arr.map((e) => e.term ?? "").filter(Boolean);
  } catch {
    return [];
  }
}

function formatVal(value: number | null | undefined, suffix: string): string {
  if (value == null) return "Not set";
  if (value === 0) return "Not set";
  return `${value}${suffix}`;
}

export function SubstanceProfilePage({ id }: { id: string }) {
  const [profile, setProfile] = React.useState<SubstanceProfile | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [riskAcknowledged, setRiskAcknowledged] = React.useState(false);

  React.useEffect(() => {
    const url = `${API_BASE}/api/substances/${id}`;
    fetch(url, { signal: AbortSignal.timeout(15000) })
      .then((res) => {
        if (!res.ok) {
          if (res.status === 404) throw new Error("Substance not found");
          throw new Error(`Failed to load: ${res.status}`);
        }
        return res.json();
      })
      .then((data: SubstanceProfile) => setProfile(data))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [id]);

  const addictionPotential = profile?.addictionPotential != null ? Number(profile.addictionPotential) : null;
  const showRiskWarning =
    !riskAcknowledged &&
    profile != null &&
    addictionPotential != null &&
    addictionPotential > ADDICTION_THRESHOLD;

  const adverseEffects = showRiskWarning
    ? parseAdverseEffects(profile?.topAdverseEventsJson)
    : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <p className="text-stone-500">Loading…</p>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-stone-50 p-6">
        <div className="mx-auto max-w-2xl rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          <p className="font-medium">{error ?? "Substance not found."}</p>
          <Link href="/dashboard" className="mt-3 inline-block text-sm underline">
            Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50">
      {showRiskWarning && (
        <RiskWarning
          adverse_effects={adverseEffects}
          onAcknowledge={() => setRiskAcknowledged(true)}
        />
      )}

      <header className="border-b border-stone-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-2xl">
          <Link href="/dashboard" className="text-sm text-stone-500 hover:text-stone-700">
            ← Dashboard
          </Link>
          <h1 className="mt-2 text-xl font-semibold text-stone-800 capitalize">{profile.name}</h1>
          <p className="text-sm text-stone-500">Substance profile — not for clinical decision-making</p>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-6 py-8">
        <article className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-stone-500">Half-life</dt>
              <dd className="font-medium text-stone-700">{formatVal(profile.halfLife, " h")}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-stone-500">Bioavailability</dt>
              <dd className="font-medium text-stone-700">{formatVal(profile.bioavailability, "%")}</dd>
            </div>
            {profile.addictionPotential != null && Number(profile.addictionPotential) > 0 && (
              <div className="flex justify-between gap-4">
                <dt className="text-stone-500">Addiction potential</dt>
                <dd className="font-medium text-stone-700">{profile.addictionPotential}/10</dd>
              </div>
            )}
            {profile.standardDosage && (
              <div>
                <dt className="text-stone-500">Standard dosage</dt>
                <dd className="mt-0.5 font-medium text-stone-700">{profile.standardDosage}</dd>
              </div>
            )}
          </dl>
          {profile.dosageJson && (
            <div className="mt-6 border-t border-stone-100 pt-4">
              <h3 className="text-sm font-medium text-stone-500">Dosage (reference)</h3>
              <pre className="mt-1 overflow-x-auto rounded bg-stone-50 p-3 text-xs text-stone-700">
                {profile.dosageJson}
              </pre>
            </div>
          )}
        </article>
      </main>
    </div>
  );
}
