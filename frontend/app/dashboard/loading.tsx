/**
 * Skeleton loader shown while the dashboard page is suspended (e.g. fetching substances).
 */
export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-stone-50">
      <header className="border-b border-stone-200 bg-white px-6 py-4">
        <div className="mx-auto max-w-6xl">
          <div className="h-7 w-64 animate-pulse rounded bg-stone-200" />
          <div className="mt-2 h-4 w-96 animate-pulse rounded bg-stone-100" />
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-6 h-8 w-48 animate-pulse rounded bg-stone-200" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="rounded-lg border border-stone-200 bg-white p-5 shadow-sm"
            >
              <div className="mb-3 h-5 w-3/4 animate-pulse rounded bg-stone-200" />
              <div className="space-y-2">
                <div className="h-4 w-full animate-pulse rounded bg-stone-100" />
                <div className="h-4 w-2/3 animate-pulse rounded bg-stone-100" />
                <div className="h-4 w-1/2 animate-pulse rounded bg-stone-100" />
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
