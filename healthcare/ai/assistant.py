"""24/7 AI medical assistant – conversational interface backed by OpenAI."""

import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

# System prompt that defines the assistant's behaviour
_SYSTEM_PROMPT = """You are a compassionate, knowledgeable 24/7 AI medical assistant for a healthcare platform.
Your role is to:
1. Help patients understand their symptoms and medical concerns.
2. Guide patients to the appropriate medical department or specialist.
3. Answer questions about medications, procedures, appointments, and billing.
4. Provide general health education and preventive care guidance.
5. Collect symptom information for triage purposes.
6. Never diagnose or prescribe – always recommend professional consultation.
7. Immediately direct anyone describing emergencies (chest pain, difficulty breathing, stroke symptoms, severe bleeding) to call 911 or go to the ER.
8. Be empathetic, clear, and concise. Avoid medical jargon when possible.
9. Ask clarifying questions to better understand the patient's situation.
10. Respect patient privacy and handle all information with care.

When you have gathered enough information about symptoms, include a line at the end of your response in this exact format:
TRIAGE_READY: true

Always remind patients that AI assistance does not replace professional medical advice."""


async def get_ai_reply(
    messages: List[dict],
    patient_id: Optional[int] = None,
    db=None,
) -> str:
    """
    Get a reply from the AI assistant.
    Falls back to a rule-based response if OpenAI is not configured.
    """
    from healthcare.config import healthcare_settings

    # Build enriched system prompt with patient context if available
    system_content = _SYSTEM_PROMPT
    if patient_id and db:
        system_content += _get_patient_context(patient_id, db)

    openai_key = healthcare_settings.openai_api_key
    if not openai_key or openai_key == "your_openai_api_key_here":
        return _fallback_reply(messages)

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=openai_key)

        # Build message list for OpenAI
        openai_messages = [{"role": "system", "content": system_content}]
        # Include up to the last 20 messages to stay within context limits
        for msg in messages[-20:]:
            openai_messages.append({"role": msg["role"], "content": msg["content"]})

        response = await client.chat.completions.create(
            model=healthcare_settings.openai_model,
            messages=openai_messages,
            max_tokens=600,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        return _fallback_reply(messages)


def _get_patient_context(patient_id: int, db) -> str:
    """Build additional context from the patient's medical record."""
    try:
        from healthcare.models.patient import Patient
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return ""
        parts = [f"\n\nPatient context (for personalisation only – do not disclose to patient):"]
        if patient.allergies:
            parts.append(f"Known allergies: {', '.join(patient.allergies)}")
        if patient.current_medications:
            meds = [m.get("name", str(m)) for m in patient.current_medications]
            parts.append(f"Current medications: {', '.join(meds)}")
        if patient.past_medical_history:
            parts.append(f"Medical history: {', '.join(patient.past_medical_history)}")
        return "\n".join(parts)
    except Exception:
        return ""


def _fallback_reply(messages: List[dict]) -> str:
    """Rule-based fallback when OpenAI is not available."""
    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "").lower()
            break

    emergency_keywords = ["chest pain", "can't breathe", "stroke", "unconscious",
                          "bleeding heavily", "overdose", "suicide", "heart attack"]
    if any(kw in last_user_msg for kw in emergency_keywords):
        return (
            "⚠️ This sounds like a medical emergency. Please call 911 immediately "
            "or have someone take you to the nearest Emergency Room. "
            "Do not delay seeking emergency care."
        )

    if any(kw in last_user_msg for kw in ["appointment", "book", "schedule"]):
        return (
            "I can help you schedule an appointment. Please use the Appointments section "
            "of the portal, or tell me your symptoms and I'll recommend the right specialist."
        )

    if any(kw in last_user_msg for kw in ["bill", "payment", "insurance", "cost", "price"]):
        return (
            "For billing questions, please visit the Billing section of your patient portal. "
            "You can view your bills, check insurance claims, set up payment plans, and make payments there. "
            "Is there a specific billing question I can help answer?"
        )

    return (
        "Thank you for reaching out. I'm here to help with your medical questions 24/7. "
        "Could you describe your symptoms or what you need help with today? "
        "The more detail you provide, the better I can guide you."
    )
