/**
 * Shared TypeScript API Contract Models (`v1.1.0`)
 * Matches `docs/API_CONTRACT.md` and `backend/app/models/schemas.py`.
 */

export type ClassificationStatus = "GREEN" | "RED" | "YELLOW";

export type IdentificationStatus =
  | "IDENTIFIED"
  | "NEEDS_INGREDIENT_LABEL"
  | "AMBIGUOUS"
  | "UNKNOWN";

export type IngredientSource =
  | "VERIFIED_DATABASE"
  | "PACKAGE_OCR"
  | "USER_TEXT_INPUT"
  | "UNVERIFIED_FALLBACK"
  | "NONE";

export interface DietaryProfile {
  allergies: string[];
  dietary_preferences: string[];
  raw_notes: string;
  parsed_restrictions: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface RecognizedProduct {
  product_id: string | null;
  name: string;
  brand: string | null;
  category: string | null;
  confidence: number;
  visual_evidence: string;
}

export interface AlternativeProduct {
  product_id: string;
  name: string;
  brand: string;
  category: string;
  reason: string;
}

export interface UncertaintyInfo {
  is_uncertain: boolean;
  confidence_score: number;
  reasons: string[];
}

export interface ScanResult {
  scan_id: string;
  session_id: string;
  timestamp: string;
  recognized_product: RecognizedProduct;
  identification_status: IdentificationStatus;
  ingredient_source: IngredientSource;
  classification: ClassificationStatus;
  headline: string;
  conflicting_ingredients: string[];
  verified_ingredients: string[];
  allergen_warnings: string[];
  recommended_alternatives: AlternativeProduct[];
  needs_ingredient_photo: boolean;
  agent_guidance_prompt: string | null;
  explanation: string;
  keeper_spoken_summary: string;
  uncertainty: UncertaintyInfo;
  safety_disclaimer: string;
}

export interface CreateSessionRequest {
  initial_message?: string;
  allergies?: string[];
  dietary_preferences?: string[];
}

export interface SessionResponse {
  session_id: string;
  created_at: string;
  mobile_scan_path: string;
  mobile_scan_url: string;
  dietary_profile: DietaryProfile;
  chat_history: ChatMessage[];
  scan_history: ScanResult[];
  latest_scan: ScanResult | null;
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  updated_dietary_profile: DietaryProfile;
  extracted_new_restrictions: string[];
}

export interface ScanBase64Request {
  image_base64?: string;
  mime_type?: string;
  ingredient_text_override?: string;
  scan_mode?: "auto" | "front" | "ingredients" | "live_stream";
  demo_product_hint?: string;
}

export interface TranscribeResponse {
  text: string;
  language_code: string;
  provider: string;
}

export interface SynthesizeRequest {
  text: string;
  voice_id?: string;
}

export interface SynthesizeResponse {
  audio_base64: string;
  mime_type: string;
  provider: string;
}
