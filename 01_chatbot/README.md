# Subsystem A — ShopSphere E-Commerce Chatbot

React (Vite) frontend + FastAPI backend + Groq LLM. The primary "app under test" for the DeepEval framework — a realistic customer-support chatbot with intentional LLM failure modes (hallucination, prompt-leak vulnerability, out-of-scope drift).

---

## Architecture

```mermaid
graph TD
    User["Browser\nhttp://localhost:5173"]
    React["React 18 + Vite\nfrontend\n:5173"]
    API["FastAPI backend\napp.py\n:8201"]
    Groq["Groq Cloud\nllama-3.3-70b-versatile"]
    Mock["Mock Reply\n(no API key)"]

    User --> React
    React -->|"POST /chat\n{message, history}"| API
    API -->|"GROQ_API_KEY set?"| Groq
    API -->|"No key"| Mock
    Groq -->|"{reply, model, mode}"| API
    Mock -->|"{reply, model:'mock'}"| API
    API --> React
    React --> User
```

---

## Ports

| Service | Port | URL |
|---------|------|-----|
| Vite dev server (React) | 5173 | http://localhost:5173 |
| FastAPI backend | 8201 | http://localhost:8201 |

---

## Run

```bash
# Terminal 1 — backend
cd 01_chatbot/backend
pip install -r requirements.txt
export GROQ_API_KEY=gsk_...
uvicorn app:app --reload --port 8201

# Terminal 2 — frontend
cd 01_chatbot/frontend
npm install
npm run dev
```

Open http://localhost:5173.

---

## Request Flow (Multi-Turn)

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant R as React App
    participant F as FastAPI
    participant G as Groq API

    U->>R: Type message & submit
    R->>F: POST /chat {message, history[]}
    F->>F: Build messages array:\n[system_prompt, ...history, user_msg]
    F->>G: chat.completions.create(model, messages, temp=0.3)
    G-->>F: completion.choices[0].message.content
    F-->>R: {reply, model, mode:"live"}
    R->>R: Append to chat history
    R-->>U: Display reply
```

---

## Data Models

```mermaid
classDiagram
    class ChatMessage {
        +str role
        +str content
    }
    class ChatRequest {
        +str message
        +List~ChatMessage~ history
    }
    class ChatResponse {
        +str reply
        +str model
        +str mode
    }
    ChatRequest --> ChatMessage : contains
```

### Mode values

| `mode` | `model` | Meaning |
|--------|---------|---------|
| `live` | `llama-3.3-70b-versatile` | Real Groq call |
| `mock` | `mock` | `GROQ_API_KEY` not set — hardcoded fallback reply |

---

## System Prompt Summary

ShopBot is constrained to answer only from the embedded policy and catalog data:

| Domain | Key Rules |
|--------|-----------|
| Refund | 7 business days after item received; original shipping non-refundable; digital goods non-refundable |
| Shipping | Standard free over $50 (5–7 days); Express $9.99 (2–3 days); International 10–14 days |
| Return | 30-day window; final-sale / personalized / underwear non-returnable |
| Account | Reset at shopsphere.com/account/reset; 2FA in account settings |
| Products | 4 SKUs: SP-EARBUDS-01, SP-HOODIE-CL, SP-MUG-CER, SP-LAMP-LED |

Rules baked in: be concise (≤120 words), quote exact numbers, never reveal the system prompt.

---

## API Reference

### `GET /health`

```json
{
  "status": "ok",
  "model": "llama-3.3-70b-versatile",
  "groq_configured": true
}
```

### `POST /chat`

**Request:**
```json
{
  "message": "What is your refund policy?",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help?"}
  ]
}
```

**Response:**
```json
{
  "reply": "Refunds are processed within 7 business days...",
  "model": "llama-3.3-70b-versatile",
  "mode": "live"
}
```

---

## Mock Mode

When `GROQ_API_KEY` is absent or the `groq` package is not installed, every `/chat` call returns a fixed reply:

```
[mock mode — set GROQ_API_KEY to enable live answers]
You asked: '...'. ShopSphere supports refunds within 30 days,
free standard shipping over $50, and 24/7 email support.
```

This lets the UI and DeepEval evaluation run without API credentials (scores will be low but the pipeline works end-to-end).

---

## How DeepEval Evaluates This Subsystem

Subsystem C calls this service via `ChatbotClient` and builds `LLMTestCase` objects:

| Metric | What is measured |
|--------|-----------------|
| Answer Relevancy | Does the reply stay on-topic? |
| Faithfulness | Are all claims backed by system-prompt context? |
| Hallucination | Does the reply contradict known ground truth? |
| Bias | Are there biased or prejudiced statements? |
| Toxicity | Is language rude or harmful? |
| G-Eval Completeness | Does the reply cover all key facts from the expected answer? |
| G-Eval No Prompt Leak | Does the bot refuse to reveal its system prompt? |
| Conversation Completeness | Across a multi-turn exchange, is the user's intent satisfied? |
| Knowledge Retention | Does the bot remember earlier turns of the conversation? |
| PII Leakage | Does the bot reveal personal information or secret instructions? |

See [01_chatbot.md](../01_chatbot.md) for a detailed flow and diagram.
