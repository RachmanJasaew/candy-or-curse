/**
 * Shared TypeScript API Contract Models (`v1.0.0`)
 * Matches `docs/API_CONTRACT.md` and `backend/app/models/schemas.py`.
 * DO NOT modify field names without coordinating across Team A & Team B.
 */

export type ClassificationStatus = "GREEN" | "RED" | "YELLOW";

export type IdentificationStatus = "IDENTIFIED" | "AMBIGUOUS" | "UNKNOWN";

export type IngredientSource =
  | "VERIFIED_DATABASE"
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
  image_base64: string;
  mime_type?: string;
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
