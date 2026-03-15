"use client";

import * as React from "react";

// Inline SVGs (lucide-react 0.460 lacks ArrowLeftRight, ShieldAlert, etc.)
type SvgProps = { className?: string };
const svg = (d: string, viewBox = "0 0 24 24") => ({ className, ...p }: SvgProps) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox={viewBox} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden {...p}><path d={d} /></svg>
);
const IconLoader = ({ className, ...p }: SvgProps) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden {...p}><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
);
const IconCheckCircle = ({ className, ...p }: SvgProps) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden {...p}>
    <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
    <path d="m9 12 2 2 4-4" />
  </svg>
);
const IconAlertCircle = svg("M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z M12 8v4 M12 16h.01");
const IconShieldAlert = svg("M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z");
const IconTriangleAlert = svg("m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z M12 9v4 M12 17h.01");
const IconSearch = svg("m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z");
const IconArrowLeftRight = svg("M16 3h5v5 M4 20L21 3 M21 16v5h-5 M15 15l6 6 M4 4l5 5");

type InteractionResponse = {
  drug_a: string;
  drug_b: string;
  risk_level: string;
  mechanism: string;
  inferred?: boolean;
  reference_drug_a?: string | null;
  reference_drug_b?: string | null;
  no_known_effect?: boolean;
};

type DrugInteractionFormProps = {
  apiBaseUrl: string;
  /** Optional: fetch substance names from core-api for dropdown (all drugs in Postgres). */
  springApiUrl?: string;
  substances?: string[];
};

type InteractionState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "not_found" }
  | { status: "error"; message: string }
  | { status: "success"; data: InteractionResponse };

// Clinical + TripSit-style names so autocomplete matches Neo4j (TripSit combos). Lookup is case-insensitive.
const DEFAULT_SUBSTANCES: string[] = [
  "Warfarin",
  "Ibuprofen",
  "Paracetamol",
  "Aspirin",
  "Atorvastatin",
  "Metformin",
  "Omeprazole",
  "alcohol",
  "caffeine",
  "cannabis",
  "cocaine",
  "lsd",
  "mdma",
  "ketamine",
  "dmt",
  "benzodiazepines",
  "amphetamines",
  "tramadol",
  "opioids",
  "ssris",
  "maois",
  "mushrooms",
  "nitrous",
  "mescaline",
  "dextromethorphan",
  "lithium",
  "ghb",
  "gbl",
  "pcp",
  "2c-x",
  "2c-t-x",
  "5-meo-dmt",
  "amt",
  "dox",
  "mxe",
  "nbomes",
  "pregabalin",
];

function getFiltered(items: string[], value: string, otherValue: string) {
  return items
    .filter((item) =>
      item.toLowerCase().includes(value.trim().toLowerCase())
    )
    .filter((item) => item.toLowerCase() !== otherValue.trim().toLowerCase())
    .slice(0, 6);
}

const FALLBACK_BACKEND = "http://localhost:8000";

function resolveBackendUrl(base: string | undefined): string {
  const s = typeof base === "string" ? base.trim() : "";
  if (s && s.startsWith("http")) return s;
  return FALLBACK_BACKEND;
}

export function DrugInteractionForm({
  apiBaseUrl,
  springApiUrl,
  substances: substancesProp,
}: DrugInteractionFormProps) {
  const [drugA, setDrugA] = React.useState("");
  const [drugB, setDrugB] = React.useState("");
  const [state, setState] = React.useState<InteractionState>({ status: "idle" });
  const [focusedField, setFocusedField] = React.useState<"a" | "b" | null>(null);
  const [substancesFromApi, setSubstancesFromApi] = React.useState<string[]>([]);
  const backendUrl = resolveBackendUrl(apiBaseUrl);

  // Load substance names from core-api for dropdown when springApiUrl is set (all pages)
  React.useEffect(() => {
    if (!springApiUrl?.trim()) return;
    const base = springApiUrl.trim().replace(/\/$/, "");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 25000);
    let allNames: string[] = [];
    let page = 0;
    const size = 200;
    function fetchPage() {
      const url = `${base}/api/substances?page=${page}&size=${size}&sortBy=name&sortDir=asc`;
      fetch(url, { signal: controller.signal })
        .then((res) => (res.ok ? res.json() : null))
        .then((data: { content?: Array<{ name?: string }>; last?: boolean } | null) => {
          if (!data?.content?.length) {
            if (allNames.length) setSubstancesFromApi(allNames);
            return;
          }
          const names = data.content.map((s) => (s.name ?? "").trim()).filter(Boolean);
          allNames = [...allNames, ...names];
          if (data.last === true || data.content.length < size) {
            setSubstancesFromApi(allNames);
            return;
          }
          page += 1;
          fetchPage();
        })
        .catch(() => {
          if (allNames.length) setSubstancesFromApi(allNames);
        });
    }
    fetchPage();
    return () => {
      clearTimeout(timeout);
      controller.abort();
    };
  }, [springApiUrl]);

  const substances = substancesProp ?? (substancesFromApi.length > 0 ? substancesFromApi : DEFAULT_SUBSTANCES);

  const filteredSubstancesA = React.useMemo(
    () => getFiltered(substances, drugA, drugB),
    [substances, drugA, drugB]
  );

  const filteredSubstancesB = React.useMemo(
    () => getFiltered(substances, drugB, drugA),
    [substances, drugB, drugA]
  );

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    const trimmedA = drugA.trim();
    const trimmedB = drugB.trim();

    if (!trimmedA || !trimmedB) {
      setState({
        status: "error",
        message: "Please select both substances before checking.",
      });
      return;
    }

    if (trimmedA.toLowerCase() === trimmedB.toLowerCase()) {
      setState({
        status: "error",
        message: "Please choose two different substances.",
      });
      return;
    }

    setState({ status: "loading" });

    void (async () => {
      try {
        const url = new URL("/interaction", backendUrl);
        url.searchParams.set("drug_a", trimmedA);
        url.searchParams.set("drug_b", trimmedB);

        const res = await fetch(url.toString(), { method: "GET" });

        if (res.status === 404) {
          setState({ status: "not_found" });
          return;
        }

        if (!res.ok) {
          const body = await res.json().catch(() => null);
          const detail =
            (body as { detail?: string } | null)?.detail ??
            "Unexpected error while checking interaction.";

          setState({
            status: "error",
            message: detail,
          });
          return;
        }

        const data: InteractionResponse = await res.json();
        setState({ status: "success", data });
      } catch (error) {
        console.error("Failed to fetch interaction", error);
        setState({
          status: "error",
          message: "Unable to reach the interaction service. Please try again.",
        });
      }
    })();
  }

  function swapValues() {
    setDrugA(drugB);
    setDrugB(drugA);
    setState({ status: "idle" });
    setFocusedField(null);
  }

  function getResultCard() {
    if (state.status === "idle") {
      return (
        <div className="rounded-2xl border border-dashed border-amber-300 bg-amber-50 p-4 text-sm text-slate-800">
          Choose two substances, then run the interaction check.
        </div>
      );
    }

    if (state.status === "loading") {
      return (
        <div className="rounded-2xl border border-amber-400/40 bg-amber-200/40 p-4">
          <div className="flex items-start gap-3">
            <IconLoader className="mt-0.5 h-5 w-5 animate-spin text-amber-700" />
            <div>
              <p className="font-medium text-amber-900">Checking interaction</p>
              <p className="mt-1 text-sm text-amber-900/80">
                Querying the interaction graph. This should only take a moment.
              </p>
            </div>
          </div>
        </div>
      );
    }

    if (state.status === "not_found") {
      return (
        <div className="rounded-2xl border border-emerald-300/40 bg-emerald-100/60 p-4">
          <div className="flex items-start gap-3">
            <IconCheckCircle className="mt-0.5 h-5 w-5 text-emerald-700" />
            <div>
              <p className="font-medium text-emerald-900">No known interaction</p>
              <p className="mt-1 text-sm text-emerald-900/80">
                There is no documented interaction between these substances in
                the current graph. This does not guarantee safety.
              </p>
            </div>
          </div>
        </div>
      );
    }

    if (state.status === "error") {
      return (
        <div className="rounded-2xl border border-rose-300/40 bg-rose-100/60 p-4">
          <div className="flex items-start gap-3">
            <IconAlertCircle className="mt-0.5 h-5 w-5 text-rose-700" />
            <div>
              <p className="font-medium text-rose-900">Something went wrong</p>
              <p className="mt-1 text-sm text-rose-900/80">{state.message}</p>
            </div>
          </div>
        </div>
      );
    }

    const { data } = state;
    const risk = data.risk_level?.toLowerCase() ?? "";
    const noKnownEffect = data.no_known_effect || risk === "unknown";
    const isInferred = Boolean(data.inferred && (data.reference_drug_a || data.reference_drug_b));
    const inferredNote = isInferred
      ? `This result is inferred from the interaction of ${[data.reference_drug_a, data.reference_drug_b].filter(Boolean).join(" and ")}; it may not apply directly to ${data.drug_a} + ${data.drug_b}.`
      : null;

    if (noKnownEffect) {
      return (
        <div className="rounded-2xl border border-slate-300 bg-slate-50 p-5">
          <div className="mb-4 flex items-center gap-3">
            <IconAlertCircle className="h-5 w-5 text-slate-600" />
            <span className="rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
              No known effects yet
            </span>
          </div>
          <div className="space-y-3">
            <p className="text-sm text-slate-800">
              <span className="font-semibold text-slate-900">Pair:</span> {data.drug_a} + {data.drug_b}
            </p>
            <p className="text-sm text-slate-700">
              {data.mechanism ||
                "No known interaction data for this combination. Colorimetric testing is presumptive; consult a professional."}
            </p>
          </div>
        </div>
      );
    }

    const isDangerous =
      risk === "dangerous" || risk === "high" || risk === "contraindicated";
    const isCaution =
      !isDangerous &&
      (risk === "caution" || risk === "moderate" || risk === "monitor");

    if (isDangerous) {
      return (
        <div className="rounded-2xl border border-rose-400/40 bg-rose-100/80 p-5">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <IconShieldAlert className="h-5 w-5 text-rose-700" />
            <span className="rounded-full border border-rose-400/40 bg-rose-200 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-rose-900">
              Dangerous interaction
            </span>
            {isInferred && (
              <span className="rounded-full border border-amber-400/40 bg-amber-500/20 px-3 py-1 text-xs font-medium text-amber-100">
                Inferred from similar substance
              </span>
            )}
          </div>
          <div className="space-y-3">
            <p className="text-sm text-rose-900">
              <span className="font-semibold text-rose-950">Pair:</span> {data.drug_a} +{" "}
              {data.drug_b}
            </p>
            <p className="text-sm text-rose-900">
              <span className="font-semibold text-rose-950">Mechanism:</span>{" "}
              {data.mechanism ||
                "This combination is flagged as dangerous in the interaction graph."}
            </p>
            {inferredNote && (
              <p className="rounded-lg border border-amber-400/40 bg-amber-100 px-3 py-2 text-sm text-amber-900">
                {inferredNote}
              </p>
            )}
          </div>
        </div>
      );
    }

    if (isCaution) {
      return (
        <div className="rounded-2xl border border-amber-300/40 bg-amber-100/80 p-5">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <IconTriangleAlert className="h-5 w-5 text-amber-700" />
            <span className="rounded-full border border-amber-400/40 bg-amber-200 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-900">
              Caution advised
            </span>
            {isInferred && (
              <span className="rounded-full border border-slate-400/40 bg-slate-500/20 px-3 py-1 text-xs font-medium text-slate-200">
                Inferred from similar substance
              </span>
            )}
          </div>
          <div className="space-y-3">
            <p className="text-sm text-amber-900">
              <span className="font-semibold text-amber-950">Pair:</span> {data.drug_a} +{" "}
              {data.drug_b}
            </p>
            <p className="text-sm text-amber-900">
              <span className="font-semibold text-amber-950">Mechanism:</span>{" "}
              {data.mechanism ||
                "Use with caution. Consider monitoring, dose adjustment, or alternatives."}
            </p>
            {inferredNote && (
              <p className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-800">
                {inferredNote}
              </p>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="rounded-2xl border border-emerald-300/40 bg-emerald-100/80 p-5">
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <IconCheckCircle className="h-5 w-5 text-emerald-700" />
          <span className="rounded-full border border-emerald-400/40 bg-emerald-200 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-900">
            Low recorded risk
          </span>
          {isInferred && (
            <span className="rounded-full border border-slate-300 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-800">
              Inferred from similar substance
            </span>
          )}
        </div>
        <div className="space-y-3">
          <p className="text-sm text-emerald-900">
            <span className="font-semibold text-emerald-950">Pair:</span> {data.drug_a} +{" "}
            {data.drug_b}
          </p>
          <p className="text-sm text-emerald-900">
            <span className="font-semibold text-emerald-950">Mechanism:</span>{" "}
            {data.mechanism ||
              "There is no significant interaction risk recorded for this combination in the graph."}
          </p>
          {inferredNote && (
            <p className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-800">
              {inferredNote}
            </p>
          )}
        </div>
      </div>
    );
  }

  function renderSuggestions(
    items: string[],
    onSelect: (value: string) => void
  ) {
    if (!items.length) return null;

    return (
      <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-2xl border border-slate-600 bg-slate-900 shadow-2xl ring-2 ring-slate-700">
        {items.map((item) => (
          <button
            key={item}
            type="button"
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => onSelect(item)}
            className="flex w-full items-center gap-3 border-b border-slate-700/80 px-4 py-3 text-left text-sm font-medium text-white transition last:border-b-0 hover:bg-slate-700/50"
          >
            <IconSearch className="h-4 w-4 shrink-0 text-cyan-400" />
            <span>{item}</span>
          </button>
        ))}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid gap-4 md:grid-cols-[1fr_auto_1fr] md:items-end">
        <div className="relative">
          <label
            htmlFor="drug-a"
            className="mb-2 block text-sm font-medium text-slate-900"
          >
            Substance A
          </label>
          <input
            id="drug-a"
            value={drugA}
            onChange={(e) => {
              setDrugA(e.target.value);
              setFocusedField("a");
              setState({ status: "idle" });
            }}
            onFocus={() => setFocusedField("a")}
            onBlur={() => {
              window.setTimeout(() => setFocusedField(null), 120);
            }}
            placeholder="Start typing to search..."
            autoComplete="off"
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-500 focus:border-amber-500 focus:ring-2 focus:ring-amber-300"
          />
          {focusedField === "a" &&
            renderSuggestions(filteredSubstancesA, (value) => {
              setDrugA(value);
              setFocusedField(null);
            })}
        </div>

        <button
          type="button"
          onClick={swapValues}
          className="inline-flex h-12 w-12 items-center justify-center self-end rounded-2xl border border-slate-300 bg-white text-slate-700 transition hover:bg-amber-100 hover:border-amber-400"
          aria-label="Swap substances"
        >
          <IconArrowLeftRight className="h-4 w-4" />
        </button>

        <div className="relative">
          <label
            htmlFor="drug-b"
            className="mb-2 block text-sm font-medium text-slate-900"
          >
            Substance B
          </label>
          <input
            id="drug-b"
            value={drugB}
            onChange={(e) => {
              setDrugB(e.target.value);
              setFocusedField("b");
              setState({ status: "idle" });
            }}
            onFocus={() => setFocusedField("b")}
            onBlur={() => {
              window.setTimeout(() => setFocusedField(null), 120);
            }}
            placeholder="Start typing to search..."
            autoComplete="off"
            className="w-full rounded-2xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-500 focus:border-amber-500 focus:ring-2 focus:ring-amber-300"
          />
          {focusedField === "b" &&
            renderSuggestions(filteredSubstancesB, (value) => {
              setDrugB(value);
              setFocusedField(null);
            })}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-300 bg-white/80 p-4">
        <div className="mb-2 flex flex-wrap gap-2">
          {drugA && (
            <span className="inline-flex rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-100">
              A: {drugA}
            </span>
          )}
          {drugB && (
            <span className="inline-flex rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-100">
              B: {drugB}
            </span>
          )}
        </div>

        <p className="text-sm leading-6 text-slate-800">
          Graph-backed interaction engine. Results do not replace clinical
          judgment or official prescribing guidance.
        </p>
      </div>

      <button
        type="submit"
        disabled={state.status === "loading"}
        className="inline-flex w-full items-center justify-center rounded-2xl bg-amber-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {state.status === "loading" ? "Checking..." : "Check interaction"}
      </button>

      <div aria-live="polite">{getResultCard()}</div>
    </form>
  );
}
