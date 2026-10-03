import time
import requests
from fastapi import FastAPI, Request
from app.database import init_db, get_recent_context, log_event

app = FastAPI(title="Alexa Local LLM Assistant")

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"[cite: 8]
sessions: dict[str, dict] = {}
SESSION_TTL_SECONDS = 600[cite: 9]

init_db()

def cleanup_expired_sessions():
    now = time.time()[cite: 9]
    expired = [sid for sid, d in sessions.items() if now - d["last_active"] > SESSION_TTL_SECONDS][cite: 9]
    for sid in expired:
        del sessions[sid][cite: 9]

def build_alexa_response(speech_text: str, end_session: bool = False, reprompt_text: str = None):
    res = {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": speech_text},
            "shouldEndSession": end_session,
        },
    }[cite: 9]
    if not end_session and reprompt_text:
        res["response"]["reprompt"] = {
            "outputSpeech": {"type": "PlainText", "text": reprompt_text}
        }[cite: 9]
    return res[cite: 9]

@app.post("/alexa")
async def handle_alexa(request: Request):
    cleanup_expired_sessions()[cite: 9]
    payload = await request.json()[cite: 8, 9]

    req = payload.get("request", {})[cite: 8, 9]
    req_type = req.get("type")[cite: 8, 9]
    session_id = payload.get("session", {}).get("sessionId")[cite: 9]

    dynamic_system_prompt = (
        "You are a local, private voice assistant running offline on the user's Mac. "
        "Keep responses conversational, concise, and under 2-3 sentences. "
        "Do not use markdown, emojis, or bullet points. "
        f"{get_recent_context()}"
    )

    if req_type == "LaunchRequest":
        sessions[session_id] = {
            "messages": [{"role": "system", "content": dynamic_system_prompt}],
            "last_active": time.time(),
        }[cite: 9]
        return build_alexa_response(
            speech_text="Local Assistant online. How can I help you?",
            end_session=False,
            reprompt_text="I'm still listening. What would you like to ask or track?"
        )

    elif req_type == "IntentRequest":
        intent_name = req.get("intent", {}).get("name")[cite: 8, 9]

        if intent_name in ["AMAZON.StopIntent", "AMAZON.CancelIntent"]:
            if session_id in sessions:
                del sessions[session_id][cite: 9]
            return build_alexa_response(speech_text="Goodbye!", end_session=True)[cite: 9]

        if intent_name in ["PromptIntent", "AMAZON.FallbackIntent"]:
            slots = req.get("intent", {}).get("slots", {})
            user_input = slots.get("query", {}).get("value", "").strip()[cite: 9]

            if not user_input:
                return build_alexa_response(
                    speech_text="I didn't quite catch that. Could you repeat?",
                    end_session=False,
                    reprompt_text="Please repeat your request."
                )

            # Auto-log memory if trigger phrases are present
            if any(trigger in user_input.lower() for trigger in ["remember that", "take a note", "log that"]):
                log_event("user_note", user_input)

            if session_id not in sessions:
                sessions[session_id] = {
                    "messages": [{"role": "system", "content": dynamic_system_prompt}],
                    "last_active": time.time(),
                }[cite: 9]

            history = sessions[session_id]["messages"]
            history.append({"role": "user", "content": user_input})[cite: 9]
            sessions[session_id]["last_active"] = time.time()[cite: 9]

            # Rolling context window (system prompt + last 6 turns) to prevent Alexa's 8s timeout
            if len(history) > 7:
                history = [history[0]] + history[-6:][cite: 9]
                sessions[session_id]["messages"] = history[cite: 9]

            try:
                res = requests.post(
                    LM_STUDIO_URL,[cite: 8, 9]
                    json={
                        "model": "local-model",[cite: 8, 9]
                        "messages": history,[cite: 9]
                        "max_tokens": 100,[cite: 9]
                        "temperature": 0.7,[cite: 8, 9]
                    },
                    timeout=5.5  # Prevents exceeding Alexa's 8-second hard window[cite: 8, 9]
                )
                assistant_reply = res.json()["choices"][0]["message"]["content"][cite: 8, 9]
            except Exception:
                assistant_reply = "I had trouble processing that locally. What else can I help with?"[cite: 9]

            history.append({"role": "assistant", "content": assistant_reply})[cite: 9]

            return build_alexa_response(
                speech_text=assistant_reply,
                end_session=False,
                reprompt_text="Anything else?"
            )

    elif req_type == "SessionEndedRequest":
        if session_id in sessions:
            del sessions[session_id][cite: 9]
        return build_alexa_response(speech_text="", end_session=True)[cite: 9]

    return build_alexa_response(speech_text="I didn't understand that.", end_session=False)
