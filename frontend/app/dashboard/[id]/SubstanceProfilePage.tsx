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

// Parsed dosage JSON shape (e.g. from PsychonautWiki-style data)
type DoseRange = { min: number; max: number; units: string | null };
type DurationRange = { min: number; max: number; units: string | null };
type Roa = {
  name: string;
  dose: {
    threshold?: DoseRange;
    light?: DoseRange;
    common?: DoseRange;
    strong?: DoseRange;
    heavy?: DoseRange;
  };
  duration: {
    onset?: DurationRange;
    comeup?: DurationRange;
    peak?: DurationRange;
    offset?: DurationRange;
    total?: DurationRange;
  };
};
type DosageData = { name?: string; roas?: Roa[] };

function parseDosageJson(json: string | undefined | null): DosageData | null {
  if (!json?.trim()) return null;
  try {
    const data = JSON.parse(json) as DosageData;
    return data?.roas ? data : null;
  } catch {
    return null;
  }
}

function formatRange(range: DoseRange | undefined, defaultUnit = ""): string {
  if (!range) return "—";
  const u = range.units ?? defaultUnit;
  const s = u ? ` ${u}` : "";
  if (range.min === range.max) return `${range.min}${s}`;
  return `${range.min}–${range.max}${s}`;
}

function formatDuration(range: DurationRange | undefined): string {
  if (!range) return "—";
  const u = range.units ?? "min";
  if (range.min === range.max) return `${range.min} ${u}`;
  return `${range.min}–${range.max} ${u}`;
}

function DosageDisplay({ dosageJson }: { dosageJson: string }) {
  const data = parseDosageJson(dosageJson);
  if (!data?.roas?.length) return null;

  const doseLabels: { key: keyof Roa["dose"]; label: string }[] = [
    { key: "threshold", label: "Threshold" },
    { key: "light", label: "Light" },
    { key: "common", label: "Common" },
    { key: "strong", label: "Strong" },
    { key: "heavy", label: "Heavy" },
  ];
  const durationLabels: { key: keyof Roa["duration"]; label: string }[] = [
    { key: "onset", label: "Onset" },
    { key: "comeup", label: "Come up" },
    { key: "peak", label: "Peak" },
    { key: "offset", label: "Offset" },
    { key: "total", label: "Total" },
  ];

  return (
    <div className="mt-6 border-t border-stone-200 pt-4">
      <h3 className="text-sm font-semibold text-stone-700 mb-3">Dosage by route</h3>
      <p className="text-xs text-stone-500 mb-4">Reference ranges only — not medical advice.</p>
      <div className="space-y-6">
        {data.roas.map((roa) => (
          <div key={roa.name} className="rounded-lg border border-stone-200 bg-stone-50/80 p-4">
            <h4 className="text-sm font-medium text-stone-800 capitalize mb-3">{roa.name}</h4>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-2">Dose</p>
                <dl className="space-y-1.5 text-sm">
                  {doseLabels.map(({ key, label }) => (
                    <div key={key} className="flex justify-between gap-2">
                      <dt className="text-stone-500">{label}</dt>
                      <dd className="font-medium text-stone-700 tabular-nums">{formatRange(roa.dose[key])}</dd>
                    </div>
                  ))}
                </dl>
              </div>
              <div>
                <p className="text-xs font-medium text-stone-500 uppercase tracking-wide mb-2">Duration</p>
                <dl className="space-y-1.5 text-sm">
                  {durationLabels.map(({ key, label }) => (
                    <div key={key} className="flex justify-between gap-2">
                      <dt className="text-stone-500">{label}</dt>
                      <dd className="font-medium text-stone-700 tabular-nums">{formatDuration(roa.duration[key])}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
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
            {profile.category && (
              <div className="flex justify-between gap-4">
                <dt className="text-stone-500">Category</dt>
                <dd className="font-medium text-stone-700">{profile.category}</dd>
              </div>
            )}
            {profile.interactionReference && (
              <div className="flex justify-between gap-4">
                <dt className="text-stone-500">Similar drug for interactions</dt>
                <dd className="font-medium text-stone-700 capitalize">{profile.interactionReference}</dd>
              </div>
            )}
            {profile.standardDosage && (
              <div>
                <dt className="text-stone-500">Standard dosage</dt>
                <dd className="mt-0.5 font-medium text-stone-700">{profile.standardDosage}</dd>
              </div>
            )}
          </dl>
          {profile.dosageJson && <DosageDisplay dosageJson={profile.dosageJson} />}
        </article>

        <CommentSection substanceId={profile.id} />
      </main>
    </div>
  );
}

type Comment = { id: number; substanceId: number; body: string; status?: string; createdAt: string };

function CommentSection({ substanceId }: { substanceId: number }) {
  const [comments, setComments] = React.useState<Comment[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [submitBody, setSubmitBody] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [submitMessage, setSubmitMessage] = React.useState<"idle" | "success" | "error">("idle");

  function loadComments() {
    fetch(`${API_BASE}/api/substances/${substanceId}/comments`, { signal: AbortSignal.timeout(10000) })
      .then((res) => (res.ok ? res.json() : []))
      .then((data: Comment[]) => setComments(Array.isArray(data) ? data : []))
      .catch(() => setComments([]))
      .finally(() => setLoading(false));
  }

  React.useEffect(() => {
    setLoading(true);
    loadComments();
  }, [substanceId]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const body = submitBody.trim();
    if (!body || submitting) return;
    setSubmitting(true);
    setSubmitMessage("idle");
    fetch(`${API_BASE}/api/substances/${substanceId}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ body }),
    })
      .then((res) => {
        if (res.ok) {
          setSubmitBody("");
          setSubmitMessage("success");
          loadComments();
        } else {
          setSubmitMessage("error");
        }
      })
      .catch(() => setSubmitMessage("error"))
      .finally(() => setSubmitting(false));
  }

  return (
    <section className="mt-8 rounded-lg border border-stone-200 bg-white p-6 shadow-sm" aria-label="Community comments">
      <h2 className="text-lg font-semibold text-stone-800">Community</h2>
      <p className="mt-1 text-sm text-stone-500">
        Anonymous experiences and notes. No login required. Comments appear after moderator approval.
      </p>

      {loading ? (
        <p className="mt-4 text-sm text-stone-500">Loading comments…</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {comments.length === 0 ? (
            <li className="text-sm text-stone-500 italic">No comments yet. Be the first to share.</li>
          ) : (
            comments.map((c) => (
              <li key={c.id} className="rounded border border-stone-100 bg-stone-50/50 p-3 text-sm text-stone-700">
                <span className="text-stone-400 text-xs">
                  Anonymous · {new Date(c.createdAt).toLocaleDateString()}
                </span>
                <p className="mt-1 whitespace-pre-wrap">{c.body}</p>
              </li>
            ))
          )}
        </ul>
      )}

      <form onSubmit={handleSubmit} className="mt-6">
        <label htmlFor="comment-body" className="block text-sm font-medium text-stone-600">
          Share your experience (anonymous)
        </label>
        <textarea
          id="comment-body"
          rows={3}
          value={submitBody}
          onChange={(e) => setSubmitBody(e.target.value)}
          placeholder="Your comment will be visible after a moderator approves it."
          maxLength={4000}
          className="mt-1 w-full rounded border border-stone-300 p-2 text-sm text-stone-800 placeholder-stone-400 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
          disabled={submitting}
        />
        <div className="mt-2 flex items-center gap-3">
          <button
            type="submit"
            disabled={!submitBody.trim() || submitting}
            className="rounded bg-stone-700 px-4 py-2 text-sm text-white hover:bg-stone-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? "Sending…" : "Submit"}
          </button>
          {submitMessage === "success" && (
            <span className="text-sm text-green-600">Submitted. It will appear after approval.</span>
          )}
          {submitMessage === "error" && (
            <span className="text-sm text-red-600">Failed to submit. Try again.</span>
          )}
        </div>
      </form>
    </section>
  );
}
