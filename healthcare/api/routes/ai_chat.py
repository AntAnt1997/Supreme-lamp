"""AI Chat API – 24/7 medical assistant, triage, and appointment recommendations."""

import logging
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from healthcare.api.auth_utils import get_current_user
from healthcare.database.db import get_db
from healthcare.models.ai_conversation import AIConversation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai_chat"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    session_token: Optional[str] = None   # Omit to start a new session
    message: str


class ChatResponse(BaseModel):
    session_token: str
    reply: str
    triage_completed: bool
    urgency_level: Optional[str] = None
    suggested_department: Optional[str] = None
    triage_summary: Optional[str] = None
    recommended_provider_id: Optional[int] = None


class TriageRequest(BaseModel):
    session_token: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatMessage,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a message to the 24/7 AI medical assistant."""
    from healthcare.ai.assistant import get_ai_reply
    from healthcare.ai.triage import run_triage_if_needed

    from healthcare.models.patient import Patient
    patient_id = current_user.id if isinstance(current_user, Patient) else None

    # Get or create conversation
    if body.session_token:
        conv = db.query(AIConversation).filter(
            AIConversation.session_token == body.session_token
        ).first()
        if not conv:
            raise HTTPException(404, "Session not found")
    else:
        conv = AIConversation(
            patient_id=patient_id,
            session_token=secrets.token_urlsafe(32),
            messages=[],
        )
        db.add(conv)
        db.flush()

    # Append patient message
    messages = conv.messages or []
    messages.append({"role": "user", "content": body.message})

    # Get AI reply
    reply = await get_ai_reply(messages, patient_id=patient_id, db=db)
    messages.append({"role": "assistant", "content": reply})
    conv.messages = messages

    # Run triage analysis
    triage_result = await run_triage_if_needed(conv, messages, db)

    db.add(conv)

    return ChatResponse(
        session_token=conv.session_token,
        reply=reply,
        triage_completed=conv.triage_completed,
        urgency_level=conv.urgency_level,
        suggested_department=conv.suggested_department,
        triage_summary=conv.triage_summary,
        recommended_provider_id=conv.recommended_provider_id,
    )


@router.post("/chat/anonymous", response_model=ChatResponse)
async def chat_anonymous(body: ChatMessage, db: Session = Depends(get_db)):
    """Anonymous chat (no auth required – useful for pre-login triage)."""
    from healthcare.ai.assistant import get_ai_reply
    from healthcare.ai.triage import run_triage_if_needed

    if body.session_token:
        conv = db.query(AIConversation).filter(
            AIConversation.session_token == body.session_token,
            AIConversation.is_anonymous == True,
        ).first()
        if not conv:
            raise HTTPException(404, "Session not found")
    else:
        conv = AIConversation(
            patient_id=None,
            session_token=secrets.token_urlsafe(32),
            messages=[],
            is_anonymous=True,
        )
        db.add(conv)
        db.flush()

    messages = conv.messages or []
    messages.append({"role": "user", "content": body.message})

    reply = await get_ai_reply(messages, patient_id=None, db=db)
    messages.append({"role": "assistant", "content": reply})
    conv.messages = messages

    triage_result = await run_triage_if_needed(conv, messages, db)
    db.add(conv)

    return ChatResponse(
        session_token=conv.session_token,
        reply=reply,
        triage_completed=conv.triage_completed,
        urgency_level=conv.urgency_level,
        suggested_department=conv.suggested_department,
        triage_summary=conv.triage_summary,
        recommended_provider_id=conv.recommended_provider_id,
    )


@router.get("/chat/{session_token}/history")
def get_chat_history(
    session_token: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(AIConversation).filter(
        AIConversation.session_token == session_token
    ).first()
    if not conv:
        raise HTTPException(404, "Session not found")

    from healthcare.models.patient import Patient
    if isinstance(current_user, Patient) and conv.patient_id != current_user.id:
        raise HTTPException(403, "Access denied")

    return {
        "session_token": session_token,
        "messages": conv.messages,
        "triage_completed": conv.triage_completed,
        "urgency_level": conv.urgency_level,
        "suggested_department": conv.suggested_department,
        "triage_summary": conv.triage_summary,
    }


@router.post("/triage")
async def force_triage(body: TriageRequest, db: Session = Depends(get_db)):
    """Force a triage evaluation on a conversation."""
    from healthcare.ai.triage import force_run_triage

    conv = db.query(AIConversation).filter(
        AIConversation.session_token == body.session_token
    ).first()
    if not conv:
        raise HTTPException(404, "Session not found")

    result = await force_run_triage(conv, db)
    db.add(conv)
    return result
