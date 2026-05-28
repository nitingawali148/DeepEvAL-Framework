# Project Flow — Full Integration of All Three Subsystems

This document covers the complete picture: how the three subsystems connect, how data flows end-to-end from a user message through the LLM to an evaluation score, and how to run the whole lab from zero.

---

## 1. The Big Picture

```mermaid
graph TD
    subgraph "Subsystem A — ShopSphere Chatbot"
        UI["React Chat UI\n:5173"]
        CB["FastAPI Chatbot\n:8201"]
        GROQ_A["Groq LLM\nllama-3.3-70b-versatile"]
        UI -->|POST /chat| CB
        CB --> GROQ_A
    end

    subgraph "Subsystem B — RAG Explorer"
        RAG_APP["FastAPI RAG\n:8202"]
        OLLAMA["Ollama\nnomic-embed-text"]
        CHROMA["ChromaDB\nvector store"]
        GROQ_B["Groq LLM\nllama-3.3-70b-versatile"]
        CORPUS["5 e-commerce docs\nrefund / return / shipping\nproducts / FAQ"]
        CORPUS --> OLLAMA --> CHROMA
        RAG_APP --> OLLAMA
        RAG_APP --> CHROMA
        RAG_APP --> GROQ_B
    end

    subgraph "Subsystem C — DeepEval Framework"
        DASH["Dashboard :8203\nor pytest CLI"]
        RUNNER["runner.py\nrun_metric()"]
        REG["registry.py\n22 MetricDef"]
        JUDGE["CompatibleJudge\nOpenAI / Groq / Ollama"]
        RESULT["Score + Reason\npass/fail"]
        DASH --> RUNNER
        RUNNER --> REG
        RUNNER --> JUDGE
        RUNNER --> RESULT
    end

    RUNNER -->|"ChatbotClient\nPOST :8201/chat"| CB
    RUNNER -->|"RagClient\nPOST :8202/api/chat"| RAG_APP

    style UI fill:#dbeafe,stroke:#3b82f6
    style CB fill:#dbeafe,stroke:#3b82f6
    style GROQ_A fill:#dbeafe,stroke:#3b82f6
    style RAG_APP fill:#dcfce7,stroke:#22c55e
    style OLLAMA fill:#dcfce7,stroke:#22c55e
    style CHROMA fill:#dcfce7,stroke:#22c55e
    style GROQ_B fill:#dcfce7,stroke:#22c55e
    style CORPUS fill:#dcfce7,stroke:#22c55e
    style DASH fill:#fef9c3,stroke:#eab308
    style RUNNER fill:#fef9c3,stroke:#eab308
    style REG fill:#fef9c3,stroke:#eab308
    style JUDGE fill:#f3e8ff,stroke:#a855f7
    style RESULT fill:#fef9c3,stroke:#eab308
```

---

## 2. End-to-End: Evaluating the Chatbot

Step-by-step flow when `run_metric("chatbot.answer_relevancy", sample_idx=0)` is called:

```mermaid
sequenceDiagram
    actor Dev as Developer / Dashboard
    participant C as runner.py
    participant R as registry.py
    participant G as chatbot_goldens.py
    participant CB as ChatbotClient → :8201
    participant GROQ_A as Groq (Chatbot)
    participant DV as DeepEval
    participant JD as Judge LLM

    Dev->>C: run_metric("chatbot.answer_relevancy", 0)
    C->>R: lookup MetricDef by id
    R-->>C: {threshold:0.7, factory:_ar, sample_kind:"golden", ...}
    C->>G: CHATBOT_GOLDENS[0]
    G-->>C: ChatbotGolden(input="What is your refund window?", expected=...)
    C->>CB: chatbot.chat("What is your refund window?")
    CB->>GROQ_A: POST /chat {message, history:[]}
    GROQ_A-->>CB: "Refunds are processed within 7 business days..."
    CB-->>C: ChatbotReply(reply, model, mode)
    C->>DV: LLMTestCase(\n  input="What is your refund window?",\n  actual_output="Refunds are processed..."\n)
    C->>DV: AnswerRelevancyMetric(threshold=0.7).measure(tc)
    DV->>JD: Structured prompt:\n"Is the output relevant to the input?\nScore 0.0–1.0."
    JD-->>DV: {score: 0.92, reason: "Directly answers the refund timing question."}
    DV-->>C: score=0.92, is_successful()=True
    C-->>Dev: {ok:true, passed:true, score:0.92, reason:"...", elapsed_ms:1100}
```

---

## 3. End-to-End: Evaluating the RAG Pipeline

Step-by-step flow when `run_metric("rag.contextual_precision", sample_idx=0)` is called:

```mermaid
sequenceDiagram
    actor Dev as Developer / Dashboard
    participant C as runner.py
    participant G as rag_goldens.py
    participant RC as RagClient → :8202
    participant OLL as Ollama (embed)
    participant CHR as ChromaDB
    participant GROQ_B as Groq (RAG)
    participant DV as DeepEval
    participant JD as Judge LLM

    Dev->>C: run_metric("rag.contextual_precision", 0)
    C->>G: RAG_GOLDENS[0]
    G-->>C: RagGolden(input="What is the refund processing time?",\n  expected_sources=["refund_policy.md"])
    C->>RC: rag.chat("What is the refund processing time?")

    rect rgb(220, 252, 231)
        Note over RC,GROQ_B: Inside RAG pipeline (:8202)
        RC->>OLL: embed_query("What is the refund processing time?")
        OLL-->>RC: 768-dim vector
        RC->>CHR: similarity_search(vector, top_k=4)
        CHR-->>RC: [Hit(refund_policy.md, 0.91), Hit(faq.md, 0.72), ...]
        RC->>GROQ_B: "Answer from context:\n[refund_policy.md #0]\nRefunds processed..."
        GROQ_B-->>RC: "Refunds take 7 business days [refund_policy.md]."
    end

    RC-->>C: RagReply(\n  answer="Refunds take 7 business days...",\n  retrieval_context=["Refunds processed...", "..."],\n  sources=["refund_policy.md", "faq.md"]\n)
    C->>DV: LLMTestCase(\n  input="What is the refund...",\n  actual_output="Refunds take 7...",\n  expected_output="Refunds are processed within 7...",\n  retrieval_context=["Refunds processed...", "..."]\n)
    C->>DV: ContextualPrecisionMetric(threshold=0.6).measure(tc)
    DV->>JD: "Are the most relevant chunks ranked first?\nScore 0.0–1.0."
    JD-->>DV: {score: 0.88, reason: "refund_policy.md ranked first, most relevant."}
    DV-->>C: score=0.88, is_successful()=True
    C-->>Dev: {ok:true, passed:true, score:0.88, reason:"...", elapsed_ms:1850}
```

---

## 4. How All Three Subsystems Connect

```mermaid
graph LR
    subgraph "Data Sources"
        GC["chatbot_goldens.py\n8 golden cases"]
        GR["rag_goldens.py\n8 golden cases"]
        SP["SAFETY_PROMPTS\n5 adversarial"]
        PII["PII_PROBES\n4 injection tests"]
        CV["CONVERSATIONS\n2 multi-turn scripts"]
        SUM["SUMMARY_SOURCE\n1 refund passage"]
    end

    subgraph "Runner (runner.py)"
        BUILD["Build\nLLMTestCase /\nConversationalTestCase"]
    end

    subgraph "Targets"
        A[":8201 Chatbot\nllm_providers → Groq"]
        B[":8202 RAG\nOllama + ChromaDB + Groq"]
    end

    subgraph "Evaluation"
        METRIC["DeepEval Metric\n22 types"]
        JUDGE["Judge LLM\nCompatibleJudge\nOpenAI / Groq / Ollama"]
    end

    GC --> BUILD
    GR --> BUILD
    SP --> BUILD
    PII --> BUILD
    CV --> BUILD
    SUM --> BUILD

    BUILD -->|chatbot metrics| A
    BUILD -->|rag metrics| B
    A -->|reply| BUILD
    B -->|answer + retrieval_context| BUILD

    BUILD --> METRIC
    METRIC --> JUDGE
    JUDGE --> METRIC
```

---

## 5. Startup Order

The three subsystems must start in order because the evaluation framework depends on the other two:

```mermaid
flowchart TD
    S0["0. Pull Ollama model\nollama pull nomic-embed-text\n(one-time)"]
    S1A["1a. Start Chatbot Backend\nuvicorn app:app --port 8201"]
    S1B["1b. Start RAG Explorer\nuvicorn app:app --port 8202"]
    S1C["1c. Start Chatbot Frontend\nnpm run dev  (optional — for UI)"]
    S2["2. Seed RAG corpus\nPOST :8202/api/ingest/seed?reset=true"]
    S3["3. Start Evaluation\ndashboard :8203  OR  pytest"]

    S0 --> S1A
    S0 --> S1B
    S0 --> S1C
    S1A --> S2
    S1B --> S2
    S2 --> S3
```

---

## 6. Service Dependency Map

```mermaid
graph LR
    C["Subsystem C\nDeepEval :8203"]
    A["Subsystem A\nChatbot :8201"]
    B["Subsystem B\nRAG :8202"]
    GROQ["Groq Cloud API"]
    OAI["OpenAI API"]
    OLL["Ollama :11434"]
    CHR["ChromaDB"]

    C -->|"needs for chatbot metrics"| A
    C -->|"needs for RAG metrics"| B
    C -->|"judge LLM (if openai)"| OAI
    C -->|"judge LLM (if groq)"| GROQ
    C -->|"judge LLM (if ollama)"| OLL
    A -->|"LLM answers"| GROQ
    B -->|"LLM answers"| GROQ
    B -->|"embeddings"| OLL
    B -->|"vector store"| CHR
```

**What is strictly required vs optional:**

| Service | Required for | What happens if absent |
|---------|-------------|----------------------|
| Groq API key | Live chatbot + RAG answers | Mock mode (deterministic replies) |
| Ollama | Semantic embeddings in RAG | Hash-based embeddings (retrieval quality degraded) |
| ChromaDB | RAG persistent store | In-memory fallback (no persistence) |
| OpenAI API | OpenAI judge | Cannot use `JUDGE_PROVIDER=openai` |
| Subsystem A | Chatbot metrics | Chatbot tests auto-skipped |
| Subsystem B | RAG metrics | RAG tests auto-skipped |

---

## 7. All Ports at a Glance

| Port | Service | Start Command |
|------|---------|---------------|
| 5173 | Chatbot React UI | `cd 01_chatbot/frontend && npm run dev` |
| 8201 | Chatbot FastAPI | `cd 01_chatbot/backend && uvicorn app:app --reload --port 8201` |
| 8202 | RAG Explorer | `cd 02_rag_explorer && uvicorn app:app --reload --port 8202 --loop asyncio` |
| 8203 | DeepEval Dashboard | `cd 03_deepeval_framework && uvicorn dashboard.app:app --port 8203 --loop asyncio` |
| 11434 | Ollama | `ollama serve` (usually auto-started) |

---

## 8. Shared Environment Variables

```mermaid
graph LR
    ENV["Environment Variables"]

    ENV -->|"GROQ_API_KEY"| A["Chatbot :8201\nRAG :8202\nSummarization runner"]
    ENV -->|"OPENAI_API_KEY"| C1["Judge (openai)"]
    ENV -->|"JUDGE_PROVIDER"| C2["factory.py → CompatibleJudge"]
    ENV -->|"JUDGE_MODEL_*"| C3["Override judge model"]
    ENV -->|"CHATBOT_URL"| C4["ChatbotClient base URL"]
    ENV -->|"RAG_URL"| C5["RagClient base URL"]
    ENV -->|"MAX_GOLDENS"| C6["Cap golden cases/metric"]
    ENV -->|"OLLAMA_HOST"| B["RAG embed.py"]
    ENV -->|"CHROMA_DIR"| B2["RAG store.py"]
```

---

## 9. Metric-to-Subsystem Mapping

```mermaid
graph TD
    subgraph "Subsystem A — Chatbot Metrics (10)"
        AR_C["Answer Relevancy"]
        FA_C["Faithfulness"]
        HA_C["Hallucination"]
        BI_C["Bias"]
        TO_C["Toxicity"]
        PII_C["PII Leakage"]
        NPL_C["No Prompt Leak"]
        GE_C["G-Eval Completeness"]
        CC_C["Conv. Completeness"]
        KR_C["Knowledge Retention"]
    end
    subgraph "Subsystem B — RAG Metrics (11)"
        CP_R["Contextual Precision"]
        CR_R["Contextual Recall"]
        CV_R["Contextual Relevancy"]
        FA_R["Faithfulness"]
        AR_R["Answer Relevancy"]
        HA_R["Hallucination"]
        CO_R["G-Eval Correctness"]
        CI_R["G-Eval Citation Quality"]
        HE_R["G-Eval Helpfulness"]
        BI_R["Bias"]
        TO_R["Toxicity"]
    end
    subgraph "Independent (1)"
        SU["Summarization"]
    end
```

---

## 10. Complete Setup & Run (Zero to Evaluation)

```bash
# ── STEP 1: Clone and install ──────────────────────────────────────
cd Project_23_DeepEvAL_Framework
uv venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
uv pip install -r 01_chatbot/backend/requirements.txt \
               -r 02_rag_explorer/requirements.txt \
               -r 03_deepeval_framework/requirements.txt
cd 01_chatbot/frontend && npm install && cd ../..
ollama pull nomic-embed-text       # one-time ~270MB download

# ── STEP 2: Set environment ────────────────────────────────────────
export GROQ_API_KEY=gsk_...        # for chatbot + RAG answers
export JUDGE_PROVIDER=groq         # groq | openai | ollama
# export OPENAI_API_KEY=sk-...     # if JUDGE_PROVIDER=openai

# ── STEP 3: Start all services (4 terminals) ──────────────────────
# Terminal 1
cd 01_chatbot/backend && uvicorn app:app --reload --port 8201

# Terminal 2
cd 01_chatbot/frontend && npm run dev

# Terminal 3
cd 02_rag_explorer && uvicorn app:app --reload --port 8202 --loop asyncio

# Terminal 4 — seed RAG corpus then start dashboard
curl -X POST "http://localhost:8202/api/ingest/seed?reset=true"
cd 03_deepeval_framework
uvicorn dashboard.app:app --port 8203 --loop asyncio

# ── STEP 4: Evaluate ──────────────────────────────────────────────
# Option A: Interactive dashboard
open http://localhost:8203

# Option B: Full batch run with HTML report
cd 03_deepeval_framework
python run_all.py
open reports/report.html

# Option C: Quick smoke test (2 cases/metric, chatbot only)
python run_all.py --only chatbot --max-goldens 2
```

---

## 11. Typical Evaluation Run Timeline

```mermaid
gantt
    title Approximate Duration of a Full Evaluation Run
    dateFormat  mm:ss
    axisFormat  %M:%S

    section Setup
    Services start up          : 00:00, 15s
    RAG corpus seeding         : 00:15, 10s

    section Chatbot Metrics
    Smoke test                 : 00:25, 5s
    Answer Relevancy × 8       : 00:30, 60s
    Faithfulness × 8           : 01:30, 90s
    Hallucination × 8          : 03:00, 60s
    Bias × 5 safety prompts    : 04:00, 45s
    Toxicity × 5               : 04:45, 45s
    G-Eval Completeness × 8    : 05:30, 90s
    PII tests                  : 07:00, 30s
    Conversation metrics       : 07:30, 60s

    section RAG Metrics
    Contextual metrics × 8     : 08:30, 120s
    Faithfulness × 8           : 10:30, 90s
    Answer Relevancy × 8       : 12:00, 60s
    Hallucination × 8          : 13:00, 60s
    G-Eval metrics × 8 × 3     : 14:00, 180s
    Safety metrics × 5 × 2     : 17:00, 90s

    section Independent
    Summarization              : 18:30, 30s
```

*Times are approximate and vary by judge LLM speed. Groq is typically the fastest.*

---

## 12. Document Map

| Document | What it covers |
|----------|---------------|
| [README.md](README.md) | Project overview, setup, run commands, metric summary |
| [01_chatbot.md](01_chatbot.md) | Chatbot architecture, request flow, data models, mock mode, golden cases |
| [02_rag_explorer.md](02_rag_explorer.md) | RAG pipeline stages, embedding, vector store, retrieval, answer generation |
| [03_deepeval_framework.md](03_deepeval_framework.md) | Evaluation engine, judge abstraction, all 22 metrics, execution modes |
| [project_flow.md](project_flow.md) | **This file** — full integration, end-to-end flows, startup order |
| [01_chatbot/README.md](01_chatbot/README.md) | Chatbot quick reference + API |
| [02_rag_explorer/README.md](02_rag_explorer/README.md) | RAG Explorer quick reference + API |
| [03_deepeval_framework/README.md](03_deepeval_framework/README.md) | DeepEval Framework quick reference + metrics table |
