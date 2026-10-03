import time
import requests
from fastapi import FastAPI, Request

app = FastAPI()

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

SYSTEM_PROMPT = (
    "You are a helpful, conversational voice assistant. Keep all responses concise, "
    "natural, and strictly under 2-3 sentences so they can be spoken clearly. "
    "Do not use markdown, bullet points, or special characters."
)

# In-memory session store: {session_id: {"messages": [...], "last_active": timestamp}}
sessions: dict[str, dict] = {}
SESSION_TTL_SECONDS = 600

def cleanup_expired_sessions():
    now = time.time()
    expired = [
        sid for sid, data in sessions.items()
        if now - data["last_active"] > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del sessions[sid]

def build_alexa_response(speech_text: str, end_session: bool = False, reprompt_text: str = None):
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": speech_text},
            "shouldEndSession": end_session,
        },
    }
    if not end_session and reprompt_text:
        response["response"]["reprompt"] = {
            "outputSpeech": {"type": "PlainText", "text": reprompt_text}
        }
    return response

@app.post("/alexa")
async def handle_alexa(request: Request):
    cleanup_expired_sessions()
    payload = await request.json()

    req = payload.get("request", {})
    req_type = req.get("type")
    session = payload.get("session", {})
    session_id = session.get("sessionId")

    # 1. User launches: "Alexa, open Local Assistant"
    if req_type == "LaunchRequest":
        sessions[session_id] = {
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
            "last_active": time.time(),
        }
        return build_alexa_response(
            speech_text="I'm listening. What's on your mind?",
            end_session=False,
            reprompt_text="Are you still there? You can ask me anything.",
        )

    # 2. Conversational turns
    elif req_type == "IntentRequest":
        intent_name = req["intent"]["name"]

        # Exit phrases
        if intent_name in ["AMAZON.StopIntent", "AMAZON.CancelIntent", "ExitIntent"]:
            if session_id in sessions:
                del sessions[session_id]
            return build_alexa_response(speech_text="Goodbye!", end_session=True)

        if intent_name == "PromptIntent":
            user_input = req["intent"]["slots"]["query"].get("value", "").strip()

            if session_id not in sessions:
                sessions[session_id] = {
                    "messages": [{"role": "system", "content": SYSTEM_PROMPT}],
                    "last_active": time.time(),
                }

            history = sessions[session_id]["messages"]
            history.append({"role": "user", "content": user_input})
            sessions[session_id]["last_active"] = time.time()

            # Keep last 6 turns to stay fast and avoid Alexa's 8-second timeout
            if len(history) > 7:
                history = [history[0]] + history[-6:]
                sessions[session_id]["messages"] = history

            try:
                res = requests.post(
                    LM_STUDIO_URL,
                    json={
                        "model": "local-model",
                        "messages": history,
                        "max_tokens": 100,
                        "temperature": 0.7,
                    },
                    timeout=6.0,
                )
                assistant_reply = res.json()["choices"][0]["message"]["content"]
            except Exception:
                assistant_reply = "I had trouble processing that. What else can I help with?"

            history.append({"role": "assistant", "content": assistant_reply})

            # Mic stays open for immediate follow-up
            return build_alexa_response(
                speech_text=assistant_reply,
                end_session=False,
                reprompt_text="Anything else you'd like to ask?",
            )

    elif req_type == "SessionEndedRequest":
        if session_id in sessions:
            del sessions[session_id]
        return build_alexa_response(speech_text="", end_session=True)

    return build_alexa_response(speech_text="I didn't quite catch that.", end_session=False)
