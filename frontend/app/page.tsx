import Link from "next/link";
import { DrugInteractionForm } from "@/components/drug-interaction-form";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-10 space-y-10">
      <div>
        <h1 className="text-2xl font-semibold text-stone-800">if-you-say-yes</h1>
        <p className="mt-2 text-stone-600">
          Drug interaction engine and substance profiles.
        </p>
        <ul className="mt-6 list-inside list-disc space-y-2 text-stone-700">
          <li>
            <Link href="/dashboard" className="text-blue-600 underline hover:no-underline">
              Dashboard
            </Link>{" "}
            — Substance profiles (Phase 2)
          </li>
          <li>
            Drug interaction checker (Phase 1) — below.
          </li>
        </ul>
      </div>

      <section>
        <h2 className="text-lg font-medium text-stone-800 mb-3">Check drug interaction</h2>
        <DrugInteractionForm apiBaseUrl={BACKEND_URL} />
      </section>
    </main>
  );
}
