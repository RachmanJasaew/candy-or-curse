/**
 * Mobile Food & Candy Scanner (`/scan/:sessionId`) — Developer A1
 * Supports:
 * 1. Live Stream Mode with conversational ElevenLabs feedback ("Okay, turn it around. Let me see the ingredients.")
 * 2. Front-of-pack OR Back-of-pack (Ingredient Label OCR) photo capture
 * 3. Direct Ingredient List text input (German & English)
 * 4. Clickable Recommended Alternatives when a product is RED
 */
import React, { useEffect, useRef, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { scanCandyImage } from "../api/client";
import { ClassificationOverlay } from "../components/ClassificationOverlay";
import { useSessionSync } from "../hooks/useSessionSync";
import { speakCandyKeeperText } from "../services/voiceRecorder";
import { ScanResult } from "../types/api";

export const MobileScanner: React.FC = () => {
  const { sessionId = "sess_demo1031" } = useParams<{ sessionId: string }>();
  const { session } = useSessionSync(sessionId, 0);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [scanning, setScanning] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [liveStreamMode, setLiveStreamMode] = useState(false);
  const [ingredientText, setIngredientText] = useState("");
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setCameraActive(true);
      }
    } catch {
      alert(
        "Camera preview requires HTTPS or permission. Use the 'Take Photo' button or 'Ingredient List' box below!"
      );
    }
  };

  const captureSnapshot = async () => {
    if (!videoRef.current) return;
    const canvas = document.createElement("canvas");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
    await submitScan(dataUrl);
  };

  useEffect(() => {
    if (!liveStreamMode || !cameraActive) return;
    const interval = window.setInterval(() => {
      if (!scanning) {
        void captureSnapshot();
      }
    }, 4000);
    return () => window.clearInterval(interval);
  }, [liveStreamMode, cameraActive, scanning]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await submitScan(file);
  };

  const submitScan = async (
    fileOrBase64?: File | string,
    demoHint?: string,
    customIngredients?: string
  ) => {
    setScanning(true);
    try {
      const res = await scanCandyImage(
        sessionId,
        fileOrBase64,
        demoHint,
        customIngredients
      );
      setScanResult(res);
      void speakCandyKeeperText(res.keeper_spoken_summary);
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#17092b] via-[#0c0714] to-black p-4 text-amber-50">
      <header className="mx-auto flex max-w-lg items-center justify-between border-b border-orange-500/30 pb-3">
        <div>
          <h1 className="text-xl font-black text-orange-400">
            🎃 Live Food &amp; Candy Scanner
          </h1>
          <p className="text-xs font-mono text-amber-200/70">Session: {sessionId}</p>
        </div>
        <Link
          to="/"
          className="rounded-xl border border-orange-400/40 bg-orange-500/20 px-3 py-1.5 text-xs font-bold text-orange-200"
        >
          ← Desktop Station
        </Link>
      </header>

      <div className="mx-auto mt-3 max-w-lg space-y-4">
        {/* Active Restrictions Banner */}
        {session && (
          <div className="rounded-2xl border border-orange-500/30 bg-orange-950/30 p-3">
            <p className="text-[11px] font-extrabold uppercase tracking-wider text-orange-300">
              Checking Against Your Profile:
            </p>
            <div className="mt-1.5 flex flex-wrap gap-1.5">
              {session.dietary_profile.parsed_restrictions.map((r) => (
                <span
                  key={r}
                  className="rounded-full bg-orange-500/25 border border-orange-400/40 px-2.5 py-0.5 text-xs font-bold text-orange-200"
                >
                  {r === "eat_everything" ? "✅ Eat Everything" : `⚠️ ${r.replace(/_/g, " ")}`}
                </span>
              ))}
            </div>
          </div>
        )}

        {scanResult ? (
          <ClassificationOverlay
            result={scanResult}
            onDismiss={() => setScanResult(null)}
            onSelectAlternative={(prodId) => void submitScan("dGVzdA==", prodId)}
          />
        ) : (
          <div className="rounded-3xl border border-purple-500/40 bg-purple-950/30 p-4 text-center shadow-2xl">
            <div className="relative mx-auto max-w-sm overflow-hidden rounded-2xl">
              <video
                ref={videoRef}
                playsInline
                muted
                className={`w-full rounded-2xl bg-black ${
                  cameraActive ? "block" : "hidden"
                }`}
              />
              {cameraActive && (
                <div className="pointer-events-none absolute inset-0 border-2 border-orange-400/60 rounded-2xl">
                  <div className="w-full h-0.5 bg-orange-400 shadow-[0_0_12px_#f97316] animate-bounce" />
                </div>
              )}
            </div>

            {!cameraActive ? (
              <button
                type="button"
                onClick={() => void startCamera()}
                className="w-full rounded-2xl bg-gradient-to-r from-purple-700 to-indigo-700 py-3.5 text-sm font-black text-white shadow-lg hover:from-purple-600 hover:to-indigo-600"
              >
                📷 Start Live Camera (Front or Ingredient Label)
              </button>
            ) : (
              <div className="mt-3 space-y-2">
                <button
                  type="button"
                  disabled={scanning}
                  onClick={() => void captureSnapshot()}
                  className="w-full rounded-2xl bg-orange-500 py-3.5 text-base font-black text-black shadow-lg"
                >
                  {scanning
                    ? "🔮 Gemma 4 Analyzing..."
                    : "📸 Snap Front OR Back Ingredient List"}
                </button>
                <button
                  type="button"
                  onClick={() => setLiveStreamMode((prev) => !prev)}
                  className={`w-full rounded-2xl py-2.5 text-xs font-extrabold ${
                    liveStreamMode
                      ? "animate-pulse bg-rose-600 text-white"
                      : "bg-white/10 text-amber-200 hover:bg-white/20"
                  }`}
                >
                  {liveStreamMode
                    ? "🔴 Live Stream ON — AI Coach Speaking Back"
                    : "▶️ Turn On Continuous Live Stream & Voice Coach"}
                </button>
              </div>
            )}

            {/* Native Mobile Camera / File Input */}
            <label className="mt-3 block cursor-pointer rounded-2xl border-2 border-dashed border-orange-400/50 bg-orange-500/10 py-3.5 text-sm font-extrabold text-orange-300 hover:bg-orange-500/20">
              {scanning ? "🔮 Reading Package..." : "📁 Take Photo / Upload Food Picture"}
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(e) => void handleFileChange(e)}
                className="hidden"
              />
            </label>

            {/* Direct Ingredient List Input (German or English) */}
            <div className="mt-4 rounded-2xl border border-purple-400/30 bg-black/45 p-3.5 text-left">
              <label className="block text-xs font-extrabold uppercase tracking-wider text-purple-300">
                📝 Or Paste / Type Ingredient List (DE / EN):
              </label>
              <div className="mt-2 flex gap-2">
                <input
                  type="text"
                  value={ingredientText}
                  onChange={(e) => setIngredientText(e.target.value)}
                  placeholder="e.g. Zutaten: Zucker, Schweinegelatine, Erdnüsse..."
                  className="flex-1 rounded-xl border border-white/20 bg-black/60 px-3 py-2 text-xs text-white"
                />
                <button
                  type="button"
                  disabled={!ingredientText.trim() || scanning}
                  onClick={() =>
                    void submitScan(undefined, undefined, ingredientText)
                  }
                  className="rounded-xl bg-purple-600 px-3.5 py-2 text-xs font-black text-white disabled:opacity-40"
                >
                  Check
                </button>
              </div>
            </div>

            {/* Quick Demo Triggers */}
            <div className="mt-5 border-t border-white/10 pt-4">
              <p className="text-xs font-extrabold uppercase tracking-wider text-amber-200/70">
                ⚡ Test Any Product Scenario Instantly:
              </p>
              <div className="mt-2 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => void submitScan("dGVzdA==", "capri-sun-multivitamin")}
                  className="rounded-xl bg-emerald-600/30 border border-emerald-400/50 p-2.5 text-xs font-bold text-emerald-200"
                >
                  🟢 Capri-Sun (OK)
                </button>
                <button
                  type="button"
                  onClick={() => void submitScan("dGVzdA==", "haribo-goldbears")}
                  className="rounded-xl bg-rose-600/30 border border-rose-400/50 p-2.5 text-xs font-bold text-rose-200"
                >
                  🔴 Haribo (+Alts)
                </button>
                <button
                  type="button"
                  onClick={() => void submitScan("dGVzdA==", "nutella-original")}
                  className="rounded-xl bg-rose-600/30 border border-rose-400/50 p-2.5 text-xs font-bold text-rose-200"
                >
                  🔴 Nutella (Hazelnuts)
                </button>
                <button
                  type="button"
                  onClick={() => void submitScan("dGVzdA==", "water-bottle-front")}
                  className="rounded-xl bg-amber-600/30 border border-amber-400/50 p-2.5 text-xs font-bold text-amber-200"
                >
                  🟡 Water Bottle (&ldquo;Turn Around!&rdquo;)
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
