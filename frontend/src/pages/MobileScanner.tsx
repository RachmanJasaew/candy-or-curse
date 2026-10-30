/**
 * Mobile Candy Scanner Page (`/scan/:sessionId`) (Developer A1 + A2)
 * Supports smartphone camera snapshot (`getUserMedia` / `capture="environment"`)
 * and instant GREEN / RED / YELLOW classification overlay.
 */
import React, { useRef, useState } from "react";
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
        "Camera preview requires HTTPS or permission. Use the 'Take Photo / Upload Candy Picture' button below!"
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

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await submitScan(file);
  };

  const submitScan = async (fileOrBase64: File | string, demoHint?: string) => {
    setScanning(true);
    try {
      const res = await scanCandyImage(sessionId, fileOrBase64, demoHint);
      setScanResult(res);
      void speakCandyKeeperText(res.keeper_spoken_summary);
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0c0714] p-4 text-amber-50">
      <header className="flex items-center justify-between border-b border-orange-500/30 pb-3">
        <div>
          <h1 className="text-xl font-black text-orange-400">🎃 Candy Scanner</h1>
          <p className="text-xs text-amber-200/70">Session: {sessionId}</p>
        </div>
        <Link
          to="/"
          className="rounded-lg border border-white/20 px-3 py-1 text-xs text-amber-200"
        >
          Desktop View
        </Link>
      </header>

      {/* Active Restrictions Banner */}
      {session && (
        <div className="mt-3 rounded-xl border border-orange-500/30 bg-orange-950/30 p-3">
          <p className="text-[11px] font-bold uppercase text-orange-300">
            Checking Against Your Restrictions:
          </p>
          <div className="mt-1 flex flex-wrap gap-1.5">
            {session.dietary_profile.parsed_restrictions.map((r) => (
              <span
                key={r}
                className="rounded-full bg-orange-500/20 px-2.5 py-0.5 text-xs font-bold text-orange-200"
              >
                {r.replace("_", " ")}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Camera / Upload Controls */}
      <div className="mt-4 space-y-4">
        {scanResult ? (
          <ClassificationOverlay
            result={scanResult}
            onDismiss={() => setScanResult(null)}
          />
        ) : (
          <div className="rounded-2xl border border-purple-500/40 bg-purple-950/30 p-4 text-center">
            <video
              ref={videoRef}
              playsInline
              muted
              className={`mx-auto w-full max-w-sm rounded-xl bg-black ${
                cameraActive ? "block" : "hidden"
              }`}
            />

            {!cameraActive ? (
              <button
                type="button"
                onClick={() => void startCamera()}
                className="w-full rounded-xl bg-purple-700 py-3 text-sm font-bold text-white hover:bg-purple-600"
              >
                📷 Start Live Camera Preview
              </button>
            ) : (
              <button
                type="button"
                disabled={scanning}
                onClick={() => void captureSnapshot()}
                className="mt-3 w-full rounded-xl bg-orange-500 py-3 text-base font-black text-black"
              >
                {scanning ? "🔮 Consulting Gemma 4..." : "📸 Capture Candy Wrapper"}
              </button>
            )}

            {/* Native Mobile Camera / File Input (Works even without WebRTC preview) */}
            <label className="mt-3 block cursor-pointer rounded-xl border-2 border-dashed border-orange-400/50 bg-orange-500/10 py-4 text-sm font-bold text-orange-300 hover:bg-orange-500/20">
              {scanning ? "🔮 Analyzing Wrapper..." : "📁 Take Photo / Upload Candy Image"}
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(e) => void handleFileChange(e)}
                className="hidden"
              />
            </label>

            {/* Quick Demo Triggers for Hackathon Presentation */}
            <div className="mt-5 border-t border-white/10 pt-4">
              <p className="text-xs font-bold uppercase tracking-wider text-amber-200/70">
                Quick Demo Candy Presets (Gemma + Verified DB):
              </p>
              <div className="mt-2 grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => void submitScan("dGVzdA==", "capri-sun-multivitamin")}
                  className="rounded-lg bg-emerald-600/30 border border-emerald-400/50 p-2 text-xs font-bold text-emerald-200"
                >
                  🟢 Capri-Sun
                </button>
                <button
                  type="button"
                  onClick={() => void submitScan("dGVzdA==", "haribo-goldbears")}
                  className="rounded-lg bg-rose-600/30 border border-rose-400/50 p-2 text-xs font-bold text-rose-200"
                >
                  🔴 Haribo
                </button>
                <button
                  type="button"
                  onClick={() => void submitScan("dGVzdA==", "unknown")}
                  className="rounded-lg bg-amber-600/30 border border-amber-400/50 p-2 text-xs font-bold text-amber-200"
                >
                  🟡 Mystery
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
