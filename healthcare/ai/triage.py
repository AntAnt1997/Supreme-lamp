"""AI Triage engine – analyse symptom conversations and score urgency."""

import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_TRIAGE_PROMPT = """You are a medical triage AI. Analyse the following patient conversation and produce a JSON triage assessment.

Return ONLY valid JSON with these fields:
{
  "urgency_level": "emergency" | "urgent" | "routine" | "self_care",
  "suggested_department": "<department name from the healthcare system>",
  "triage_summary": "<1-2 sentence clinical summary>",
  "confidence": <0.0-1.0>,
  "red_flags": ["<symptom 1>", ...],
  "recommended_actions": ["<action 1>", ...]
}

Urgency definitions:
- emergency: life-threatening, call 911 / go to ER immediately
- urgent: needs care within hours (urgent care or same-day appointment)
- routine: can schedule regular appointment within days/weeks
- self_care: can manage at home with OTC remedies

Be conservative: when in doubt, escalate urgency."""


async def run_triage_if_needed(conv, messages: list, db) -> Optional[dict]:
    """
    Run triage if the conversation contains 'TRIAGE_READY: true' in the last assistant message
    or if there are enough messages (6+) and triage has not been done yet.
    """
    if conv.triage_completed:
        return None

    last_assistant = ""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            last_assistant = msg.get("content", "")
            break

    should_triage = (
        "TRIAGE_READY: true" in last_assistant
        or len(messages) >= 6
    )

    if not should_triage:
        return None

    return await force_run_triage(conv, db)


async def force_run_triage(conv, db) -> dict:
    """Run triage on the conversation regardless of state."""
    from healthcare.config import healthcare_settings

    messages = conv.messages or []
    # Build a readable transcript
    transcript = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages[-20:]
    )

    result = None
    openai_key = healthcare_settings.openai_api_key
    if openai_key and openai_key != "your_openai_api_key_here":
        result = await _llm_triage(transcript, healthcare_settings)

    if not result:
        result = _rule_based_triage(transcript)

    # Persist to conversation
    conv.triage_completed = True
    conv.urgency_level = result.get("urgency_level", "routine")
    conv.suggested_department = result.get("suggested_department", "Primary Care")
    conv.triage_summary = result.get("triage_summary", "")
    conv.triage_confidence = result.get("confidence", 0.5)

    # Find recommended provider
    if conv.suggested_department:
        provider = _find_provider(conv.suggested_department, db)
        if provider:
            conv.recommended_provider_id = provider.id

    return result


async def _llm_triage(transcript: str, settings) -> Optional[dict]:
    """Use OpenAI to perform triage analysis."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _TRIAGE_PROMPT},
                {"role": "user", "content": f"Patient conversation:\n{transcript}"},
            ],
            max_tokens=400,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as e:
        logger.error("LLM triage error: %s", e)
        return None


def _rule_based_triage(transcript: str) -> dict:
    """Keyword-based fallback triage."""
    text = transcript.lower()

    emergency_kw = [
        "chest pain", "can't breathe", "difficulty breathing", "stroke",
        "unconscious", "severe bleeding", "overdose", "suicide", "heart attack",
        "anaphylaxis", "seizure", "choking", "head trauma",
    ]
    urgent_kw = [
        "high fever", "severe pain", "vomiting blood", "broken bone",
        "deep cut", "allergic reaction", "severe headache", "confusion",
        "abdominal pain", "urinary tract infection",
    ]
    dental_kw = ["tooth", "dental", "gum", "jaw", "cavity", "orthodon", "denture"]
    mental_kw = ["anxiety", "depression", "depressed", "anxious", "panic", "mental", "psychiatric", "mood"]
    skin_kw = ["rash", "skin", "itching", "lesion", "acne"]

    if any(kw in text for kw in emergency_kw):
        return {
            "urgency_level": "emergency",
            "suggested_department": "Emergency Medicine",
            "triage_summary": "Potential emergency symptoms detected. Immediate care required.",
            "confidence": 0.9,
            "red_flags": [kw for kw in emergency_kw if kw in text],
            "recommended_actions": ["Call 911 or go to the nearest Emergency Room immediately"],
        }

    if any(kw in text for kw in urgent_kw):
        return {
            "urgency_level": "urgent",
            "suggested_department": "Urgent Care",
            "triage_summary": "Symptoms suggest urgent evaluation is needed.",
            "confidence": 0.75,
            "red_flags": [],
            "recommended_actions": ["Visit urgent care or call your doctor today"],
        }

    if any(kw in text for kw in dental_kw):
        return {
            "urgency_level": "routine",
            "suggested_department": "General Dentistry",
            "triage_summary": "Dental concern identified. Recommend dental appointment.",
            "confidence": 0.8,
            "red_flags": [],
            "recommended_actions": ["Schedule a dental appointment"],
        }

    if any(kw in text for kw in mental_kw):
        return {
            "urgency_level": "routine",
            "suggested_department": "Psychiatry",
            "triage_summary": "Mental health concern identified.",
            "confidence": 0.7,
            "red_flags": [],
            "recommended_actions": ["Schedule appointment with Psychiatry or Psychology"],
        }

    if any(kw in text for kw in skin_kw):
        return {
            "urgency_level": "routine",
            "suggested_department": "Dermatology",
            "triage_summary": "Skin-related concern identified.",
            "confidence": 0.7,
            "red_flags": [],
            "recommended_actions": ["Schedule a dermatology appointment"],
        }

    return {
        "urgency_level": "routine",
        "suggested_department": "Primary Care",
        "triage_summary": "General health concern. Recommend primary care evaluation.",
        "confidence": 0.5,
        "red_flags": [],
        "recommended_actions": ["Schedule an appointment with your primary care provider"],
    }


def _find_provider(department_name: str, db):
    """Find an active provider in the suggested department."""
    try:
        from healthcare.models.provider import Provider
        from healthcare.models.department import Department
        dept = db.query(Department).filter(Department.name == department_name).first()
        if not dept:
            return None
        return (
            db.query(Provider)
            .filter(Provider.department_id == dept.id, Provider.is_active == True)
            .order_by(Provider.average_rating.desc())
            .first()
        )
    except Exception:
        return None
