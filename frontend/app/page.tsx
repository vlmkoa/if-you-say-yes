import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
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
          Drug interaction checker (Phase 1) — use the form component with{" "}
          <code className="rounded bg-stone-100 px-1">apiBaseUrl=&quot;http://localhost:8000&quot;</code>
        </li>
      </ul>
    </main>
  );
}
