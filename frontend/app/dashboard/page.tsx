import { fetchSubstances } from "@/lib/fetch-substances";
import type { SubstanceProfile } from "@/lib/substance-types";

/**
 * Server Component: fetches SubstanceProfile from Spring Boot and renders a sterile, clinical dashboard.
 */
export default async function DashboardPage() {
  let data;
  let error: string | null = null;

  try {
    data = await fetchSubstances({ page: 0, size: 24 });
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load substances.";
  }

  if (error) {
    return (
      <div className="min-h-screen bg-stone-50">
        <header className="border-b border-stone-200 bg-white px-6 py-4">
          <div className="mx-auto max-w-6xl">
            <h1 className="text-xl font-semibold text-stone-800">Substance profiles</h1>
            <p className="text-sm text-stone-500">Pharmacological reference</p>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-6 py-8">
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
            <p className="font-medium">Error loading data</p>
            <p className="mt-1 text-sm">{error}</p>
          </div>
        </main>
      </div>
    );
  }

  const { content, totalElements, totalPages, number, size } = data!;

  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-6xl">
          <h1 className="text-xl font-semibold text-stone-800">Substance profiles</h1>
          <p className="text-sm text-stone-500">Pharmacological reference — not for clinical decision-making</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <p className="text-sm text-stone-600">
            Showing {number * size + 1}&ndash;{Math.min((number + 1) * size, totalElements)} of {totalElements} (page {number + 1} of {totalPages})
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {content.map((profile) => (
            <SubstanceCard key={profile.id} profile={profile} />
          ))}
        </div>

        {content.length === 0 && (
          <div className="rounded-lg border border-stone-200 bg-white p-8 text-center text-stone-500">
            No substance profiles found.
          </div>
        )}
      </main>
    </div>
  );
}

function SubstanceCard({ profile }: { profile: SubstanceProfile }) {
  return (
    <article className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <h2 className="text-base font-semibold text-stone-800">{profile.name}</h2>
      <dl className="mt-3 space-y-1.5 text-sm">
        <div className="flex justify-between gap-2">
          <dt className="text-stone-500">Half-life</dt>
          <dd className="font-medium text-stone-700">{profile.halfLife} h</dd>
        </div>
        <div className="flex justify-between gap-2">
          <dt className="text-stone-500">Bioavailability</dt>
          <dd className="font-medium text-stone-700">{profile.bioavailability}%</dd>
        </div>
        {profile.standardDosage && (
          <div>
            <dt className="text-stone-500">Standard dosage</dt>
            <dd className="mt-0.5 font-medium text-stone-700">{profile.standardDosage}</dd>
          </div>
        )}
      </dl>
    </article>
  );
}
