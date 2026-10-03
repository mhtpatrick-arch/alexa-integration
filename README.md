# Local Alexa LLM Assistant with Long-Term Memory

Bridge an Amazon Echo Dot with an offline open-source Large Language Model (e.g., Llama 3.1 8B, Qwen 2.5) running locally on Apple Silicon via LM Studio. 

Includes persistent multi-turn conversational memory, local SQLite state tracking, and zero recurring cloud LLM API costs.

---

## Architecture Flow

[Echo Dot]
└── (Audio) ──► [Amazon ASK Cloud (ASR/NLU)]
└── (JSON Webhook) ──► [Ngrok Static Domain]
└── (Encrypted Tunnel) ──► [FastAPI :8000]
├── [SQLite Memory]
└── [LM Studio :1234]


1. **Voice Input**: Amazon Echo captures natural speech and transcribes it via Alexa Skills Kit (ASK).
2. **Ingress**: A permanent Ngrok static domain proxies Alexa's webhook directly to your machine.
3. **Context & State Management**: FastAPI manages the rolling conversation history, queries persistent SQLite memory, and constructs the agent prompt.
4. **Local Inference**: LM Studio generates responses locally in 1-2 seconds using Apple Silicon unified memory.
5. **Continuous Conversation**: The skill returns `shouldEndSession: false`, keeping the microphone open for fluid dialogue without wake-word repetition.

---

## Prerequisites

- **MacBook** (Apple Silicon M1/M2/M3/M4 recommended)
- **LM Studio** installed and running
- **Amazon Echo Dot** or Alexa-enabled device
- **Python 3.10+**
- **Ngrok Account** (Free tier with 1 static dev domain)
- **Amazon Developer Account** (Free tier)

---

## Quick Start

### 1. Clone & Set Up Python Environment
```bash
git clone [https://github.com/](https://github.com/)<your-username>/alexa-local-llm-assistant.git
cd alexa-local-llm-assistant

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


2. Configure LM Studio
Open LM Studio and download an instruction model (e.g., Meta-Llama-3.1-8B-Instruct-GGUF).

Go to the Local Server tab (<-> icon).

Ensure port is set to 1234 and click Start Server.

3. Start the Ingress Tunnel
Authenticate Ngrok and claim your free static domain from your Ngrok dashboard:

ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
ngrok http 8000 --url=https://<YOUR-STATIC-DOMAIN>.ngrok-free.dev


4. Start the FastAPI Middleware
In a new terminal window:

Bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
5. Configure Alexa Skills Kit (ASK)
Go to the Alexa Developer Console.

Create a new skill: Local Assistant -> Custom -> Provision your own.

Under Interaction Model -> JSON Editor, import alexa_skill_model/interaction_model.json and click Build Model.

Under Endpoint -> HTTPS:

Set Default Region to: https://<YOUR-STATIC-DOMAIN>.ngrok-free.dev/alexa

Select: "My development endpoint is a sub-domain of a domain that has a wildcard certificate from a certificate authority."

Click Save Endpoints.

Daily Life Tracking & Usage
Continuous Chat
Say:

"Alexa, open Local Assistant."

"Tell me three facts about Mars."

(Wait for answer)

"What is its largest volcano?" (No need to repeat "Alexa" or the invocation).

Habit & Note Tracking
"Alexa, ask Local Assistant to note that I completed my workout and drank 3 liters of water."

The agent parses this and writes a timestamped record directly into local SQLite assistant_memory.db.

Latency & Alexa's 8-Second Deadline
Alexa enforces a strict 8-second response ceiling:

Stick to 7B-8B quantized models (Q4_K_M or Q8_0) to maintain sub-2-second Time-To-First-Token (TTFT).

The middleware automatically caps rolling context history to the last 6 turns to avoid context-length inference bottlenecks.

