"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";

const DISCLAIMER =
  "Colorimetric testing is presumptive and subject to contamination errors.";

type Match = { substance: string; probability: number };
type ColorResult = { hex: string; label: string | null; matches: Match[] };
type AnalysisResult = {
  description: string | null;
  labels: string[];
  colors: ColorResult[];
};

type Message =
  | { role: "user"; type: "image"; label: string; description?: string }
  | { role: "assistant"; type: "analysis"; data: AnalysisResult }
  | { role: "assistant"; type: "error"; message: string };

/** SetState accepts either a value or updater (project React types may omit updater form). */
type SetState<T> = (value: T | ((prev: T) => T)) => void;

function HorizontalBarChart({ matches }: { matches: Match[] }) {
  return (
    <div className="space-y-2">
      {matches.map((m, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="w-40 shrink-0 truncate text-sm font-medium text-stone-700" title={m.substance}>
            {m.substance}
          </span>
          <div className="min-w-[100px] flex-1 rounded-full bg-stone-200">
            <div
              className="h-5 rounded-full bg-cyan-500 transition-all"
              style={{ width: `${Math.min(100, m.probability)}%`, minWidth: m.probability > 0 ? "4px" : 0 }}
            />
          </div>
          <span className="w-12 shrink-0 text-right text-sm tabular-nums text-stone-600">
            {m.probability}%
          </span>
        </div>
      ))}
    </div>
  );
}

export function ReagentChat({ apiBaseUrl }: { apiBaseUrl: string }) {
  const [messages, setMessagesState] = React.useState<Message[]>([]);
  const setMessages = setMessagesState as SetState<Message[]>;
  const [uploading, setUploading] = React.useState(false);
  const [fileInputEl, setFileInputEl] = React.useState<HTMLInputElement | null>(null);
  const [promptText, setPromptText] = React.useState("");

  const backendUrl = (() => {
    const s = (apiBaseUrl || "").trim();
    return s && s.startsWith("http") ? s : "http://localhost:8000";
  })();

  async function handleFile(e: { target: HTMLInputElement }) {
    const file = e.target.files?.[0];
    if (!file || !file.type.startsWith("image/")) return;
    e.target.value = "";

    const description = promptText.trim();
    setMessages((prev) => [
      ...prev,
      { role: "user", type: "image", label: file.name, description: description || undefined },
    ]);
    setUploading(true);

    try {
      const form = new FormData();
      form.append("image", file);
      if (description) form.append("prompt", description);
      const res = await fetch(`${backendUrl}/reagent/analyze`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        let msg: string;
        const contentType = res.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          const err = await res.json().catch(() => ({}));
          msg = (err as { detail?: string }).detail || `Request failed: ${res.status}`;
        } else {
          const text = await res.text();
          if (res.status === 404) {
            msg = "Reagent analysis endpoint not found (404). Is the backend running at the correct URL and does it expose POST /reagent/analyze?";
          } else if (text && text.length < 200) {
            msg = text;
          } else {
            msg = `Request failed: ${res.status}. ${res.status === 503 ? "Vision service may be unavailable (check OPENAI_API_KEY)." : ""}`;
          }
        }
        setMessages((prev) => [
          ...prev,
          { role: "assistant", type: "error", message: msg },
        ]);
        return;
      }

      let data: AnalysisResult = await res.json();
      // Normalize legacy response { hex, matches } to { description, labels, colors }
      if (data && "hex" in data && "matches" in data && !("colors" in data && Array.isArray((data as AnalysisResult).colors))) {
        const leg = data as { hex: string; matches: Match[] };
        data = { description: null, labels: [], colors: [{ hex: leg.hex, label: null, matches: leg.matches }] };
      }
      setMessages((prev) => [
        ...prev,
        { role: "assistant", type: "analysis", data },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          type: "error",
          message: message.includes("fetch") || message.includes("Failed to fetch")
            ? "Network error. Is the backend running at the URL shown on this page?"
            : `Error: ${message}`,
        },
      ]);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-xl border border-stone-200 bg-white shadow-sm">
        <div className="border-b border-stone-100 p-3">
          <p className="text-sm text-stone-500">Chat</p>
        </div>
        <div className="min-h-[200px] max-h-[400px] overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <p className="text-sm text-stone-400">
              Upload a reagent test image to see color-based substance suggestions.
            </p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={
                msg.role === "user"
                  ? "flex justify-end"
                  : "flex justify-start"
              }
            >
              <div
                className={
                  msg.role === "user"
                    ? "rounded-lg bg-cyan-500/20 px-3 py-2 text-sm text-cyan-900"
                    : "max-w-full rounded-lg border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                }
              >
                {msg.role === "user" && msg.type === "image" && (
                  <div>
                    <span>📷 {msg.label}</span>
                    {msg.description && (
                      <p className="mt-1 text-cyan-800/90 text-xs">“{msg.description}”</p>
                    )}
                  </div>
                )}
                {msg.role === "assistant" && msg.type === "analysis" && (
                  <div className="space-y-3">
                    {msg.data.description && (
                      <p className="text-stone-600">{msg.data.description}</p>
                    )}
                    {msg.data.labels && msg.data.labels.length > 0 && (
                      <p className="text-sm text-stone-500">
                        Visible labels: {msg.data.labels.join(", ")}
                      </p>
                    )}
                    {(msg.data.colors || []).map((color, idx) => (
                      <div key={idx} className="rounded border border-stone-200 bg-white p-2">
                        <p className="text-stone-600">
                          {color.label ? (
                            <span className="font-medium">{color.label}: </span>
                          ) : null}
                          <span className="font-mono font-medium" style={{ color: color.hex }}>{color.hex}</span>
                        </p>
                        <HorizontalBarChart matches={color.matches} />
                      </div>
                    ))}
                    <p className="mt-3 text-xs italic text-amber-700 border-t border-amber-200 pt-2">
                      {DISCLAIMER}
                    </p>
                  </div>
                )}
                {msg.role === "assistant" && msg.type === "error" && (
                  <p className="text-red-600">{msg.message}</p>
                )}
              </div>
            </div>
          ))}
          {uploading && (
            <div className="flex justify-start">
              <div className="rounded-lg border border-stone-200 bg-stone-50 px-4 py-2 text-sm text-stone-500">
                Analyzing image…
              </div>
            </div>
          )}
        </div>
        <div className="border-t border-stone-100 p-3 space-y-2">
          <textarea
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder="Describe what’s in the image (optional): e.g. Marquis reagent, left tube; or Ehrlich test."
            className="w-full rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-800 placeholder:text-stone-400 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
            rows={2}
            maxLength={500}
            disabled={uploading}
            aria-label="Description of what is in the image"
          />
          <div className="flex items-center gap-2">
            <input
              ref={(el) => setFileInputEl(el)}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFile}
              className="hidden"
              aria-label="Upload reagent test image"
            />
            <Button
              type="button"
              onClick={() => fileInputEl?.click()}
              disabled={uploading}
              className="rounded-lg bg-cyan-600 px-4 py-2 text-sm text-white hover:bg-cyan-700 disabled:opacity-50"
            >
              {uploading ? "Uploading…" : "Upload image"}
            </Button>
            <span className="text-xs text-stone-500">JPEG, PNG or WebP (max 10 MB)</span>
          </div>
        </div>
      </div>
      <p className="text-xs text-stone-500 text-center">
        {DISCLAIMER}
      </p>
    </div>
  );
}
