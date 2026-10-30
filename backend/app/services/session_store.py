"""Session management and QR synchronization store."""
from datetime import datetime, timezone
import uuid
from typing import Optional
from app.config import settings
from app.models.schemas import (
    ChatMessage,
    CreateSessionRequest,
    DietaryProfile,
    ScanResult,
    SessionResponse,
)
from app.services.classifier import build_dietary_profile


class SessionStore:
    """Thread-safe in-memory session store for desktop/mobile QR synchronization."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionResponse] = {}

    def create_session(self, req: CreateSessionRequest) -> SessionResponse:
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        profile = build_dietary_profile(
            allergies=req.allergies,
            dietary_preferences=req.dietary_preferences,
            raw_notes=req.initial_message or "",
        )

        mobile_scan_path = f"/scan/{session_id}"
        mobile_scan_url = f"{settings.PUBLIC_FRONTEND_URL}{mobile_scan_path}"

        restrictions_summary = (
            ", ".join(profile.parsed_restrictions)
            if profile.parsed_restrictions
            else "none recorded yet"
        )
        welcome_msg = (
            f"Welcome to the Crypt of Candies! I am The Candy Keeper. "
            f"Active dietary restrictions: {restrictions_summary}. "
            f"Scan the QR code with your phone to inspect your Halloween treats!"
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
        return session

    def get_session(self, session_id: str) -> Optional[SessionResponse]:
        return self._sessions.get(session_id)

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
        combined_notes = (
            f"{session.dietary_profile.raw_notes} | {user_message}".strip(" |")
            if session.dietary_profile.raw_notes
            else user_message
        )
        merged_allergies = list(
            dict.fromkeys(session.dietary_profile.allergies + new_restrictions)
        )
        session.dietary_profile = build_dietary_profile(
            allergies=merged_allergies,
            dietary_preferences=session.dietary_profile.dietary_preferences,
            raw_notes=combined_notes,
        )
        session.chat_history.append(
            ChatMessage(role="user", content=user_message, timestamp=now_iso)
        )
        session.chat_history.append(
            ChatMessage(role="assistant", content=assistant_reply, timestamp=now_iso)
        )
        return session

    def record_scan(self, session_id: str, scan_result: ScanResult) -> Optional[SessionResponse]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        session.scan_history.insert(0, scan_result)
        session.latest_scan = scan_result
        return session


session_store = SessionStore()
