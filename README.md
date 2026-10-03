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
