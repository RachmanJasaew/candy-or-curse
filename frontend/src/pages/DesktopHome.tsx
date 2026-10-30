/**
 * Desktop Experience — "The Candy Keeper" Chat & QR Code Station (Developer A1 + A2)
 */
import React, { useRef, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { sendChatMessage } from "../api/client";
import { ClassificationOverlay } from "../components/ClassificationOverlay";
import { useSessionSync } from "../hooks/useSessionSync";
import {
  speakCandyKeeperText,
  VoiceInteractionController,
} from "../services/voiceRecorder";

export const DesktopHome: React.FC = () => {
  const { session, setSession } = useSessionSync(undefined, 2500);
  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [busy, setBusy] = useState(false);
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
    (typeof window !== "undefined" ? window.location.origin : "https://candy-or-curse.lovable.app");

  const qrUrl = session
    ? `${publicOrigin.replace(/\/$/, "")}/scan/${session.session_id}`
    : `${publicOrigin}/scan/sess_demo1031`;

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#0c0714] via-[#190c2c] to-[#09040e] p-6 text-amber-50">
      <header className="mx-auto flex max-w-6xl items-center justify-between border-b border-orange-500/30 pb-4">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-orange-400">
            🎃 CANDY OR CURSE?
          </h1>
          <p className="text-sm text-amber-200/80">
            Spooky AI Candy Scanner • Powered by Gemma 4 &amp; ElevenLabs
          </p>
        </div>
        {session && (
          <span className="rounded-full border border-orange-500/40 bg-orange-950/60 px-3 py-1 text-xs font-mono text-orange-300">
            Session: {session.session_id}
          </span>
        )}
      </header>

      <main className="mx-auto mt-6 grid max-w-6xl gap-6 lg:grid-cols-12">
        {/* Left Column: The Candy Keeper & Chat */}
        <section className="flex flex-col rounded-2xl border border-purple-500/30 bg-purple-950/30 p-5 lg:col-span-7">
          <div className="flex items-center gap-4 border-b border-white/10 pb-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-500/20 text-3xl">
              🧙‍♂️
            </div>
            <div>
              <h2 className="text-lg font-extrabold text-orange-300">The Candy Keeper</h2>
              <p className="text-xs text-amber-200/70">
                Tell me your allergies, vegan rules, or forbidden ingredients by voice or text.
              </p>
            </div>
          </div>

          {/* Active Restrictions Badges */}
          <div className="mt-3 flex flex-wrap gap-2">
            {session?.dietary_profile.parsed_restrictions.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-orange-500/20 px-3 py-1 text-xs font-bold uppercase text-orange-300 border border-orange-400/40"
              >
                ⚠️ {tag.replace("_", " ")}
              </span>
            ))}
          </div>

          {/* Chat Messages */}
          <div className="mt-4 flex-1 space-y-3 overflow-y-auto max-h-80 pr-2">
            {session?.chat_history.map((m, idx) => (
              <div
                key={idx}
                className={`rounded-xl p-3 text-sm ${
                  m.role === "assistant"
                    ? "bg-purple-900/50 border border-purple-400/30 text-amber-50"
                    : "ml-8 bg-orange-600/30 border border-orange-400/40 text-white"
                }`}
              >
                <span className="block text-[10px] font-bold uppercase opacity-60">
                  {m.role === "assistant" ? "The Candy Keeper" : "You"}
                </span>
                {m.content}
              </div>
            ))}
          </div>

          {/* Input & Microphone Controls */}
          <div className="mt-4 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && void handleSend()}
              placeholder="e.g. I am vegan and allergic to peanuts and gluten..."
              className="flex-1 rounded-xl border border-purple-400/40 bg-black/50 px-4 py-2.5 text-sm text-white placeholder-amber-200/40"
            />
            <button
              type="button"
              onClick={() => void toggleMicrophone()}
              className={`rounded-xl px-4 py-2.5 text-sm font-bold ${
                isRecording
                  ? "animate-pulse bg-rose-600 text-white"
                  : "bg-purple-700 text-white hover:bg-purple-600"
              }`}
            >
              {isRecording ? "⏹ Stop" : "🎙 Speak"}
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleSend()}
              className="rounded-xl bg-orange-500 px-5 py-2.5 text-sm font-black text-black hover:bg-orange-400 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </section>

        {/* Right Column: QR Code & Live Mobile Scan Feed */}
        <section className="space-y-6 lg:col-span-5">
          <div className="rounded-2xl border border-orange-500/40 bg-black/40 p-5 text-center">
            <h3 className="text-base font-extrabold text-orange-300">
              📱 Scan With Your Smartphone Camera
            </h3>
            <p className="mt-1 text-xs text-amber-200/70">
              Opens the mobile candy scanner synced to this session
            </p>
            <div className="mx-auto mt-4 inline-block rounded-2xl bg-white p-4">
              <QRCodeSVG value={qrUrl} size={168} />
            </div>
            <p className="mt-3 break-all font-mono text-[11px] text-amber-200/70">{qrUrl}</p>
            <a
              href={`/scan/${session?.session_id || "sess_demo1031"}`}
              className="mt-3 inline-block rounded-lg bg-orange-500/20 px-3 py-1.5 text-xs font-bold text-orange-300 hover:bg-orange-500/30"
            >
              Open Mobile Scanner in This Tab →
            </a>
          </div>

          {session?.latest_scan && (
            <div>
              <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-amber-300">
                Latest Scan Result:
              </h4>
              <ClassificationOverlay result={session.latest_scan} />
            </div>
          )}
        </section>
      </main>
    </div>
  );
};
