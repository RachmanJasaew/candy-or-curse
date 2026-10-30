/**
 * Mock API Responses for Independent Team A Frontend Development.
 * Covers GREEN, RED (with Recommended Alternatives), and YELLOW ("Turn it around, let me see the ingredients!").
 */
import {
  ChatResponse,
  ScanResult,
  SessionResponse,
  SynthesizeResponse,
  TranscribeResponse,
} from "../types/api";

export const MOCK_SCAN_RED: ScanResult = {
  scan_id: "scan_red_haribo",
  session_id: "sess_demo1031",
  timestamp: new Date().toISOString(),
  recognized_product: {
    product_id: "haribo-goldbears",
    name: "Haribo Goldbears (Goldbären)",
    brand: "Haribo",
    category: "gummy_candy",
    confidence: 0.96,
    visual_evidence:
      "Gold plastic bag with red HARIBO banner, cartoon bear mascot, and colorful gummy bears.",
  },
  identification_status: "IDENTIFIED",
  ingredient_source: "VERIFIED_DATABASE",
  classification: "RED",
  headline: "CURSED / NOT RECOMMENDED! Contains Pork Gelatin",
  conflicting_ingredients: [
    "Gelatin (Pork-derived)",
    "Glazing agents (Beeswax white and yellow)",
  ],
  verified_ingredients: [
    "Glucose syrup",
    "Sugar",
    "Gelatin (Pork-derived)",
    "Dextrose",
    "Fruit juice from concentrate",
    "Citric acid",
    "Glazing agents (Beeswax white and yellow, Carnauba wax)",
  ],
  allergen_warnings: ["May contain traces of milk and wheat"],
  recommended_alternatives: [
    {
      product_id: "sour-patch-kids",
      name: "Sour Patch Kids Original",
      brand: "Mondelez",
      category: "gummy_candy",
      reason: "Compatible with your preferences (Halal, Vegan, No Gelatin, Peanut-Free)",
    },
    {
      product_id: "skittles-original",
      name: "Skittles Original Fruit Candies",
      brand: "Mars Wrigley",
      category: "chewy_candy",
      reason: "Compatible with your preferences (Halal, Vegan, No Gelatin, Peanut-Free)",
    },
    {
      product_id: "katjes-yoghurt-gums",
      name: "Katjes Yoghurt-Gums (Veggie)",
      brand: "Katjes",
      category: "gummy_candy",
      reason: "Gelatin-free & Halal-friendly gummy alternative (contains dairy)",
    },
  ],
  needs_ingredient_photo: false,
  agent_guidance_prompt: null,
  explanation:
    "NOT RECOMMENDED! Haribo Goldbears contains pork-derived gelatin, which conflicts with Halal, Vegan, and Gelatin-Free preferences. Recommended alternatives: Sour Patch Kids Original, Skittles Original.",
  keeper_spoken_summary:
    "Hold on! Haribo Goldbears is not recommended for you because it contains pork gelatin. Instead, try Sour Patch Kids or Skittles—they match your preferences!",
  uncertainty: {
    is_uncertain: false,
    confidence_score: 0.96,
    reasons: [],
  },
  safety_disclaimer:
    "Classification is based on our verified reference database or package OCR. Formulations vary by region and batch—always read the physical package label before consuming.",
};

export const MOCK_SCAN_GREEN: ScanResult = {
  scan_id: "scan_green_caprisun",
  session_id: "sess_demo1031",
  timestamp: new Date().toISOString(),
  recognized_product: {
    product_id: "capri-sun-multivitamin",
    name: "Capri-Sun Multivitamin",
    brand: "Capri-Sun",
    category: "beverage_pouch",
    confidence: 0.95,
    visual_evidence:
      "Silver foil stand-up drink pouch with blue/orange Capri-Sun logo and tropical fruit splash.",
  },
  identification_status: "IDENTIFIED",
  ingredient_source: "VERIFIED_DATABASE",
  classification: "GREEN",
  headline: "RECOMMENDED! No Known Conflicting Ingredients",
  conflicting_ingredients: [],
  verified_ingredients: [
    "Spring water",
    "Fruit juice from concentrate 12% (lemon, orange, apple, grapefruit, pineapple, banana, kiwi, passion fruit, lime)",
    "Sugar",
    "Citric acid",
    "Natural flavoring",
    "Antioxidant (Ascorbic acid)",
    "Vitamins (C, Niacin, E, B6, Thiamin, Biotin, B12)",
  ],
  allergen_warnings: [],
  recommended_alternatives: [],
  needs_ingredient_photo: false,
  agent_guidance_prompt: null,
  explanation:
    "No known conflicting ingredients were found in our verified database record for Capri-Sun Multivitamin against your active preferences. Always verify the physical package label.",
  keeper_spoken_summary:
    "Good news! Capri-Sun Multivitamin has no known conflicting ingredients for your preferences!",
  uncertainty: {
    is_uncertain: false,
    confidence_score: 0.95,
    reasons: [],
  },
  safety_disclaimer:
    "Classification is based on our verified reference database or package OCR. Formulations vary by region and batch—always read the physical package label before consuming.",
};

export const MOCK_SCAN_YELLOW: ScanResult = {
  scan_id: "scan_yellow_turn_around",
  session_id: "sess_demo1031",
  timestamp: new Date().toISOString(),
  recognized_product: {
    product_id: null,
    name: "Flavored Water Bottle",
    brand: "Local Brand",
    category: "beverage",
    confidence: 0.88,
    visual_evidence: "Front of a plastic water bottle; ingredient list is on the back.",
  },
  identification_status: "NEEDS_INGREDIENT_LABEL",
  ingredient_source: "NONE",
  classification: "YELLOW",
  headline: "TURN IT AROUND! Show Me the Ingredient List",
  conflicting_ingredients: [],
  verified_ingredients: [],
  allergen_warnings: [],
  recommended_alternatives: [],
  needs_ingredient_photo: true,
  agent_guidance_prompt:
    "Okay, I see the front of your bottle. Turn it around—let me see the ingredients on the back!",
  explanation:
    "I see the front of the Flavored Water Bottle, but to check your preferences accurately, turn it around so I can read the ingredient list on the back (or paste the ingredients below).",
  keeper_spoken_summary:
    "Okay, turn it around. Let me see the ingredients!",
  uncertainty: {
    is_uncertain: true,
    confidence_score: 0.88,
    reasons: [
      "Front of product detected, but exact ingredients are not in the pre-verified database.",
      "Turn the product around to show the ingredient label, or type the ingredients below.",
    ],
  },
  safety_disclaimer:
    "Classification is based on our verified reference database or package OCR. Formulations vary by region and batch—always read the physical package label before consuming.",
};

export const MOCK_SESSION: SessionResponse = {
  session_id: "sess_demo1031",
  created_at: new Date().toISOString(),
  mobile_scan_path: "/scan/sess_demo1031",
  mobile_scan_url: `${typeof window !== "undefined" ? window.location.origin : "https://candy-or-curse.lovable.app"}/scan/sess_demo1031`,
  dietary_profile: {
    allergies: ["peanuts"],
    dietary_preferences: ["halal", "no_gelatin"],
    raw_notes: "I want Halal food, avoid gelatin, and have a peanut allergy.",
    parsed_restrictions: ["halal", "pork", "no_gelatin", "peanuts"],
  },
  chat_history: [
    {
      role: "assistant",
      content:
        "Welcome! Tell me your preferences (Halal, Vegan, Eat Everything, or any allergies). Then scan the QR code with your phone to live-stream or snap any food product—front or ingredient label!",
      timestamp: new Date().toISOString(),
    },
  ],
  scan_history: [MOCK_SCAN_RED, MOCK_SCAN_GREEN, MOCK_SCAN_YELLOW],
  latest_scan: MOCK_SCAN_RED,
};

export const MOCK_CHAT_RESPONSE: ChatResponse = {
  session_id: "sess_demo1031",
  reply:
    "Got it! I've updated your preferences. Point your phone camera at any food product—if I don't recognize the front, I'll ask you to turn it around so I can read the ingredients!",
  updated_dietary_profile: MOCK_SESSION.dietary_profile,
  extracted_new_restrictions: ["halal", "peanuts", "no_gelatin"],
};

export const MOCK_TRANSCRIBE_RESPONSE: TranscribeResponse = {
  text: "I eat halal and I am allergic to peanuts.",
  language_code: "en",
  provider: "mock_elevenlabs_scribe_v1",
};

export const MOCK_SYNTHESIZE_RESPONSE: SynthesizeResponse = {
  audio_base64:
    "//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABIADAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA",
  mime_type: "audio/mpeg",
  provider: "mock_elevenlabs_flash_v2_5",
};
