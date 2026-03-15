"use client";

import * as React from "react";
import { Button } from "./ui/button";

export type RiskWarningProps = {
  /** List of adverse effects to display in the warning. */
  adverse_effects: string[];
  /** Called when the user has checked the box and acknowledged the warning (modal can close). */
  onAcknowledge: () => void;
};

/**
 * Modal that obscures underlying content (e.g. dosage data). The user must check
 * "I understand the neurological and physiological risks" before the modal can be closed.
 */
export function RiskWarning({ adverse_effects, onAcknowledge }: RiskWarningProps) {
  const [checked, setChecked] = React.useState(false);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/80 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="risk-warning-title"
    >
      <div className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border border-stone-200 bg-white p-6 shadow-xl">
        <h2 id="risk-warning-title" className="text-lg font-semibold text-stone-800">
          Reconsider: risks and downsides
        </h2>
        <p className="mt-2 text-sm text-stone-600">
          This substance carries notable risks. Before viewing dosage or use information, please review the following potential adverse effects:
        </p>
        {adverse_effects.length > 0 ? (
          <ul className="mt-3 list-inside list-disc space-y-1 text-sm text-stone-700">
            {adverse_effects.map((effect, i) => (
              <li key={i}>{effect}</li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-stone-500 italic">No specific adverse effects listed.</p>
        )}
        <label className="mt-6 flex cursor-pointer items-start gap-3">
          <input
            type="checkbox"
            checked={checked}
            onChange={(e) => setChecked(e.target.checked)}
            className="mt-1 h-4 w-4 rounded border-stone-300"
            aria-describedby="risk-warning-title"
          />
          <span className="text-sm text-stone-700">
            I understand the neurological and physiological risks.
          </span>
        </label>
        <div className="mt-6 flex justify-end">
          <Button
            type="button"
            onClick={onAcknowledge}
            disabled={!checked}
            className="min-w-[120px]"
          >
            Continue
          </Button>
        </div>
      </div>
    </div>
  );
}
