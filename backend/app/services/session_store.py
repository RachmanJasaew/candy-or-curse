"""Session management and QR synchronization store with automatic disk persistence (Developer B2)."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Optional
import uuid

from app.config import settings
from app.models.schemas import (
    ChatMessage,
    CreateSessionRequest,
    ScanResult,
    SessionResponse,
)
from app.services.classifier import build_dietary_profile

PERSIST_PATH = Path(__file__).resolve().parent.parent.parent / "tmp" / "sessions.json"
TUNNEL_LOG_PATH = Path(
    "/Users/rachmanjasaew/.gemini/antigravity/brain/b0de59da-2240-4856-a40d-07869c96a65e/.system_generated/tasks/task-238.log"
)


def get_live_public_url() -> str:
    """Return the latest active HTTPS tunnel URL (auto-detecting localhost.run rotations)."""
    try:
        if TUNNEL_LOG_PATH.exists():
            text = TUNNEL_LOG_PATH.read_text(encoding="utf-8", errors="ignore")
            matches = re.findall(r"https://[a-z0-9]+\.lhr\.life", text)
            if matches:
                return matches[-1]
    except Exception:
        pass
    return settings.PUBLIC_FRONTEND_URL


class SessionStore:
    """Session store with automatic JSON persistence so QR sessions survive `uvicorn --reload`."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionResponse] = {}
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        try:
            if PERSIST_PATH.exists():
                raw = json.loads(PERSIST_PATH.read_text(encoding="utf-8"))
                for sid, data in raw.items():
                    self._sessions[sid] = SessionResponse.model_validate(data)
        except Exception:
            # Start clean if disk cache is corrupted
            self._sessions = {}

    def _save_to_disk(self) -> None:
        try:
            PERSIST_PATH.parent.mkdir(parents=True, exist_ok=True)
            serialized = {
                sid: sess.model_dump(mode="json")
                for sid, sess in self._sessions.items()
            }
            PERSIST_PATH.write_text(json.dumps(serialized, indent=2), encoding="utf-8")
        except Exception:
            pass

    def create_session(self, req: CreateSessionRequest) -> SessionResponse:
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        profile = build_dietary_profile(
            allergies=req.allergies,
            dietary_preferences=req.dietary_preferences,
            raw_notes=req.initial_message or "",
        )

        mobile_scan_path = f"/scan/{session_id}"
        mobile_scan_url = f"{get_live_public_url()}{mobile_scan_path}"

        restrictions_summary = (
            ", ".join(profile.parsed_restrictions)
            if profile.parsed_restrictions
            else "none recorded yet"
        )
        welcome_msg = (
            f"Welcome! I am The Candy Keeper. "
            f"Active dietary preferences: {restrictions_summary}. "
            f"Scan the QR code with your phone to live-stream or photograph any food product—front or ingredient label!"
        )

        session = SessionResponse(
            session_id=session_id,
            created_at=now_iso,
            mobile_scan_path=mobile_scan_path,
            mobile_scan_url=mobile_scan_url,
            dietary_profile=profile,
            chat_history=[
                ChatMessage(
                    role="assistant",
                    content=welcome_msg,
                    timestamp=now_iso,
                )
            ],
            scan_history=[],
            latest_scan=None,
        )
        self._sessions[session_id] = session
        self._save_to_disk()
        return session

    def get_session(self, session_id: str) -> Optional[SessionResponse]:
        sess = self._sessions.get(session_id)
        if sess:
            sess.mobile_scan_url = f"{get_live_public_url()}{sess.mobile_scan_path}"
        return sess

    def replace_preferences(
        self,
        session_id: str,
        req: CreateSessionRequest,
    ) -> Optional[SessionResponse]:
        """Directly overwrite a session's dietary preferences (e.g. from onboarding toggles)."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        session.dietary_profile = build_dietary_profile(
            allergies=req.allergies,
            dietary_preferences=req.dietary_preferences,
            raw_notes=req.initial_message or "",
        )
        self._save_to_disk()
        return session

    def update_dietary_profile(
        self,
        session_id: str,
        user_message: str,
        assistant_reply: str,
        new_restrictions: list[str],
    ) -> Optional[SessionResponse]:
        session = self._sessions.get(session_id)
        if not session:
            return None

        now_iso = datetime.now(timezone.utc).isoformat()
        if "eat_everything" in new_restrictions and len(new_restrictions) == 1:
            session.dietary_profile = build_dietary_profile(
                allergies=[],
                dietary_preferences=["eat_everything"],
                raw_notes=user_message,
            )
        else:
            combined_notes = (
                f"{session.dietary_profile.raw_notes} | {user_message}".strip(" |")
                if session.dietary_profile.raw_notes
                else user_message
            )
            merged_allergies = [
                r
                for r in dict.fromkeys(session.dietary_profile.allergies + new_restrictions)
                if r != "eat_everything"
            ]
            merged_prefs = [
                p
                for p in session.dietary_profile.dietary_preferences
                if p != "eat_everything"
            ]
            session.dietary_profile = build_dietary_profile(
                allergies=merged_allergies,
                dietary_preferences=merged_prefs,
                raw_notes="",
            )
            session.dietary_profile.raw_notes = combined_notes

        session.chat_history.append(
            ChatMessage(role="user", content=user_message, timestamp=now_iso)
        )
        session.chat_history.append(
            ChatMessage(role="assistant", content=assistant_reply, timestamp=now_iso)
        )
        self._save_to_disk()
        return session

    def record_scan(self, session_id: str, scan_result: ScanResult) -> Optional[SessionResponse]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        session.scan_history.insert(0, scan_result)
        session.latest_scan = scan_result
        self._save_to_disk()
        return session


session_store = SessionStore()
