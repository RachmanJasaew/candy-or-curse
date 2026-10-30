/**
 * Mock API Responses for Independent Team A Frontend Development.
 * Covers GREEN, RED, and YELLOW classification states + session + voice.
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
  headline: "CURSED! Contains Gelatin (Pork-derived), Beeswax",
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
  explanation:
    "CURSED! Haribo Goldbears (Goldbären) contains verified conflicting ingredients for your dietary profile: Gelatin (Pork-derived), Glazing agents (Beeswax white and yellow).",
  keeper_spoken_summary:
    "Back away from the golden pouch! Haribo Goldbears contain pork gelatin and beeswax—a dark curse for vegans!",
  uncertainty: {
    is_uncertain: false,
    confidence_score: 0.96,
    reasons: [],
  },
  safety_disclaimer:
    "Classification is based on our verified reference database. Formulations vary by region and batch—always read the physical package label before consuming.",
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
  headline: "CANDY! No Known Conflicting Ingredients",
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
  explanation:
    "No known conflicting ingredients were found in our verified database record for Capri-Sun Multivitamin against your active restrictions (vegan, no_gelatin, peanuts). Note: Always verify the physical package label, as regional recipes and factory lines vary.",
  keeper_spoken_summary:
    "A sweet potion indeed! Our verified scroll shows no known conflicting ingredients in Capri-Sun Multivitamin for your restrictions, though you should always check the pouch!",
  uncertainty: {
    is_uncertain: false,
    confidence_score: 0.95,
    reasons: [],
  },
  safety_disclaimer:
    "Classification is based on our verified reference database. Formulations vary by region and batch—always read the physical package label before consuming.",
};

export const MOCK_SCAN_YELLOW: ScanResult = {
  scan_id: "scan_yellow_mystery",
  session_id: "sess_demo1031",
  timestamp: new Date().toISOString(),
  recognized_product: {
    product_id: null,
    name: "Unverified Spooky Wrapper",
    brand: null,
    category: "unknown",
    confidence: 0.41,
    visual_evidence: "Wrapper text is blurry and not in the verified 15-product catalog.",
  },
  identification_status: "AMBIGUOUS",
  ingredient_source: "NONE",
  classification: "YELLOW",
  headline: "UNCERTAIN! Insufficient Product or Ingredient Data",
  conflicting_ingredients: [],
  verified_ingredients: [],
  allergen_warnings: [],
  explanation:
    "Caution, mortal! My crystal ball cannot verify the exact ingredients for 'Unverified Spooky Wrapper'. Visual recognition confidence (41%) is below the 60% verification threshold. Please inspect the physical wrapper carefully.",
  keeper_spoken_summary:
    "Proceed with caution! The mists obscure this treat and I cannot verify its ingredients. Check the physical wrapper yourself!",
  uncertainty: {
    is_uncertain: true,
    confidence_score: 0.41,
    reasons: [
      "Product is not in our verified 15-product ingredient database.",
      "Visual recognition confidence (41%) is below the 60% verification threshold.",
    ],
  },
  safety_disclaimer:
    "Classification is based on our verified reference database. Formulations vary by region and batch—always read the physical package label before consuming.",
};

export const MOCK_SESSION: SessionResponse = {
  session_id: "sess_demo1031",
  created_at: new Date().toISOString(),
  mobile_scan_path: "/scan/sess_demo1031",
  mobile_scan_url: `${typeof window !== "undefined" ? window.location.origin : "https://candy-or-curse.lovable.app"}/scan/sess_demo1031`,
  dietary_profile: {
    allergies: ["peanuts"],
    dietary_preferences: ["vegan", "no_gelatin"],
    raw_notes: "I am vegan, avoid gelatin, and have a peanut allergy.",
    parsed_restrictions: ["peanuts", "vegan", "no_gelatin", "dairy", "milk", "eggs"],
  },
  chat_history: [
    {
      role: "assistant",
      content:
        "Welcome to the Crypt of Candies! I am The Candy Keeper. I have recorded your restrictions: Vegan, No Gelatin, and Peanut Allergy. Scan the QR code with your phone to inspect your Halloween treats!",
      timestamp: new Date().toISOString(),
    },
  ],
  scan_history: [MOCK_SCAN_RED, MOCK_SCAN_GREEN, MOCK_SCAN_YELLOW],
  latest_scan: MOCK_SCAN_RED,
};

export const MOCK_CHAT_RESPONSE: ChatResponse = {
  session_id: "sess_demo1031",
  reply:
    "Ah, mortal! The Candy Keeper hears your decree! I have inscribed your dietary restrictions onto my glowing scroll. Hold a candy wrapper before your phone camera to see if it is Candy or Curse!",
  updated_dietary_profile: MOCK_SESSION.dietary_profile,
  extracted_new_restrictions: ["peanuts", "vegan", "no_gelatin"],
};

export const MOCK_TRANSCRIBE_RESPONSE: TranscribeResponse = {
  text: "I am vegan and allergic to peanuts and gelatin.",
  language_code: "en",
  provider: "mock_elevenlabs_scribe_v1",
};

export const MOCK_SYNTHESIZE_RESPONSE: SynthesizeResponse = {
  audio_base64:
    "//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAABIADAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA",
  mime_type: "audio/mpeg",
  provider: "mock_elevenlabs_flash_v2_5",
};
