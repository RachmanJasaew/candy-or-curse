/**
 * ElevenLabs Audio Recording & Playback Helper with Web Speech API Fallback (Developer A2)
 */
import { synthesizeSpeech, transcribeVoice } from "../api/client";

export class VoiceInteractionController {
  private mediaRecorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];

  async startRecording(): Promise<void> {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.chunks = [];
    this.mediaRecorder = new MediaRecorder(stream);
    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        this.chunks.push(e.data);
      }
    };
    this.mediaRecorder.start();
  }

  async stopAndTranscribe(): Promise<string> {
    if (!this.mediaRecorder) {
      throw new Error("Microphone recording was not started.");
    }

    const audioBlob = await new Promise<Blob>((resolve) => {
      if (!this.mediaRecorder) return resolve(new Blob());
      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: "audio/webm" });
        this.mediaRecorder?.stream.getTracks().forEach((t) => t.stop());
        resolve(blob);
      };
      this.mediaRecorder.stop();
    });

    const result = await transcribeVoice(audioBlob);
    return result.text;
  }
}

export async function speakCandyKeeperText(text: string): Promise<void> {
  try {
    const res = await synthesizeSpeech({ text });
    if (res.audio_base64 && res.provider !== "mock_elevenlabs_flash_v2_5") {
      const audio = new Audio(`data:${res.mime_type};base64,${res.audio_base64}`);
      await audio.play();
      return;
    }
  } catch {
    // Fallback to browser SpeechSynthesis below if ElevenLabs is offline or rate-limited
  }

  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.pitch = 0.75;
    utterance.rate = 0.95;
    window.speechSynthesis.speak(utterance);
  }
}
