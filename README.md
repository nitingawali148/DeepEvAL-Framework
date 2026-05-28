# Project 23 — DeepEval Framework

A complete, locally-runnable **LLM evaluation lab** for e-commerce AI features. Three independent subsystems work together: two real LLM-powered applications serve as targets, and one evaluation framework measures them with 22 metrics across quality, safety, retrieval, and conversational dimensions.

---

## System Map

```mermaid
graph TD
    A["01_chatbot<br/>ShopSphere Chatbot<br/>React + FastAPI + Groq<br/>:5173 / :8201"]
    B["02_rag_explorer<br/>RAG Explorer<br/>FastAPI + ChromaDB + Ollama + Groq<br/>:8202"]
    C["03_deepeval_framework<br/>Evaluation Engine<br/>DeepEval + pytest + Dashboard<br/>:8203"]

    A -->|"HTTP POST /chat"| C
    B -->|"HTTP POST /api/chat"| C
    C -->|"Judge LLM scores"| J["Judge LLM<br/>OpenAI / Groq / Ollama"]

    style A fill:#dbeafe,stroke:#3b82f6
    style B fill:#dcfce7,stroke:#22c55e
    style C fill:#fef9c3,stroke:#eab308
    style J fill:#f3e8ff,stroke:#a855f7
```

| Folder | What | Stack | Port |
|--------|------|-------|------|
| `01_chatbot/` | ShopSphere e-commerce chatbot — the app under test | React (Vite) + FastAPI + Groq | 5173 / 8201 |
| `02_rag_explorer/` | RAG pipeline with auditable stages | FastAPI + ChromaDB + Ollama + Groq | 8202 |
| `03_deepeval_framework/` | 22 metrics + live dashboard + swappable judge LLMs | DeepEval + pytest + FastAPI | 8203 |

---

## Screenshots

### DeepEval Dashboard (Subsystem C)
Live metric runs with target/judge dropdowns and per-card pass/fail indicators.
![DeepEval Dashboard](screenshots/DeepEval-Dashboard-04-26-2026_12_40_PM.png)

### ShopSphere Chatbot (Subsystem A)
React UI with FastAPI backend talking to Groq's `llama-3.3-70b-versatile`.
![ShopSphere Support Chat](screenshots/ShopSphere-—-Support-Chat-04-26-2026_12_41_PM.png)

### RAG Explorer (Subsystem B)
Pipeline dashboard exposing every stage from ingest through answer.
![RAG Explorer Dashboard](screenshots/Dashboard-·-RAG-Explorer-04-26-2026_12_41_PM.png)

---

## Why Three Subsystems?

You can't evaluate something you haven't built. Subsystems A and B are **real, working LLM applications** that exhibit real LLM failure modes — hallucination, weak retrieval, prompt leakage, biased output. Subsystem C points DeepEval at them and measures everything quantitatively.

```mermaid
flowchart LR
    subgraph "What We Evaluate"
        A["Subsystem A\nChatbot"] 
        B["Subsystem B\nRAG Pipeline"]
    end
    subgraph "How We Evaluate"
        C["Subsystem C\nDeepEval Framework"]
        J["Judge LLM\n(OpenAI / Groq / Ollama)"]
    end
    subgraph "Output"
        R["HTML Report"]
        D["Live Dashboard"]
    end

    A --> C
    B --> C
    C --> J
    J --> C
    C --> R
    C --> D
```

---

## End-to-End Evaluation Flow

```mermaid
sequenceDiagram
    participant T as Test Runner
    participant CS as Chatbot / RAG
    participant DV as DeepEval
    participant JL as Judge LLM

    T->>CS: POST /chat {message}
    CS-->>T: {reply, model, mode}
    T->>DV: LLMTestCase(input, actual_output, context?)
    DV->>JL: Score prompt (structured JSON)
    JL-->>DV: {score: 0.85, reason: "..."}
    DV-->>T: metric.score, metric.is_successful()
    T->>T: Assert pass/fail vs threshold
```

---

## Environment Variables

| Variable | Used By | Purpose | Default |
|----------|---------|---------|---------|
| `GROQ_API_KEY` | A, B, C | Groq LLM API key | — (mock mode if unset) |
| `OPENAI_API_KEY` | C | OpenAI judge key | — |
| `JUDGE_PROVIDER` | C | Judge LLM provider | `openai` |
| `JUDGE_MODEL_OPENAI` | C | Override OpenAI model | `gpt-4o-mini` |
| `JUDGE_MODEL_GROQ` | C | Override Groq model | `openai/gpt-oss-120b` |
| `JUDGE_MODEL_OLLAMA` | C | Override Ollama model | `gpt-oss:20b` |
| `OLLAMA_HOST` | B | Ollama base URL | `http://localhost:11434` |
| `CHATBOT_URL` | C | Subsystem A base URL | `http://localhost:8201` |
| `RAG_URL` | C | Subsystem B base URL | `http://localhost:8202` |
| `MAX_GOLDENS` | C | Cap test cases per metric | unlimited |
| `CHROMA_DIR` | B | ChromaDB persistence path | `chroma_db/` |

---

## One-Shot Setup

```bash
cd Project_23_DeepEvAL_Framework

# Shared Python venv
uv venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install all Python deps
uv pip install -r 01_chatbot/backend/requirements.txt \
               -r 02_rag_explorer/requirements.txt \
               -r 03_deepeval_framework/requirements.txt

# React frontend deps
cd 01_chatbot/frontend && npm install && cd ../..

# Pull embedding model into Ollama (one-time, ~270 MB)
ollama pull nomic-embed-text

# Set keys
export GROQ_API_KEY=gsk_...
export JUDGE_PROVIDER=groq          # or openai, or ollama
```

---

## Run Everything

Open **four terminals** from the project root (venv activated):

```bash
# Terminal 1 — Chatbot backend (port 8201)
cd 01_chatbot/backend && uvicorn app:app --reload --port 8201

# Terminal 2 — Chatbot frontend (port 5173)
cd 01_chatbot/frontend && npm run dev

# Terminal 3 — RAG Explorer (port 8202)
cd 02_rag_explorer && uvicorn app:app --reload --port 8202 --loop asyncio

# Terminal 4 — Evaluation dashboard (port 8203)  OR  batch pytest run
cd 03_deepeval_framework
uvicorn dashboard.app:app --port 8203 --loop asyncio   # live dashboard
# python run_all.py                                     # batch HTML report
```

| URL | What |
|-----|------|
| http://localhost:5173 | ShopSphere Chatbot UI |
| http://localhost:8202 | RAG Explorer |
| http://localhost:8203 | DeepEval Dashboard |

---

## Switching Judge LLMs

```bash
# OpenAI (highest quality)
export JUDGE_PROVIDER=openai   OPENAI_API_KEY=sk-...

# Groq OSS-120B (cheaper, fast)
export JUDGE_PROVIDER=groq     GROQ_API_KEY=gsk-...

# Local Ollama (no API costs, slower)
export JUDGE_PROVIDER=ollama   # uses http://localhost:11434
```

The same `CompatibleJudge` class handles all three — OpenAI, Groq, and Ollama all expose the same OpenAI-compatible wire protocol.

---

## Metrics at a Glance

| Category | Metrics | Target | Threshold |
|----------|---------|--------|-----------|
| Quality | Answer Relevancy, Faithfulness, Hallucination | Chatbot + RAG | 0.7 / 0.4 |
| Safety | Bias, Toxicity, PII Leakage, No Prompt Leak | Chatbot + RAG | 0.4 / 0.3 |
| Retrieval | Contextual Precision, Recall, Relevancy | RAG | 0.6 |
| G-Eval | Completeness, Correctness, Citation, Helpfulness | Chatbot + RAG | 0.5–0.7 |
| Conversational | Conversation Completeness, Knowledge Retention | Chatbot | 0.5 |
| Synthetic | Summarization | Independent | 0.5 |

---

## Deep-Dive Documentation

| File | Contents |
|------|----------|
| [01_chatbot.md](01_chatbot.md) | Chatbot architecture, request flow, data models, API reference |
| [02_rag_explorer.md](02_rag_explorer.md) | RAG pipeline stages, embedding, vector store, retrieval, answer generation |
| [03_deepeval_framework.md](03_deepeval_framework.md) | Evaluation architecture, all 22 metrics, judge LLM abstraction, execution modes |
| [project_flow.md](project_flow.md) | Full integration flow across all three subsystems |

## Per-Subsystem READMEs

- [01_chatbot/README.md](01_chatbot/README.md)
- [02_rag_explorer/README.md](02_rag_explorer/README.md)
- [03_deepeval_framework/README.md](03_deepeval_framework/README.md)
