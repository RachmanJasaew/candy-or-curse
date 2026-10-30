/**
 * Frontend API Client & Mock Switcher (Developer A2)
 */
import {
  ChatRequest,
  ChatResponse,
  CreateSessionRequest,
  ScanResult,
  SessionResponse,
  SynthesizeRequest,
  SynthesizeResponse,
  TranscribeResponse,
} from "../types/api";
import {
  MOCK_CHAT_RESPONSE,
  MOCK_SCAN_GREEN,
  MOCK_SCAN_RED,
  MOCK_SCAN_YELLOW,
  MOCK_SESSION,
  MOCK_SYNTHESIZE_RESPONSE,
  MOCK_TRANSCRIBE_RESPONSE,
} from "../mocks/mockData";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const DEFAULT_USE_MOCK =
  String(import.meta.env.VITE_USE_MOCK_API ?? "false").toLowerCase() === "true";

let mockSessionState: SessionResponse = structuredClone(MOCK_SESSION);

export async function createSession(
  payload: CreateSessionRequest = {},
  useMock = DEFAULT_USE_MOCK
): Promise<SessionResponse> {
  if (useMock) {
    mockSessionState = {
      ...structuredClone(MOCK_SESSION),
      session_id: `sess_${Math.random().toString(36).slice(2, 10)}`,
      created_at: new Date().toISOString(),
    };
    mockSessionState.mobile_scan_path = `/scan/${mockSessionState.session_id}`;
    mockSessionState.mobile_scan_url = `${window.location.origin}${mockSessionState.mobile_scan_path}`;
    return mockSessionState;
  }

  const res = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to create session (${res.status})`);
  }
  return res.json();
}

export async function getSession(
  sessionId: string,
  useMock = DEFAULT_USE_MOCK
): Promise<SessionResponse> {
  if (useMock) {
    return { ...mockSessionState, session_id: sessionId };
  }

  const res = await fetch(`${API_BASE_URL}/api/sessions/${encodeURIComponent(sessionId)}`);
  if (!res.ok) {
    throw new Error(`Session '${sessionId}' not found (${res.status})`);
  }
  return res.json();
}

export async function sendChatMessage(
  sessionId: string,
  payload: ChatRequest,
  useMock = DEFAULT_USE_MOCK
): Promise<ChatResponse> {
  if (useMock) {
    const lower = payload.message.toLowerCase();
    if (lower.includes("eat everything") || lower.includes("eat_everything")) {
      mockSessionState.dietary_profile.parsed_restrictions = ["eat_everything"];
      mockSessionState.dietary_profile.raw_notes = payload.message;
      const reply =
        "Awesome—you eat everything with no restrictions! Point your phone at any snack or drink.";
      mockSessionState.chat_history.push(
        { role: "user", content: payload.message, timestamp: new Date().toISOString() },
        { role: "assistant", content: reply, timestamp: new Date().toISOString() }
      );
      return {
        session_id: sessionId,
        reply,
        updated_dietary_profile: mockSessionState.dietary_profile,
        extracted_new_restrictions: ["eat_everything"],
      };
    }

    const added: string[] = [];
    if (lower.includes("halal")) added.push("halal", "pork", "no_gelatin");
    if (lower.includes("peanut")) added.push("peanuts");
    if (lower.includes("vegan")) added.push("vegan", "no_gelatin");
    if (lower.includes("vegetarian")) added.push("vegetarian", "no_gelatin");
    if (lower.includes("gelatin")) added.push("no_gelatin");
    if (lower.includes("gluten") || lower.includes("wheat")) added.push("gluten");
    if (lower.includes("milk") || lower.includes("dairy") || lower.includes("lactose")) {
      added.push("dairy");
    }

    const merged = Array.from(
      new Set(
        [...mockSessionState.dietary_profile.parsed_restrictions, ...added].filter(
          (r) => r !== "eat_everything"
        )
      )
    );
    mockSessionState.dietary_profile.parsed_restrictions = merged;
    mockSessionState.dietary_profile.raw_notes = payload.message;

    const reply =
      added.length > 0
        ? `Got it! I updated your profile with [${added.join(", ")}]. Film any product or show me its ingredient list!`
        : MOCK_CHAT_RESPONSE.reply;

    mockSessionState.chat_history.push(
      { role: "user", content: payload.message, timestamp: new Date().toISOString() },
      { role: "assistant", content: reply, timestamp: new Date().toISOString() }
    );

    return {
      session_id: sessionId,
      reply,
      updated_dietary_profile: mockSessionState.dietary_profile,
      extracted_new_restrictions: added,
    };
  }

  const res = await fetch(
    `${API_BASE_URL}/api/sessions/${encodeURIComponent(sessionId)}/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
  if (!res.ok) {
    throw new Error(`Chat request failed (${res.status})`);
  }
  return res.json();
}

export async function scanCandyImage(
  sessionId: string,
  fileOrBase64?: File | string,
  demoProductHint?: string,
  ingredientTextOverride?: string,
  useMock = DEFAULT_USE_MOCK
): Promise<ScanResult> {
  if (useMock) {
    if (ingredientTextOverride && ingredientTextOverride.trim()) {
      const lowerIng = ingredientTextOverride.toLowerCase();
      const hasConflict =
        lowerIng.includes("gelatin") ||
        lowerIng.includes("pork") ||
        lowerIng.includes("peanut");
      const base = hasConflict
        ? structuredClone(MOCK_SCAN_RED)
        : structuredClone(MOCK_SCAN_GREEN);
      base.ingredient_source = "USER_TEXT_INPUT";
      base.recognized_product.name = "Custom Ingredient List Scan";
      base.verified_ingredients = ingredientTextOverride
        .split(/[,;\n]+/)
        .map((s) => s.trim())
        .filter(Boolean);
      mockSessionState.latest_scan = base;
      mockSessionState.scan_history.unshift(base);
      return base;
    }

    const hint = (demoProductHint || "").toLowerCase();
    let result: ScanResult = MOCK_SCAN_RED;
    if (hint.includes("capri") || hint.includes("skittles") || hint.includes("green")) {
      result = structuredClone(MOCK_SCAN_GREEN);
    } else if (
      hint.includes("unknown") ||
      hint.includes("yellow") ||
      hint.includes("water") ||
      hint.includes("turn")
    ) {
      result = structuredClone(MOCK_SCAN_YELLOW);
    } else {
      result = structuredClone(MOCK_SCAN_RED);
    }
    result.session_id = sessionId;
    result.timestamp = new Date().toISOString();
    mockSessionState.latest_scan = result;
    mockSessionState.scan_history.unshift(result);
    return result;
  }

  const query = demoProductHint
    ? `?demo_product_hint=${encodeURIComponent(demoProductHint)}`
    : "";
  const url = `${API_BASE_URL}/api/sessions/${encodeURIComponent(sessionId)}/scan${query}`;

  if (!fileOrBase64 || typeof fileOrBase64 === "string") {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image_base64: fileOrBase64 || "",
        mime_type: "image/jpeg",
        demo_product_hint: demoProductHint,
        ingredient_text_override: ingredientTextOverride,
      }),
    });
    if (!res.ok) {
      throw new Error(`Scan request failed (${res.status})`);
    }
    return res.json();
  }

  const formData = new FormData();
  formData.append("image", fileOrBase64);
  if (demoProductHint) {
    formData.append("demo_product_hint", demoProductHint);
  }
  if (ingredientTextOverride) {
    formData.append("ingredient_text_override", ingredientTextOverride);
  }
  const res = await fetch(url, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new Error(`Scan upload failed (${res.status})`);
  }
  return res.json();
}

export async function transcribeVoice(
  audioBlob: Blob,
  languageCode = "en",
  useMock = DEFAULT_USE_MOCK
): Promise<TranscribeResponse> {
  if (useMock) {
    return MOCK_TRANSCRIBE_RESPONSE;
  }

  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");
  formData.append("language_code", languageCode);

  const res = await fetch(`${API_BASE_URL}/api/voice/transcribe`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    throw new Error(`Voice transcription failed (${res.status})`);
  }
  return res.json();
}

export async function synthesizeSpeech(
  payload: SynthesizeRequest,
  useMock = DEFAULT_USE_MOCK
): Promise<SynthesizeResponse> {
  if (useMock) {
    return MOCK_SYNTHESIZE_RESPONSE;
  }

  const res = await fetch(`${API_BASE_URL}/api/voice/synthesize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Speech synthesis failed (${res.status})`);
  }
  return res.json();
}
