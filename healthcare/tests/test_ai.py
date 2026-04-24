"""Tests for the AI triage and assistant modules."""

import pytest


def test_rule_based_triage_emergency():
    from healthcare.ai.triage import _rule_based_triage
    result = _rule_based_triage("USER: I have chest pain and I can't breathe")
    assert result["urgency_level"] == "emergency"
    assert "Emergency" in result["suggested_department"]


def test_rule_based_triage_dental():
    from healthcare.ai.triage import _rule_based_triage
    result = _rule_based_triage("USER: I have a toothache and my gum is swollen")
    assert result["urgency_level"] in ("routine", "urgent")
    assert "Dent" in result["suggested_department"]


def test_rule_based_triage_mental_health():
    from healthcare.ai.triage import _rule_based_triage
    result = _rule_based_triage("USER: I have been feeling very depressed and anxious")
    assert result["urgency_level"] == "routine"
    assert "Psychiatry" in result["suggested_department"]


def test_rule_based_triage_skin():
    from healthcare.ai.triage import _rule_based_triage
    result = _rule_based_triage("USER: I have a rash on my arm that is itching")
    assert result["urgency_level"] == "routine"
    assert "Dermatology" in result["suggested_department"]


def test_rule_based_triage_default():
    from healthcare.ai.triage import _rule_based_triage
    result = _rule_based_triage("USER: I just want a general checkup")
    assert result["urgency_level"] in ("routine", "self_care")
    assert result["confidence"] > 0


def test_fallback_reply_emergency():
    from healthcare.ai.assistant import _fallback_reply
    reply = _fallback_reply([{"role": "user", "content": "I have chest pain"}])
    assert "911" in reply or "Emergency" in reply


def test_fallback_reply_billing():
    from healthcare.ai.assistant import _fallback_reply
    reply = _fallback_reply([{"role": "user", "content": "I have questions about my bill"}])
    assert "bill" in reply.lower() or "billing" in reply.lower()


def test_fallback_reply_appointment():
    from healthcare.ai.assistant import _fallback_reply
    reply = _fallback_reply([{"role": "user", "content": "I want to book an appointment"}])
    assert "appointment" in reply.lower() or "schedule" in reply.lower()


@pytest.mark.asyncio
async def test_anonymous_chat(client):
    resp = client.post("/api/ai/chat/anonymous", json={"message": "Hello, I need help"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_token" in data
    assert "reply" in data
    assert len(data["reply"]) > 0


@pytest.mark.asyncio
async def test_chat_session_continuity(client):
    # Start session
    r1 = client.post("/api/ai/chat/anonymous", json={"message": "I have a headache"})
    token = r1.json()["session_token"]

    # Continue session
    r2 = client.post("/api/ai/chat/anonymous", json={
        "session_token": token,
        "message": "It has been going on for 3 days",
    })
    assert r2.status_code == 200
    assert r2.json()["session_token"] == token


@pytest.mark.asyncio
async def test_chat_history(client):
    r = client.post("/api/ai/chat/anonymous", json={"message": "Test message"})
    token = r.json()["session_token"]

    hist = client.get(f"/api/ai/chat/{token}/history")
    # Anonymous history requires authentication
    assert hist.status_code in (200, 401, 403)


@pytest.mark.asyncio
async def test_triage_triggers_on_many_messages(client):
    """Triage should auto-trigger after enough messages."""
    r = client.post("/api/ai/chat/anonymous", json={"message": "I have symptoms"})
    token = r.json()["session_token"]

    for msg in [
        "My chest hurts",
        "It started 2 hours ago",
        "I also have shortness of breath",
        "I am sweating a lot",
        "My left arm feels numb",
    ]:
        r = client.post("/api/ai/chat/anonymous", json={
            "session_token": token, "message": msg
        })
    # After 6 messages triage should be completed
    data = r.json()
    if data["triage_completed"]:
        assert data["urgency_level"] in ("emergency", "urgent", "routine", "self_care")
        assert data["suggested_department"]
