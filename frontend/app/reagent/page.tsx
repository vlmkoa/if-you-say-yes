import Link from "next/link";
import { ReagentChat } from "./ReagentChat";

const BACKEND_URL =
  (typeof process.env.NEXT_PUBLIC_BACKEND_URL === "string" && process.env.NEXT_PUBLIC_BACKEND_URL.trim())
    ? process.env.NEXT_PUBLIC_BACKEND_URL.trim()
    : "http://localhost:8000";

export default function ReagentPage() {
  return (
    <div className="subtle-grid">
      <section className="app-shell py-10 sm:py-14">
        <div className="mx-auto max-w-3xl">
          <Link href="/" className="text-xs font-semibold uppercase tracking-wide text-slate-700 hover:text-slate-900">
            ← Back to home
          </Link>
          <div className="mt-4 glass-card p-5 sm:p-6">
            <h1 className="text-xl font-semibold text-slate-900 sm:text-2xl">
              Reagent test chat
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-800">
              Upload a clear photo of a reagent test. The system reads the color in the tube and shows how that color
              reacts for different substances — always presumptive, never a guarantee of what&apos;s actually there.
            </p>
            <p className="mt-2 text-xs text-slate-600">
              Use this as a conversation starter with friends or local harm reduction services, not as proof of purity.
            </p>
          </div>
          <div className="mt-6">
            <ReagentChat apiBaseUrl={BACKEND_URL} />
          </div>
        </div>
      </section>
    </div>
  );
}
