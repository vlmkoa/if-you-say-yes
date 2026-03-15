"use client";

import * as React from "react";
import {
  AlertCircle,
  ArrowLeftRight,
  CheckCircle2,
  Loader2,
  Search,
  ShieldAlert,
  TriangleAlert,
} from "lucide-react";

type InteractionResponse = {
  drug_a: string;
  drug_b: string;
  risk_level: string;
  mechanism: string;
};

type DrugInteractionFormProps = {
  apiBaseUrl: string;
  substances?: string[];
};

type InteractionState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "not_found" }
  | { status: "error"; message: string }
  | { status: "success"; data: InteractionResponse };

const DEFAULT_SUBSTANCES: string[] = [
  "Warfarin",
  "Ibuprofen",
  "Paracetamol",
  "Aspirin",
  "Atorvastatin",
  "Metformin",
  "Omeprazole",
];

function getFiltered(items: string[], value: string, otherValue: string) {
  return items
    .filter((item) =>
      item.toLowerCase().includes(value.trim().toLowerCase())
    )
    .filter((item) => item.toLowerCase() !== otherValue.trim().toLowerCase())
    .slice(0, 6);
}

export function DrugInteractionForm({
  apiBaseUrl,
  substances = DEFAULT_SUBSTANCES,
}: DrugInteractionFormProps) {
  const [drugA, setDrugA] = React.useState("");
  const [drugB, setDrugB] = React.useState("");
  const [state, setState] = React.useState<InteractionState>({ status: "idle" });
  const [focusedField, setFocusedField] = React.useState<"a" | "b" | null>(null);

  const filteredSubstancesA = React.useMemo(
    () => getFiltered(substances, drugA, drugB),
    [substances, drugA, drugB]
  );

  const filteredSubstancesB = React.useMemo(
    () => getFiltered(substances, drugB, drugA),
    [substances, drugB, drugA]
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
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

    try {
      const url = new URL("/interaction", apiBaseUrl);
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
        <div className="rounded-2xl border border-dashed border-white/10 bg-slate-900/60 p-4 text-sm text-slate-400">
          Choose two substances, then run the interaction check.
        </div>
      );
    }

    if (state.status === "loading") {
      return (
        <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 p-4">
          <div className="flex items-start gap-3">
            <Loader2 className="mt-0.5 h-5 w-5 animate-spin text-cyan-300" />
            <div>
              <p className="font-medium text-cyan-100">Checking interaction</p>
              <p className="mt-1 text-sm text-cyan-50/80">
                Querying the interaction graph. This should only take a moment.
              </p>
            </div>
          </div>
        </div>
      );
    }

    if (state.status === "not_found") {
      return (
        <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-4">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-300" />
            <div>
              <p className="font-medium text-emerald-100">No known interaction</p>
              <p className="mt-1 text-sm text-emerald-50/80">
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
        <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 text-rose-300" />
            <div>
              <p className="font-medium text-rose-100">Something went wrong</p>
              <p className="mt-1 text-sm text-rose-50/80">{state.message}</p>
            </div>
          </div>
        </div>
      );
    }

    const { data } = state;
    const risk = data.risk_level?.toLowerCase() ?? "";

    const isDangerous =
      risk === "dangerous" || risk === "high" || risk === "contraindicated";
    const isCaution =
      !isDangerous &&
      (risk === "caution" || risk === "moderate" || risk === "monitor");

    if (isDangerous) {
      return (
        <div className="rounded-2xl border border-rose-400/20 bg-rose-400/10 p-5">
          <div className="mb-4 flex items-center gap-3">
            <ShieldAlert className="h-5 w-5 text-rose-300" />
            <span className="rounded-full border border-rose-300/20 bg-rose-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-rose-100">
              Dangerous interaction
            </span>
          </div>

          <div className="space-y-3">
            <p className="text-sm text-rose-50/90">
              <span className="font-semibold text-white">Pair:</span> {data.drug_a} +{" "}
              {data.drug_b}
            </p>
            <p className="text-sm text-rose-50/90">
              <span className="font-semibold text-white">Mechanism:</span>{" "}
              {data.mechanism ||
                "This combination is flagged as dangerous in the interaction graph."}
            </p>
          </div>
        </div>
      );
    }

    if (isCaution) {
      return (
        <div className="rounded-2xl border border-amber-400/20 bg-amber-400/10 p-5">
          <div className="mb-4 flex items-center gap-3">
            <TriangleAlert className="h-5 w-5 text-amber-300" />
            <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-100">
              Caution advised
            </span>
          </div>

          <div className="space-y-3">
            <p className="text-sm text-amber-50/90">
              <span className="font-semibold text-white">Pair:</span> {data.drug_a} +{" "}
              {data.drug_b}
            </p>
            <p className="text-sm text-amber-50/90">
              <span className="font-semibold text-white">Mechanism:</span>{" "}
              {data.mechanism ||
                "Use with caution. Consider monitoring, dose adjustment, or alternatives."}
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 p-5">
        <div className="mb-4 flex items-center gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-300" />
          <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-100">
            Low recorded risk
          </span>
        </div>

        <div className="space-y-3">
          <p className="text-sm text-emerald-50/90">
            <span className="font-semibold text-white">Pair:</span> {data.drug_a} +{" "}
            {data.drug_b}
          </p>
          <p className="text-sm text-emerald-50/90">
            <span className="font-semibold text-white">Mechanism:</span>{" "}
            {data.mechanism ||
              "There is no significant interaction risk recorded for this combination in the graph."}
          </p>
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
            <Search className="h-4 w-4 shrink-0 text-cyan-400" />
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
            className="mb-2 block text-sm font-medium text-white"
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
            className="w-full rounded-2xl border border-slate-600 bg-slate-800 px-4 py-3 text-white outline-none transition placeholder:text-slate-400 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30"
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
          className="inline-flex h-12 w-12 items-center justify-center self-end rounded-2xl border border-white/10 bg-white/5 text-slate-200 transition hover:bg-white/10"
          aria-label="Swap substances"
        >
          <ArrowLeftRight className="h-4 w-4" />
        </button>

        <div className="relative">
          <label
            htmlFor="drug-b"
            className="mb-2 block text-sm font-medium text-white"
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
            className="w-full rounded-2xl border border-slate-600 bg-slate-800 px-4 py-3 text-white outline-none transition placeholder:text-slate-400 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/30"
          />
          {focusedField === "b" &&
            renderSuggestions(filteredSubstancesB, (value) => {
              setDrugB(value);
              setFocusedField(null);
            })}
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-slate-900/70 p-4">
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

        <p className="text-sm leading-6 text-slate-400">
          Graph-backed interaction engine. Results do not replace clinical
          judgment or official prescribing guidance.
        </p>
      </div>

      <button
        type="submit"
        disabled={state.status === "loading"}
        className="inline-flex w-full items-center justify-center rounded-2xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {state.status === "loading" ? "Checking..." : "Check interaction"}
      </button>

      <div aria-live="polite">{getResultCard()}</div>
    </form>
  );
}
