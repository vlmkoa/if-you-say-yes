import Link from "next/link";
import { DrugInteractionForm } from "@/components/drug-interaction-form";
import { HomeHero } from "@/components/HomeHero";

// Must be a valid base URL or fetch throws. Empty string / undefined at build time can break client.
const BACKEND_URL =
  (typeof process.env.NEXT_PUBLIC_BACKEND_URL === "string" && process.env.NEXT_PUBLIC_BACKEND_URL.trim())
    ? process.env.NEXT_PUBLIC_BACKEND_URL.trim()
    : "http://localhost:8000";
const SPRING_API_URL =
  (typeof process.env.NEXT_PUBLIC_SPRING_API_URL === "string" && process.env.NEXT_PUBLIC_SPRING_API_URL.trim())
    ? process.env.NEXT_PUBLIC_SPRING_API_URL.trim()
    : "http://localhost:8080";

function IconShield({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}
function IconFlask({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M10 2v7.31" /><path d="M14 9.3V2" /><path d="M8.5 2h7" /><path d="M14 9.3a6.5 6.5 0 1 1-4 0" /><path d="M5.52 16h12.96" />
    </svg>
  );
}
function IconActivity({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );
}
function IconArrowRight({ className }: { className?: string }) {
  return (
    <svg className={className} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M5 12h14" /><path d="m12 5 7 7-7 7" />
    </svg>
  );
}

export default function HomePage() {
  return (
    <div className="subtle-grid">
      <HomeHero />

      <section className="app-shell pb-12 sm:pb-16 md:pb-24">
        <div className="grid gap-8 md:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] md:items-start">
          <div className="space-y-6">
            <div className="glass-card p-5 sm:p-6">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-orange-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-orange-800">
                <IconShield className="h-4 w-4" />
                Interaction checker
              </div>
              <h2 className="text-lg font-semibold text-slate-900">
                What happens if I mix these two?
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-800">
                Type any two substances and see what&apos;s known ({`or`} unknown) about that combo — straight from the harm
                reduction graphs, with clear &quot;dangerous / caution / low info&quot; feedback.
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <Link
                  href="#checker"
                  className="inline-flex items-center gap-2 rounded-xl bg-amber-400 px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-sm shadow-amber-300/50 transition hover:bg-amber-300"
                >
                  Try the checker
                  <IconArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="glass-card p-5">
                <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-sky-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-sky-900">
                  <IconFlask className="h-4 w-4" />
                  Dashboard
                </div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Learn the shape of a drug
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-800">
                  Half-life, reference dosages, common adverse effects, and community notes — one card per substance so
                  you can actually see what you&apos;re dealing with.
                </p>
                <Link
                  href="/dashboard"
                  className="mt-3 inline-flex text-xs font-semibold text-sky-900 underline underline-offset-4"
                >
                  Open the dashboard
                </Link>
              </div>

              <div className="glass-card p-5">
                <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-rose-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-rose-900">
                  <IconActivity className="h-4 w-4" />
                  Reagent test chat
                </div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Make sense of reagent colors
                </h3>
                <p className="mt-2 text-sm leading-6 text-slate-800">
                  Upload a reagent test photo and get a color-based, non-diagnostic read on what it might react like —
                  plus a plain-language explanation.
                </p>
                <Link
                  href="/reagent"
                  className="mt-3 inline-flex text-xs font-semibold text-rose-900 underline underline-offset-4"
                >
                  Go to reagent test
                </Link>
              </div>
            </div>
          </div>

          <div
            id="checker"
            className="glass-card p-5 sm:p-6 md:p-8 lg:sticky lg:top-24"
          >
            <div className="mb-5 text-left">
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-500 mb-1">
                Live interaction check
              </p>
              <h2 className="text-lg font-semibold text-slate-900 sm:text-xl">
                Compare two substances
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-800">
                Start typing names (or nicknames) — we&apos;ll pull from the known interaction graph and, when data is thin,
                from similar reference substances.
              </p>
            </div>

            <DrugInteractionForm apiBaseUrl={BACKEND_URL} springApiUrl={SPRING_API_URL} />
          </div>
        </div>
      </section>

      <section className="app-shell pb-12 sm:pb-16 md:pb-24">
        <div className="glass-card p-5 sm:p-6 md:p-8">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-left">
              <p className="text-xs font-semibold uppercase tracking-wide text-rose-500 mb-1">
                How to read the colors
              </p>
              <h2 className="text-lg font-semibold text-slate-900 sm:text-xl">
                Interaction guide at a glance
              </h2>
              <p className="mt-2 max-w-xl text-sm leading-6 text-slate-800">
                We sort combinations into three buckets. They&apos;re not moral judgments and they&apos;re not guarantees —
                just the best read from the data we have.
              </p>
            </div>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <div className="metric-card">
              <span className="pill border-emerald-400/40 bg-emerald-100 text-emerald-900">
                Low / no recorded risk
              </span>
              <p className="mt-3 text-sm leading-6 text-slate-800">
                We haven&apos;t found a strong signal for this pair. That doesn&apos;t mean it&apos;s safe — just that serious
                problems aren&apos;t well-documented in the graph yet.
              </p>
            </div>

            <div className="metric-card">
              <span className="pill border-amber-400/60 bg-amber-100 text-amber-900">
                Caution
              </span>
              <p className="mt-3 text-sm leading-6 text-slate-800">
                There is some known risk. Dose, timing, health conditions, and other substances can tilt this toward
                danger; this is where extra checking and slower decisions matter.
              </p>
            </div>

            <div className="metric-card">
              <span className="pill border-rose-500/70 bg-rose-100 text-rose-900">
                Dangerous
              </span>
              <p className="mt-3 text-sm leading-6 text-slate-800">
                These mixes show clear harm patterns (e.g. respiratory depression, serotonin toxicity, cardiac load).
                Best treated as hard no&apos;s or &quot;only with medical supervision&quot; territory.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
