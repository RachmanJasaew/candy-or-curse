"""Environment configuration for Candy or Curse backend."""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")

PLACEHOLDER_KEYS = {
    "",
    "your_google_ai_studio_api_key_here",
    "your_elevenlabs_api_key_here",
    "changeme",
}


def _clean_api_key(raw: str) -> str:
    val = raw.strip()
    return "" if val.lower() in PLACEHOLDER_KEYS else val


class Settings:
    """Server configuration loaded from environment variables."""

    GEMINI_API_KEY: str = _clean_api_key(os.getenv("GEMINI_API_KEY", ""))
    GEMMA_MODEL: str = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it").strip()

    ELEVENLABS_API_KEY: str = _clean_api_key(os.getenv("ELEVENLABS_API_KEY", ""))
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb").strip()
    ELEVENLABS_TTS_MODEL: str = os.getenv("ELEVENLABS_TTS_MODEL", "eleven_flash_v2_5").strip()
    ELEVENLABS_STT_MODEL: str = os.getenv("ELEVENLABS_STT_MODEL", "scribe_v1").strip()

    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    PUBLIC_FRONTEND_URL: str = os.getenv(
        "PUBLIC_FRONTEND_URL", "https://pixel-perfect-replay-80513.lovable.app"
    ).rstrip("/")
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]


settings = Settings()
