import Link from "next/link";
import { ReagentChat } from "./ReagentChat";

const BACKEND_URL =
  (typeof process.env.NEXT_PUBLIC_BACKEND_URL === "string" && process.env.NEXT_PUBLIC_BACKEND_URL.trim())
    ? process.env.NEXT_PUBLIC_BACKEND_URL.trim()
    : "http://localhost:8000";

export default function ReagentPage() {
  return (
    <div className="min-h-screen bg-stone-50">
      <div className="border-b border-stone-200 bg-white px-4 py-4 sm:px-6">
        <div className="mx-auto max-w-2xl">
          <Link href="/" className="text-sm text-stone-500 hover:text-stone-700">
            ← Home
          </Link>
          <h1 className="mt-2 text-xl font-semibold text-stone-800">Reagent test analysis</h1>
          <p className="text-sm text-stone-500">
            Upload an image of a reagent test result. The system extracts the tube color and suggests possible substance matches (presumptive only).
          </p>
        </div>
      </div>
      <div className="mx-auto max-w-2xl px-4 py-6 sm:px-6">
        <ReagentChat apiBaseUrl={BACKEND_URL} />
      </div>
    </div>
  );
}
