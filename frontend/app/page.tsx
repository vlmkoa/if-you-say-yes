import Link from "next/link";
import { DrugInteractionForm } from "@/components/drug-interaction-form";

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

const quickFacts = [
  {
    title: "Fast interaction checks",
    description:
      "Compare two substances instantly through the graph-backed interaction service.",
    icon: IconShield,
  },
  {
    title: "Clinical-style profiles",
    description:
      "Browse half-life, bioavailability, and standard dosage from the structured profile dashboard.",
    icon: IconFlask,
  },
  {
    title: "Action-focused outputs",
    description:
      "Highlight caution and dangerous combinations with clearer visual feedback.",
    icon: IconActivity,
  },
];

export default function HomePage() {
  return (
    <div className="subtle-grid">
      <section className="app-shell py-12 sm:py-16 md:py-24">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-start lg:gap-12">
          <div className="space-y-8 animate-fade-in">
            <div className="space-y-4">
              <span className="soft-label">Drug interaction engine</span>
              <h1 className="section-title max-w-2xl">
                Check substance interactions with a cleaner, more trustworthy workflow.
              </h1>
              <p className="section-copy max-w-xl">
                Compare two substances instantly. This app uses a graph-backed interaction service and a clinical-style dashboard for reference.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link
                href="#checker"
                className="inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-900 shadow-lg shadow-cyan-400/20 transition hover:bg-cyan-300 hover:shadow-cyan-400/25"
              >
                Check interaction
                <IconArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium text-white transition hover:bg-white/10"
              >
                Browse dashboard
              </Link>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              {quickFacts.map((item, i) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="glass-card p-5 animate-slide-up">
                    <div className="mb-3 inline-flex rounded-xl bg-cyan-400/10 p-2.5 text-cyan-300 ring-1 ring-cyan-400/20">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h2 className="mb-1.5 text-base font-semibold text-white">
                      {item.title}
                    </h2>
                    <p className="text-sm leading-6 text-slate-400">
                      {item.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          <div
            id="checker"
            className="glass-card p-5 sm:p-6 md:p-8 lg:sticky lg:top-24 animate-slide-up"
          >
            <div className="mb-5">
              <p className="soft-label mb-2">Live checker</p>
              <h2 className="text-xl font-semibold text-white sm:text-2xl">
                Compare two substances
              </h2>
              <p className="mt-2 text-sm leading-6 text-slate-400">
                Type substance names below. Results are powered by your FastAPI interaction endpoint.
              </p>
            </div>

            <DrugInteractionForm apiBaseUrl={BACKEND_URL} springApiUrl={SPRING_API_URL} />
          </div>
        </div>
      </section>

      <section className="app-shell pb-12 sm:pb-16 md:pb-24">
        <div className="glass-card grid gap-5 p-5 sm:gap-6 sm:p-6 md:grid-cols-2 lg:grid-cols-4 md:p-8">
          <div className="lg:col-span-1">
            <p className="soft-label mb-2">How to read results</p>
            <h3 className="text-lg font-semibold text-white sm:text-xl">Risk levels</h3>
          </div>

          <div className="metric-card">
            <span className="pill border-emerald-400/30 bg-emerald-400/10 text-emerald-200">
              Low / none recorded
            </span>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              No significant interaction recorded in the graph for the chosen pair.
            </p>
          </div>

          <div className="metric-card">
            <span className="pill border-amber-400/30 bg-amber-400/10 text-amber-200">
              Caution
            </span>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              Monitoring, dose adjustment, or alternatives may be needed depending on context.
            </p>
          </div>

          <div className="metric-card">
            <span className="pill border-rose-400/40 bg-rose-500/20 text-rose-200">
              Dangerous
            </span>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              This combination is flagged as high risk. Avoid or seek clinical guidance before use.
            </p>
          </div>
        </div>

        <div className="mt-6 glass-card p-5 sm:p-6 md:p-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="soft-label mb-2">Phase 2</p>
              <h3 className="text-xl font-semibold text-white sm:text-2xl">
                Substance profile dashboard
              </h3>
              <p className="mt-2 max-w-xl text-sm leading-6 text-slate-400">
                View pharmacological reference data in a polished grid with cards and pagination.
              </p>
            </div>

            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium text-white transition hover:bg-white/10"
            >
              Open dashboard
              <IconArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
