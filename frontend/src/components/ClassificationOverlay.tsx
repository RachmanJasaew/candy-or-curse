/**
 * GREEN / RED / YELLOW Candy Classification Overlay (Developer A1)
 */
import React from "react";
import { ScanResult } from "../types/api";

interface Props {
  result: ScanResult;
  onDismiss?: () => void;
}

const STATUS_STYLES = {
  GREEN: {
    border: "border-emerald-400",
    bg: "bg-emerald-950/90",
    badge: "bg-emerald-500 text-black",
    label: "GREEN — NO KNOWN CONFLICTS",
  },
  RED: {
    border: "border-rose-500",
    bg: "bg-rose-950/95",
    badge: "bg-rose-600 text-white",
    label: "RED — VERIFIED CONFLICT (CURSE!)",
  },
  YELLOW: {
    border: "border-amber-400",
    bg: "bg-amber-950/95",
    badge: "bg-amber-400 text-black",
    label: "YELLOW — INSUFFICIENT / UNCERTAIN DATA",
  },
};

export const ClassificationOverlay: React.FC<Props> = ({ result, onDismiss }) => {
  const style = STATUS_STYLES[result.classification];

  return (
    <div
      className={`rounded-2xl border-2 ${style.border} ${style.bg} p-5 shadow-2xl transition-all`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className={`rounded-full px-3 py-1 text-xs font-extrabold tracking-wider ${style.badge}`}>
          {style.label}
        </span>
        <span className="text-xs text-amber-200/70">
          Confidence: {Math.round(result.recognized_product.confidence * 100)}%
        </span>
      </div>

      <h3 className="mt-3 text-xl font-black text-white">{result.headline}</h3>
      <p className="mt-1 text-sm font-semibold text-amber-200">
        Product: {result.recognized_product.name}{" "}
        {result.recognized_product.brand ? `(${result.recognized_product.brand})` : ""}
      </p>

      <p className="mt-3 text-sm leading-relaxed text-amber-50">{result.explanation}</p>

      {result.conflicting_ingredients.length > 0 && (
        <div className="mt-4 rounded-xl bg-black/40 p-3">
          <p className="text-xs font-bold uppercase tracking-wider text-rose-300">
            Conflicting Ingredients Detected:
          </p>
          <ul className="mt-1 list-inside list-disc text-sm text-rose-100">
            {result.conflicting_ingredients.map((ing) => (
              <li key={ing}>{ing}</li>
            ))}
          </ul>
        </div>
      )}

      {result.uncertainty.is_uncertain && result.uncertainty.reasons.length > 0 && (
        <div className="mt-4 rounded-xl bg-black/40 p-3">
          <p className="text-xs font-bold uppercase tracking-wider text-amber-300">
            Why This Is Uncertain:
          </p>
          <ul className="mt-1 list-inside list-disc text-sm text-amber-100">
            {result.uncertainty.reasons.map((reason, idx) => (
              <li key={idx}>{reason}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="mt-4 border-t border-white/15 pt-2 text-[11px] text-amber-100/70">
        {result.safety_disclaimer}
      </p>

      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="mt-4 w-full rounded-xl bg-white/15 py-2.5 text-sm font-bold text-white hover:bg-white/25"
        >
          Scan Another Treat
        </button>
      )}
    </div>
  );
};
