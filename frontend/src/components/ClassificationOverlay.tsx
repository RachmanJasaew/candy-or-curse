/**
 * GREEN / RED / YELLOW Candy & Food Classification Overlay (Developer A1)
 * Includes animated status header, conflicting ingredient pills,
 * Recommended Alternatives (when RED), and "Turn it around" Voice Coach banner (when YELLOW).
 */
import React from "react";
import { ScanResult } from "../types/api";

interface Props {
  result: ScanResult;
  onDismiss?: () => void;
  onSelectAlternative?: (productId: string) => void;
}

const STATUS_STYLES = {
  GREEN: {
    border: "border-emerald-400 shadow-[0_0_35px_rgba(16,185,129,0.35)]",
    bg: "bg-gradient-to-br from-emerald-950/95 via-[#07261d] to-black/95",
    badge: "bg-emerald-400 text-black",
    icon: "🍬",
    label: "GREEN — SAFE FOR YOUR PREFERENCES",
  },
  RED: {
    border: "border-rose-500 shadow-[0_0_40px_rgba(244,63,94,0.45)]",
    bg: "bg-gradient-to-br from-rose-950/95 via-[#2a0813] to-black/95",
    badge: "bg-rose-500 text-white",
    icon: "💀",
    label: "RED — CURSED / NOT RECOMMENDED",
  },
  YELLOW: {
    border: "border-amber-400 shadow-[0_0_35px_rgba(251,191,36,0.35)]",
    bg: "bg-gradient-to-br from-amber-950/95 via-[#291b06] to-black/95",
    badge: "bg-amber-400 text-black",
    icon: "🔮",
    label: "YELLOW — TURN PRODUCT AROUND / UNCERTAIN",
  },
};

export const ClassificationOverlay: React.FC<Props> = ({
  result,
  onDismiss,
  onSelectAlternative,
}) => {
  const style = STATUS_STYLES[result.classification];

  return (
    <div
      className={`rounded-3xl border-2 ${style.border} ${style.bg} p-5 transition-all duration-300`}
    >
      {/* Top Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1 text-xs font-black tracking-wider ${style.badge}`}
        >
          <span>{style.icon}</span>
          <span>{style.label}</span>
        </span>
        <span className="rounded-full bg-white/10 px-2.5 py-0.5 text-[11px] font-mono text-amber-200/80">
          {result.ingredient_source.replace(/_/g, " ")} •{" "}
          {Math.round(result.recognized_product.confidence * 100)}% conf
        </span>
      </div>

      {/* Headline & Product Identity */}
      <h3 className="mt-3 text-2xl font-black tracking-tight text-white">
        {result.headline}
      </h3>
      <p className="mt-1 text-sm font-bold text-amber-300">
        {result.recognized_product.name}{" "}
        {result.recognized_product.brand ? (
          <span className="text-amber-200/70">• {result.recognized_product.brand}</span>
        ) : null}
      </p>

      {/* Conversational AI Voice Coach Prompt ("Okay, turn it around. Let me see the ingredients.") */}
      {result.agent_guidance_prompt && (
        <div className="mt-4 flex items-center gap-3 rounded-2xl border border-amber-300/60 bg-amber-400/20 p-3.5 text-sm font-extrabold text-amber-100 animate-pulse">
          <span className="text-2xl">🔄</span>
          <div>
            <span className="block text-[10px] uppercase tracking-wider text-amber-300">
              Live Voice Coach (ElevenLabs):
            </span>
            &ldquo;{result.agent_guidance_prompt}&rdquo;
          </div>
        </div>
      )}

      {/* Explanation */}
      <p className="mt-3 text-sm leading-relaxed text-amber-50/90">
        {result.explanation}
      </p>

      {/* Conflicting Ingredients (RED) */}
      {result.conflicting_ingredients.length > 0 && (
        <div className="mt-4 rounded-2xl border border-rose-500/40 bg-black/50 p-3.5">
          <p className="text-xs font-extrabold uppercase tracking-wider text-rose-300">
            ⚠️ Conflicting Ingredients Found:
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {result.conflicting_ingredients.map((ing) => (
              <span
                key={ing}
                className="rounded-lg bg-rose-500/25 border border-rose-400/40 px-2.5 py-1 text-xs font-bold text-rose-100"
              >
                ✕ {ing}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Alternatives (RED) */}
      {result.recommended_alternatives &&
        result.recommended_alternatives.length > 0 && (
          <div className="mt-4 rounded-2xl border border-emerald-400/40 bg-emerald-950/50 p-3.5">
            <p className="text-xs font-extrabold uppercase tracking-wider text-emerald-300">
              ✅ Recommended Similar Alternatives For You:
            </p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {result.recommended_alternatives.map((alt) => (
                <div
                  key={alt.product_id}
                  onClick={() => onSelectAlternative?.(alt.product_id)}
                  className="cursor-pointer rounded-xl border border-emerald-400/25 bg-black/40 p-2.5 text-xs transition hover:border-emerald-400 hover:bg-emerald-900/40"
                >
                  <div className="font-black text-white">{alt.name}</div>
                  <div className="text-[11px] text-emerald-200/70">{alt.brand}</div>
                  <div className="mt-1 text-[11px] text-emerald-300">{alt.reason}</div>
                </div>
              ))}
            </div>
          </div>
        )}

      {/* Verified Ingredients Accordion */}
      {result.verified_ingredients.length > 0 && (
        <details className="mt-3 rounded-xl bg-black/30 p-2.5 text-xs text-amber-100/80">
          <summary className="cursor-pointer font-bold text-amber-200">
            View Full Verified Ingredient List ({result.verified_ingredients.length})
          </summary>
          <p className="mt-2 leading-relaxed">
            {result.verified_ingredients.join(" • ")}
          </p>
        </details>
      )}

      {/* Uncertainty Reasons (YELLOW) */}
      {result.uncertainty.is_uncertain &&
        result.uncertainty.reasons.length > 0 && (
          <div className="mt-4 rounded-2xl bg-black/40 p-3.5">
            <p className="text-xs font-bold uppercase tracking-wider text-amber-300">
              How to Get a Verified Verdict:
            </p>
            <ul className="mt-1.5 list-inside list-disc space-y-1 text-xs text-amber-100">
              {result.uncertainty.reasons.map((reason, idx) => (
                <li key={idx}>{reason}</li>
              ))}
            </ul>
          </div>
        )}

      {/* Safety Disclaimer */}
      <p className="mt-4 border-t border-white/15 pt-2.5 text-[11px] text-amber-100/60">
        🛡️ {result.safety_disclaimer}
      </p>

      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="mt-4 w-full rounded-2xl bg-gradient-to-r from-orange-500 to-amber-500 py-3 text-sm font-black text-black shadow-lg hover:from-orange-400 hover:to-amber-400"
        >
          {result.needs_ingredient_photo
            ? "📸 Flip Product & Scan Ingredient Label Now"
            : "🔍 Scan Another Product"}
        </button>
      )}
    </div>
  );
};
