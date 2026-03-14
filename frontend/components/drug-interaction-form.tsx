"use client";

import * as React from "react";

import { Input, Button, Label, Alert, AlertDescription, AlertTitle } from "./ui";

const AlertCircle = (props: any) => <span {...props} />;
const Info = (props: any) => <span {...props} />;
const TriangleAlert = (props: any) => <span {...props} />;

type InteractionResponse = {
  drug_a: string;
  drug_b: string;
  risk_level: string;
  mechanism: string;
};

type DrugInteractionFormProps = {
  /** Base URL of the FastAPI service, e.g. "http://localhost:8000". */
  apiBaseUrl: string;
  /**
   * Optional list of known substances to power simple autocomplete.
   * In a later phase this can be replaced with a live search endpoint.
   */
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

export function DrugInteractionForm({
  apiBaseUrl,
  substances = DEFAULT_SUBSTANCES,
}: DrugInteractionFormProps) {
  const [drugA, setDrugA] = React.useState("");
  const [drugB, setDrugB] = React.useState("");
  const [state, setState] = React.useState({ status: "idle" } as InteractionState);

  const [focusedField, setFocusedField] = React.useState<"a" | "b" | null>(null);

  const filteredSubstancesA = React.useMemo(
    () =>
      substances.filter((s) =>
        s.toLowerCase().includes(drugA.toLowerCase())
      ),
    [substances, drugA]
  );

  const filteredSubstancesB = React.useMemo(
    () =>
      substances.filter((s) =>
        s.toLowerCase().includes(drugB.toLowerCase())
      ),
    [substances, drugB]
  );

  const handleSubmit = async (event: any) => {
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

    setState({ status: "loading" });

    try {
      const url = new URL("/interaction", apiBaseUrl);
      url.searchParams.set("drug_a", trimmedA);
      url.searchParams.set("drug_b", trimmedB);

      const res = await fetch(url.toString(), {
        method: "GET",
      });

      if (res.status === 404) {
        setState({ status: "not_found" });
        return;
      }

      if (!res.ok) {
        const body = await res.json().catch(() => null as unknown);
        const detail =
          (body as { detail?: string } | null)?.detail ??
          "Unexpected error while checking interaction.";
        setState({ status: "error", message: detail });
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
  };

  const renderAlert = () => {
    if (state.status === "idle") return null;

    if (state.status === "loading") {
      return (
        <Alert className="border-blue-500/80 bg-blue-50 text-blue-900">
          <Info className="h-4 w-4" />
          <AlertTitle>Checking interaction…</AlertTitle>
          <AlertDescription>
            Querying the interaction graph. This should only take a moment.
          </AlertDescription>
        </Alert>
      );
    }

    if (state.status === "not_found") {
      return (
        <Alert className="border-emerald-500/80 bg-emerald-50 text-emerald-900">
          <Info className="h-4 w-4" />
          <AlertTitle>No known interaction</AlertTitle>
          <AlertDescription>
            There is no documented interaction between these substances in the current
            graph. This does not guarantee safety—always consult clinical guidance.
          </AlertDescription>
        </Alert>
      );
    }

    if (state.status === "error") {
      return (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Something went wrong</AlertTitle>
          <AlertDescription>{state.message}</AlertDescription>
        </Alert>
      );
    }

    if (state.status === "success") {
      const { data } = state;
      const risk = data.risk_level?.toLowerCase();

      const isDangerous =
        risk === "dangerous" || risk === "high" || risk === "contraindicated";
      const isCaution =
        !isDangerous &&
        (risk === "caution" ||
          risk === "moderate" ||
          risk === "monitor");

      if (isDangerous) {
        return (
          <Alert variant="destructive">
            <TriangleAlert className="h-4 w-4" />
            <AlertTitle>Dangerous interaction</AlertTitle>
            <AlertDescription>
              {data.mechanism ||
                "This combination is flagged as dangerous in the interaction graph."}
            </AlertDescription>
          </Alert>
        );
      }

      if (isCaution) {
        return (
          <Alert className="border-yellow-500/80 bg-yellow-50 text-yellow-900">
            <TriangleAlert className="h-4 w-4" />
            <AlertTitle>Caution advised</AlertTitle>
            <AlertDescription>
              {data.mechanism ||
                "Use with caution. Consider dose adjustment, monitoring, or alternatives."}
            </AlertDescription>
          </Alert>
        );
      }

      return (
        <Alert className="border-emerald-500/80 bg-emerald-50 text-emerald-900">
          <Info className="h-4 w-4" />
          <AlertTitle>No significant risk recorded</AlertTitle>
          <AlertDescription>
            {data.mechanism ||
              "There is no significant interaction risk recorded for this combination in the graph."}
          </AlertDescription>
        </Alert>
      );
    }

    return null;
  };

  const renderAutocompleteList = (
    items: string[],
    onSelect: (value: string) => void
  ) => {
    if (!items.length) return null;

    return (
      <div className="mt-1 max-h-40 overflow-y-auto rounded-md border bg-background text-sm shadow-sm">
        {items.map((item) => (
          <button
            key={item}
            type="button"
            className="flex w-full cursor-pointer items-center px-2 py-1.5 text-left hover:bg-muted"
            onClick={() => onSelect(item)}
          >
            {item}
          </button>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-4 rounded-lg border bg-card p-4 shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="drug-a">Substance A</Label>
            <Input
              id="drug-a"
              value={drugA}
              onChange={(e: { target: { value: string } }) => {
                setDrugA(e.target.value);
                setFocusedField("a");
              }}
              onFocus={() => setFocusedField("a")}
              placeholder="Start typing to search…"
              autoComplete="off"
            />
            {focusedField === "a" &&
              renderAutocompleteList(filteredSubstancesA, (value) => {
                setDrugA(value);
                setFocusedField(null);
              })}
          </div>

          <div>
            <Label htmlFor="drug-b">Substance B</Label>
            <Input
              id="drug-b"
              value={drugB}
              onChange={(e: { target: { value: string } }) => {
                setDrugB(e.target.value);
                setFocusedField("b");
              }}
              onFocus={() => setFocusedField("b")}
              placeholder="Start typing to search…"
              autoComplete="off"
            />
            {focusedField === "b" &&
              renderAutocompleteList(filteredSubstancesB, (value) => {
                setDrugB(value);
                setFocusedField(null);
              })}
          </div>
        </div>

        <div className="flex items-center justify-between gap-2">
          <p className="text-xs text-muted-foreground">
            Graph-backed interaction engine. Results do not replace clinical judgment.
          </p>
          <Button type="submit" disabled={state.status === "loading"}>
            {state.status === "loading" ? "Checking…" : "Check interaction"}
          </Button>
        </div>
      </form>

      {renderAlert()}
    </div>
  );
}

