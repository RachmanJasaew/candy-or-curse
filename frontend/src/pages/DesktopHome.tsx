/**
 * Desktop Experience — Onboarding Preferences, "The Candy Keeper" Character Stage,
 * Voice/Chat & Live QR Scanner Station (Developer A1)
 */
import React, { useRef, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { scanCandyImage, sendChatMessage } from "../api/client";
import { ClassificationOverlay } from "../components/ClassificationOverlay";
import { useSessionSync } from "../hooks/useSessionSync";
import {
  speakCandyKeeperText,
  VoiceInteractionController,
} from "../services/voiceRecorder";

const QUICK_PREFERENCES = [
  { id: "halal", label: "☪️ Halal", phrase: "I only eat Halal food and avoid gelatin and pork." },
  { id: "vegan", label: "🌱 Vegan", phrase: "I am vegan and avoid gelatin, dairy, and eggs." },
  { id: "vegetarian", label: "🥗 Vegetarian", phrase: "I am vegetarian and avoid gelatin." },
  { id: "no_gelatin", label: "🚫 No Gelatin", phrase: "I strictly avoid gelatin." },
  { id: "peanuts", label: "🥜 Peanut Allergy", phrase: "I have a severe peanut allergy." },
  { id: "tree_nuts", label: "🌰 Hazelnut / Nut Allergy", phrase: "I am allergic to hazelnuts and tree nuts." },
  { id: "gluten", label: "🌾 Gluten-Free", phrase: "I avoid gluten and wheat." },
  { id: "lactose", label: "🥛 Lactose-Free", phrase: "I am lactose intolerant and avoid milk." },
  { id: "eat_everything", label: "🍽️ Eat Everything", phrase: "I eat everything and have no restrictions." },
];

export const DesktopHome: React.FC = () => {
  const { session, setSession } = useSessionSync(undefined, 2500);
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const voiceRef = useRef(new VoiceInteractionController());

  const handleSend = async (textToSend?: string) => {
    const message = (textToSend ?? input).trim();
    if (!message || !session) return;
    setInput("");
    setBusy(true);
    try {
      const res = await sendChatMessage(session.session_id, { message });
      setSession({
        ...session,
        dietary_profile: res.updated_dietary_profile,
        chat_history: [
          ...session.chat_history,
          { role: "user", content: message, timestamp: new Date().toISOString() },
          { role: "assistant", content: res.reply, timestamp: new Date().toISOString() },
        ],
      });
      void speakCandyKeeperText(res.reply);
    } finally {
      setBusy(false);
    }
  };

  const handleQuickDemoScan = async (hint: string) => {
    if (!session) return;
    setBusy(true);
    try {
      const scanRes = await scanCandyImage(session.session_id, "dGVzdA==", hint);
      setSession({
        ...session,
        latest_scan: scanRes,
        scan_history: [scanRes, ...session.scan_history],
      });
      void speakCandyKeeperText(scanRes.keeper_spoken_summary);
    } finally {
      setBusy(false);
    }
  };

  const toggleMicrophone = async () => {
    if (!isRecording) {
      await voiceRef.current.startRecording();
      setIsRecording(true);
    } else {
      setIsRecording(false);
      setBusy(true);
      try {
        const transcript = await voiceRef.current.stopAndTranscribe();
        if (transcript) {
          await handleSend(transcript);
        }
      } finally {
        setBusy(false);
      }
    }
  };

  const publicOrigin =
    import.meta.env.VITE_PUBLIC_APP_URL ||
    (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");

  const qrUrl = session
    ? `${publicOrigin.replace(/\/$/, "")}/scan/${session.session_id}`
    : `${publicOrigin}/scan/sess_demo1031`;

  const latestStatus = session?.latest_scan?.classification;
  const keeperAvatar =
    latestStatus === "RED"
      ? "🧛‍♂️"
      : latestStatus === "GREEN"
      ? "🎃"
      : latestStatus === "YELLOW"
      ? "🧐"
      : "🧙‍♂️";

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-[#241042] via-[#0d0618] to-[#05020a] p-4 sm:p-6 text-amber-50">
      {/* Top Navigation Header */}
      <header className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 rounded-2xl border border-orange-500/30 bg-black/40 px-5 py-3.5 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🎃</span>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-amber-300 to-emerald-300">
              CANDY OR CURSE?
            </h1>
            <p className="text-xs text-amber-200/75">
              AI Food &amp; Halloween Candy Scanner • Gemma 4 Vision • ElevenLabs Voice • Verified DB
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {session && (
            <span className="rounded-full border border-orange-500/40 bg-orange-950/60 px-3 py-1 text-xs font-mono text-orange-300">
              Session: {session.session_id}
            </span>
          )}
          <a
            href={`/scan/${session?.session_id || "sess_demo1031"}`}
            className="rounded-xl bg-orange-500 px-3.5 py-1.5 text-xs font-black text-black hover:bg-orange-400"
          >
            📱 Open Mobile Scanner View
          </a>
        </div>
      </header>

      <main className="mx-auto mt-6 grid max-w-7xl gap-6 lg:grid-cols-12">
        {/* Left Column: The Candy Keeper Stage, Onboarding Chips & Voice/Text Chat */}
        <section className="flex flex-col rounded-3xl border border-purple-500/30 bg-purple-950/25 p-5 shadow-2xl backdrop-blur-sm lg:col-span-7">
          {/* Character Hero Stage */}
          <div className="flex items-center gap-4 rounded-2xl border border-orange-500/25 bg-gradient-to-r from-purple-950/80 via-[#1f0e38] to-orange-950/40 p-4">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl border border-orange-400/40 bg-orange-500/20 text-4xl shadow-inner">
              {keeperAvatar}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-black text-orange-300">
                  The Candy Keeper (AI Food Coach)
                </h2>
                <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                  LIVE VOICE
                </span>
              </div>
              <p className="mt-0.5 text-xs text-amber-100/80">
                Select your dietary preferences below or tell me by voice. Then scan any product front or ingredient label with your phone!
              </p>
            </div>
          </div>

          {/* Step 1: Interactive Onboarding Preference Chips */}
          <div className="mt-4">
            <p className="text-xs font-extrabold uppercase tracking-wider text-purple-300">
              1️⃣ Choose Your Preferences, Allergies, or &ldquo;Eat Everything&rdquo;:
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              {QUICK_PREFERENCES.map((pref) => {
                const isActive = session?.dietary_profile.parsed_restrictions.includes(
                  pref.id
                );
                return (
                  <button
                    key={pref.id}
                    type="button"
                    disabled={busy}
                    onClick={() => void handleSend(pref.phrase)}
                    className={`rounded-xl border px-3 py-1.5 text-xs font-bold transition ${
                      isActive
                        ? "border-orange-400 bg-orange-500 text-black shadow-[0_0_15px_rgba(249,115,22,0.5)]"
                        : "border-purple-400/35 bg-purple-900/40 text-amber-100 hover:border-orange-400/60 hover:bg-purple-800/60"
                    }`}
                  >
                    {pref.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Active Profile Summary Bar */}
          <div className="mt-3 flex flex-wrap items-center gap-1.5 rounded-xl bg-black/35 px-3 py-2">
            <span className="text-[11px] font-bold uppercase text-amber-300/80">
              Active Filter:
            </span>
            {session?.dietary_profile.parsed_restrictions.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-orange-500/25 border border-orange-400/40 px-2.5 py-0.5 text-[11px] font-extrabold uppercase text-orange-200"
              >
                {tag === "eat_everything" ? "✅ Eat Everything" : `⚠️ ${tag.replace(/_/g, " ")}`}
              </span>
            ))}
          </div>

          {/* Chat Transcript */}
          <div className="mt-4 flex-1 space-y-3 overflow-y-auto max-h-72 pr-1">
            {session?.chat_history.map((m, idx) => (
              <div
                key={idx}
                className={`rounded-2xl p-3.5 text-sm leading-relaxed ${
                  m.role === "assistant"
                    ? "bg-purple-900/50 border border-purple-400/30 text-amber-50"
                    : "ml-10 bg-orange-500/25 border border-orange-400/40 text-white"
                }`}
              >
                <span className="mb-1 block text-[10px] font-extrabold uppercase tracking-wider text-orange-300/80">
                  {m.role === "assistant" ? "🧙‍♂️ The Candy Keeper" : "🧑 You"}
                </span>
                {m.content}
              </div>
            ))}
          </div>

          {/* Voice + Text Chat Input */}
          <div className="mt-4 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void handleSend()}
              placeholder="Tell me what you don't want to eat (e.g. Halal, no gelatin, allergic to nuts)..."
              className="flex-1 rounded-2xl border border-purple-400/40 bg-black/60 px-4 py-3 text-sm text-white placeholder-amber-200/40 focus:border-orange-400 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => void toggleMicrophone()}
              className={`rounded-2xl px-4 py-3 text-sm font-extrabold transition ${
                isRecording
                  ? "animate-pulse bg-rose-600 text-white shadow-[0_0_20px_rgba(225,29,72,0.7)]"
                  : "bg-purple-700 text-white hover:bg-purple-600"
              }`}
            >
              {isRecording ? "⏹ Stop" : "🎙 Speak"}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleSend()}
              className="rounded-2xl bg-orange-500 px-5 py-3 text-sm font-black text-black hover:bg-orange-400 disabled:opacity-50"
            >
              {busy ? "..." : "Send"}
            </button>
          </div>

          {/* Instant Demo Simulator Bar on Desktop */}
          <div className="mt-4 border-t border-white/10 pt-3">
            <p className="text-[11px] font-bold uppercase tracking-wider text-amber-200/70">
              ⚡ Instant Product Test (Simulates Phone Camera Scan):
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void handleQuickDemoScan("haribo-goldbears")}
                className="rounded-xl border border-rose-500/50 bg-rose-950/60 px-3 py-1.5 text-xs font-bold text-rose-200 hover:bg-rose-900"
              >
                🔴 Haribo Goldbären (Gelatin)
              </button>
              <button
                type="button"
                onClick={() => void handleQuickDemoScan("snickers-original")}
                className="rounded-xl border border-rose-500/50 bg-rose-950/60 px-3 py-1.5 text-xs font-bold text-rose-200 hover:bg-rose-900"
              >
                🔴 Snickers (Peanuts &amp; Milk)
              </button>
              <button
                type="button"
                onClick={() => void handleQuickDemoScan("capri-sun-multivitamin")}
                className="rounded-xl border border-emerald-500/50 bg-emerald-950/60 px-3 py-1.5 text-xs font-bold text-emerald-200 hover:bg-emerald-900"
              >
                🟢 Capri-Sun (Vegan/Halal)
              </button>
              <button
                type="button"
                onClick={() => void handleQuickDemoScan("water-bottle-front")}
                className="rounded-xl border border-amber-400/50 bg-amber-950/60 px-3 py-1.5 text-xs font-bold text-amber-200 hover:bg-amber-900"
              >
                🟡 Water Bottle (&ldquo;Turn It Around!&rdquo;)
              </button>
            </div>
          </div>
        </section>

        {/* Right Column: QR Code Station & Live Mobile Result Overlay */}
        <section className="space-y-6 lg:col-span-5">
          <div className="rounded-3xl border border-orange-500/40 bg-black/50 p-5 text-center shadow-2xl">
            <h3 className="text-base font-black text-orange-300">
              2️⃣ Scan QR to Connect Your Smartphone Camera
            </h3>
            <p className="mt-1 text-xs text-amber-200/75">
              Stream or snap any food product—front or back ingredient label!
            </p>
            <div className="mx-auto mt-4 inline-block rounded-2xl border-4 border-orange-400 bg-white p-3.5 shadow-[0_0_30px_rgba(249,115,22,0.3)]">
              <QRCodeSVG value={qrUrl} size={164} />
            </div>
            <div className="mt-3 flex items-center justify-center gap-2">
              <code className="max-w-xs truncate rounded bg-white/10 px-2.5 py-1 text-[11px] text-amber-200">
                {qrUrl}
              </code>
              <button
                type="button"
                onClick={() => {
                  void navigator.clipboard?.writeText(qrUrl);
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                }}
                className="rounded-lg bg-white/15 px-2.5 py-1 text-[11px] font-bold text-white hover:bg-white/25"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
          </div>

          {session?.latest_scan && (
            <div>
              <h4 className="mb-2 text-xs font-extrabold uppercase tracking-wider text-amber-300">
                🔮 Live Scan Verdict &amp; Alternatives:
              </h4>
              <ClassificationOverlay
                result={session.latest_scan}
                onSelectAlternative={(prodId) => void handleQuickDemoScan(prodId)}
              />
            </div>
          )}
        </section>
      </main>
    </div>
  );
};
