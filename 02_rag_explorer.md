# 02 — RAG Explorer — Deep Dive

**Subsystem B** is a fully auditable Retrieval-Augmented Generation (RAG) pipeline. Unlike the chatbot, it retrieves relevant knowledge from a vector store at query time. This makes every answer traceable — you can see exactly which chunks were retrieved and why.

---

## 1. What It Does

The RAG Explorer demonstrates the full pipeline from document ingestion through grounded answer generation. Every stage is visible: you can inspect individual chunks, run pure retrieval without LLM generation, and see retrieval hit scores alongside the final answer.

---

## 2. RAG: The Core Idea

```mermaid
flowchart LR
    subgraph "Without RAG"
        Q1["Q: What is your return policy?"]
        LLM1["LLM\n(only training data)"]
        A1["A: 30 days (guessed)"]
    end
    subgraph "With RAG"
        Q2["Q: What is your return policy?"]
        VS["Vector Store\n(your documents)"]
        CTX["Retrieved Context\n'Items can be returned within\n30 days of delivery...'"]
        LLM2["LLM\n(context-grounded)"]
        A2["A: 30 days of delivery\n[return_policy.md]"]
    end

    Q1 --> LLM1 --> A1
    Q2 --> VS --> CTX --> LLM2 --> A2
```

RAG = give the LLM real, current, company-specific knowledge at query time — instead of relying on its training data.

---

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Server | FastAPI | REST API + Jinja2 HTML pages |
| Embeddings | Ollama `nomic-embed-text` | Convert text → dense vectors (768-dim) |
| Vector store | ChromaDB (persistent) | Store and similarity-search embeddings |
| LLM | Groq `llama-3.3-70b-versatile` | Generate grounded answers from context |
| Fallback (embed) | Hash-based deterministic | When Ollama is unavailable |
| Fallback (store) | In-memory search | When ChromaDB fails |
| Fallback (LLM) | Mock reply | When `GROQ_API_KEY` is absent |

---

## 4. Full Pipeline Diagram

```mermaid
flowchart TD
    subgraph "Ingest Path (one-time)"
        DOCS["Source Documents\n.md / .pdf / .txt"]
        LOAD["load_directory()\nor load_any()\ningest.py"]
        CHUNK["chunk_document()\n500 chars, 60-char overlap\nparagraph-aware\ningest.py"]
        EMBED["embed_texts()\nOllama nomic-embed-text\nembed.py"]
        STORE["add_chunks()\nChromaDB upsert\nstore.py"]
    end

    subgraph "Query Path (every chat)"
        QINPUT["User Question"]
        QEMBED["embed_query()\nSame Ollama model\nembed.py"]
        SEARCH["store.search()\nCosine similarity\ntop-k chunks\nstore.py"]
        CONTEXT["Retrieved Context\nchunk texts + sources"]
        PROMPT["Build LLM prompt:\nsystem + context + question\nchat.py"]
        GROQ["Groq API\nllama-3.3-70b-versatile\ntemp=0.2, max_tokens=500"]
        ANSWER["Grounded Answer\n+ source citations [filename.md]"]
    end

    DOCS --> LOAD --> CHUNK --> EMBED --> STORE
    QINPUT --> QEMBED
    QEMBED --> SEARCH
    STORE -->|"vector similarity"| SEARCH
    SEARCH --> CONTEXT
    CONTEXT --> PROMPT
    PROMPT --> GROQ --> ANSWER
```

---

## 5. Module Architecture

```mermaid
graph TD
    APP["app.py\nFastAPI routes\nPage rendering\nAPI endpoints"]
    INGEST["rag/ingest.py\nload_any(path)\nload_directory(dir)\nchunk_document(doc)\nchunk_documents(docs)"]
    EMBED["rag/embed.py\nembed_texts(texts[])\nembed_query(text)\nmodel_info()"]
    STORE["rag/store.py\nVectorStore class\nadd_chunks()\nsearch()\nlist_chunks()\nstats()\nreset()"]
    CHAT["rag/chat.py\nanswer_with_rag(\n  question, store,\n  top_k, history\n)"]
    OLLAMA["Ollama\nnomic-embed-text"]
    CHROMA["ChromaDB\nchroma_db/"]
    GROQ["Groq API"]

    APP --> INGEST
    APP --> EMBED
    APP --> STORE
    APP --> CHAT
    INGEST -->|"Document chunks"| EMBED
    EMBED -->|"HTTP"| OLLAMA
    EMBED -->|"float vectors"| STORE
    STORE -->|"persist"| CHROMA
    CHAT -->|"embed_query"| EMBED
    CHAT -->|"search"| STORE
    CHAT -->|"completions"| GROQ
```

---

## 6. Ingest Stage — Chunking Details

```mermaid
flowchart TD
    DOC["Document\nsource, text, metadata"]
    PARA["Split by\nparagraph breaks\n(blank lines)"]
    SIZE{"Paragraph\n> 500 chars?"}
    SPLIT["Hard split at 500 chars\nwith 60-char overlap"]
    KEEP["Keep as-is"]
    MERGE{"Running chunk\n< 500 chars\n+ next para\nfits?"}
    ADD["Add to running chunk"]
    FLUSH["Flush to chunks list\nstart new chunk"]
    OUT["Chunk objects\n{id, source, index,\ntext, char_start, char_end}"]

    DOC --> PARA
    PARA --> SIZE
    SIZE -->|Yes| SPLIT
    SIZE -->|No| MERGE
    SPLIT --> OUT
    MERGE -->|Yes| ADD --> MERGE
    MERGE -->|No| FLUSH --> MERGE
    FLUSH --> OUT
```

**Parameters:**
- Chunk size: 500 characters
- Overlap: 60 characters (preserves context across boundaries)
- Strategy: paragraph-aware (splits on blank lines first)

---

## 7. Embedding Stage

```mermaid
sequenceDiagram
    participant App as app.py / chat.py
    participant E as embed.py
    participant O as Ollama :11434
    participant FB as Fallback

    App->>E: embed_texts(["chunk1", "chunk2", ...])
    E->>O: POST /api/embeddings\n{model:"nomic-embed-text", prompt:"chunk1"}
    alt Ollama available
        O-->>E: {"embedding": [0.12, -0.34, ...]} (768-dim)
        E-->>App: List[List[float]]
    else Ollama unavailable
        E->>FB: hash_embed(text)
        FB-->>E: deterministic 768-dim vector
        E-->>App: List[List[float]]
    end
```

**`nomic-embed-text` properties:**
- 768-dimensional dense vectors
- Trained for semantic similarity
- English-focused, optimized for retrieval tasks

---

## 8. Vector Store Stage

```mermaid
flowchart LR
    subgraph "VectorStore (store.py)"
        CHROMA_CLIENT["ChromaDB Client\ncollection: 'shopsphere'"]
        ADD["add_chunks(chunks, embeddings)\nupsert by chunk.id"]
        SEARCH["search(query_emb, top_k)\ncosine similarity\nreturns Hit[]"]
        LIST["list_chunks(source=None)\nfilter by source filename"]
        STATS["stats()\ndoc_count, chunk_count"]
        RESET["reset()\ndelete collection + recreate"]
    end
    subgraph "Fallback"
        MEM["In-memory list\nmanual cosine sim\nif ChromaDB fails"]
    end

    CHROMA_CLIENT --> ADD
    CHROMA_CLIENT --> SEARCH
    CHROMA_CLIENT --> LIST
    CHROMA_CLIENT --> STATS
    CHROMA_CLIENT --> RESET
    SEARCH -.->|fallback| MEM
```

**ChromaDB persistence:** `chroma_db/` directory (configurable via `CHROMA_DIR` env var). Survives server restarts — you only need to ingest once.

---

## 9. Retrieval Stage — Similarity Search

```mermaid
sequenceDiagram
    participant Q as User Query
    participant E as embed_query()
    participant S as VectorStore.search()
    participant C as ChromaDB

    Q->>E: "What is your refund policy?"
    E->>E: Embed query → 768-dim vector
    E->>S: search(query_emb, top_k=4)
    S->>C: collection.query(\n  query_embeddings=[vec],\n  n_results=4\n)
    C-->>S: ids[], documents[], distances[], metadatas[]
    S->>S: Build Hit objects\n(id, source, text, score=1-distance)
    S-->>Q: [Hit(source="refund_policy.md", score=0.91, text="..."),\n Hit(source="faq.md", score=0.74, text="..."), ...]
```

**Score formula:** `score = 1 - cosine_distance`. Ranges 0–1, higher = more similar.

---

## 10. Answer Generation Stage

```mermaid
flowchart TD
    HITS["Retrieved Hits\n[Hit(source, text), ...]"]
    CTX["Build context block:\n[refund_policy.md #0]\n'Refunds are processed...\n\n[faq.md #3]\n'You can request a refund...'"]
    SYS["System prompt:\n'Answer ONLY from context\nCite sources [filename.md]\nUnder 150 words'"]
    MSG["Build messages:\n[system]\n[...history]\n[user: question + context]"]
    GROQ["Groq API\ntemp=0.2, max_tokens=500"]
    ANS["Answer:\n'Refunds are processed within 7 business\ndays [refund_policy.md]. Digital goods\nare non-refundable once downloaded.'"]

    HITS --> CTX
    SYS --> MSG
    CTX --> MSG
    MSG --> GROQ --> ANS
```

The LLM is instructed to:
1. Answer **only** from retrieved context
2. Cite sources inline: `[filename.md]`
3. Stay under 150 words
4. Say "I don't have that information" if context doesn't cover the question

---

## 11. Data Models

```mermaid
classDiagram
    class Document {
        +str source
        +str text
        +dict metadata
    }
    class Chunk {
        +str id
        +str source
        +int index
        +str text
        +int char_start
        +int char_end
    }
    class Hit {
        +str id
        +str source
        +str text
        +float score
        +dict metadata
    }
    class RagAnswer {
        +str answer
        +list~str~ sources
        +list~str~ retrieval_context
        +list~Hit~ hits
        +str mode
        +str model
    }
    class SearchRequest {
        +str query
        +int top_k
    }
    class ChatRequest {
        +str message
        +int top_k
        +list~dict~ history
    }

    Document "1" --> "1..*" Chunk : chunked into
    Chunk --> Hit : retrieved as
    Hit "1..*" --> "1" RagAnswer : aggregated into
    SearchRequest --> Hit : returns
    ChatRequest --> RagAnswer : returns
```

---

## 12. UI Pages

```mermaid
stateDiagram-v2
    [*] --> Home: GET /
    Home --> Ingest: click Ingest
    Home --> Search: click Search
    Home --> Chat: click Chat
    Ingest --> Ingest: seed corpus / upload file
    Search --> Search: submit query
    Chat --> Chat: send message
```

| Page | Path | What you see |
|------|------|-------------|
| **Pipeline Dashboard** | `/` | Stage diagram, store stats (chunk count, doc count, embed model status, Groq status) |
| **Ingest** | `/ingest` | Available corpus files, upload form, full chunk list with source and char positions |
| **Search** | `/search` | Query box, ranked hits with similarity scores — **no LLM involved** |
| **Chat** | `/chat` | Chat interface + collapsible retrieval panel showing the top-k chunks that informed the answer |

---

## 13. API Endpoints — Full Reference

### `GET /api/health`
```json
{
  "status": "ok",
  "stats": {"doc_count": 5, "chunk_count": 47},
  "embed": {"model": "nomic-embed-text", "available": true},
  "groq_configured": true
}
```

### `POST /api/ingest/seed?reset=false`
Seeds the bundled 5-document corpus. Pass `reset=true` to wipe the store first.
```json
{"added": 47, "documents": 5, "stats": {...}}
```

### `POST /api/ingest/upload`
Multipart form: `file` (PDF/MD/TXT) + `reset` (bool).
```json
{
  "added": 12,
  "source": "my_policy.md",
  "chunk_count": 12,
  "preview": ["First 160 chars of chunk 0...", "..."],
  "stats": {...}
}
```

### `POST /api/ingest/reset`
Wipes the entire vector store.
```json
{"status": "reset", "stats": {"doc_count": 0, "chunk_count": 0}}
```

### `POST /api/search`
```json
// Request
{"query": "How long does a refund take?", "top_k": 4}

// Response
{
  "query": "How long does a refund take?",
  "hits": [
    {"id": "refund_policy.md#0", "source": "refund_policy.md", "score": 0.9123,
     "text": "Refunds are processed within 7 business days...", "metadata": {...}},
    ...
  ]
}
```

### `POST /api/chat`
```json
// Request
{"message": "How long does a refund take?", "top_k": 4, "history": []}

// Response
{
  "answer": "Refunds are processed within 7 business days [refund_policy.md].",
  "sources": ["refund_policy.md"],
  "retrieval_context": ["Refunds are processed within 7 business days...", "..."],
  "hits": [{"id": "...", "source": "refund_policy.md", "score": 0.91, "text": "..."}],
  "mode": "live",
  "model": "llama-3.3-70b-versatile"
}
```

---

## 14. Bundled Corpus — Knowledge Base

```mermaid
mindmap
    root((data/ecommerce/))
        refund_policy.md
            7 business days processing
            Original payment method
            Original shipping non-refundable
            Digital goods non-refundable
        return_policy.md
            30-day return window
            Original condition required
            Non-returnable items
            Free return shipping for defects
        shipping_policy.md
            Standard free over $50
            5-7 business days US
            Express $9.99 / 2-3 days
            International 10-14 days
            Customs buyer responsibility
        product_catalog.md
            SP-EARBUDS-01 Wireless Earbuds $79
            SP-HOODIE-CL Classic Hoodie $49
            SP-MUG-CER Ceramic Mug $14
            SP-LAMP-LED LED Desk Lamp $39
        faq.md
            Payment methods
            Account deletion
            ShopSphere Plus
```

---

## 15. Graceful Degradation Chain

```mermaid
flowchart TD
    OLL{"Ollama\navailable?"}
    REAL_EMB["Real embeddings\nnomic-embed-text\n768-dim semantic vectors"]
    FAKE_EMB["Hash-based embeddings\ndeterministic but non-semantic\nretrieval quality degraded"]

    CHROMA{"ChromaDB\nfunctional?"}
    REAL_STORE["ChromaDB persistent store\nfull cosine similarity"]
    MEM_STORE["In-memory list\nmanual cosine sim\nno persistence"]

    GROQ{"GROQ_API_KEY\nset?"}
    REAL_ANS["Groq LLM answer\ngrounded in context"]
    MOCK_ANS["Mock reply listing\nretrieved chunk IDs"]

    OLL -->|Yes| REAL_EMB
    OLL -->|No| FAKE_EMB
    REAL_EMB --> CHROMA
    FAKE_EMB --> CHROMA
    CHROMA -->|Yes| REAL_STORE
    CHROMA -->|No| MEM_STORE
    REAL_STORE --> GROQ
    MEM_STORE --> GROQ
    GROQ -->|Yes| REAL_ANS
    GROQ -->|No| MOCK_ANS
```

---

## 16. RAG Goldens (for DeepEval)

The evaluation framework uses 8 golden cases with expected context keywords and expected source files:

| Question | Expected Sources |
|----------|-----------------|
| "What is the refund processing time?" | `refund_policy.md` |
| "How long does standard shipping take inside the US?" | `shipping_policy.md` |
| "What items cannot be returned?" | `return_policy.md` |
| "Tell me about the SP-EARBUDS-01 earbuds." | `product_catalog.md` |
| "How much does express shipping cost?" | `shipping_policy.md` |
| "Are digital goods refundable?" | `refund_policy.md` |
| "What is ShopSphere Plus?" | `faq.md` |
| "Who pays for return shipping on defective items?" | `return_policy.md` |

---

## 17. Models Used

| Role | Model | Provider | File | Env Override |
|------|-------|----------|------|-------------|
| Text embedding | `nomic-embed-text` | Ollama | `rag/embed.py:13` | `EMBED_MODEL` |
| Answer generation (Groq) | `llama-3.3-70b-versatile` | Groq Cloud | `rag/chat.py:26` | `RAG_MODEL` |
| Answer generation (local) | `llama3.2:3b` | Ollama | `rag/chat.py:24` | `RAG_MODEL` |

```mermaid
flowchart LR
    subgraph Embedding
        T[Text] --> OLL_EMB["nomic-embed-text\nOllama :11434\nENV: EMBED_MODEL\nOLLAMA_HOST"]
        OLL_EMB -->|Ollama down| FB["blake2b hash fallback\n64-dim deterministic vector"]
    end
    subgraph Generation
        CTX[Context + Question] --> PROV{LLM_PROVIDER?}
        PROV -->|groq + key| GROQ["llama-3.3-70b-versatile\nGroq Cloud\ntemp=0.2, max_tokens=500\nENV: RAG_MODEL"]
        PROV -->|ollama| OLL_GEN["llama3.2:3b\nOllama local\ntemp=0.2, max_tokens=500\nENV: RAG_MODEL"]
        PROV -->|no key| MOCK["Mock reply\nlists chunk IDs"]
    end
```

**Key differences from the chatbot's LLM settings:**

| Setting | Chatbot | RAG |
|---------|---------|-----|
| `temperature` | `0.3` | `0.2` — stricter grounding |
| `max_tokens` | `400` | `500` — longer context-grounded answers |
| Knowledge source | Hardcoded system prompt | Retrieved chunks at query time |

---

## 18. Environment Variables

| Variable | Default | Effect |
|----------|---------|--------|
| `GROQ_API_KEY` | — | Required for live answers; unset = mock mode |
| `RAG_MODEL` | `llama-3.3-70b-versatile` | Override Groq model for answer generation |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `CHROMA_DIR` | `chroma_db/` | ChromaDB persistence directory |

---

## 18. Run Commands

```bash
# Start server
cd 02_rag_explorer
uvicorn app:app --reload --port 8202 --loop asyncio

# Seed the corpus via curl
curl -X POST "http://localhost:8202/api/ingest/seed?reset=true"

# Run a search
curl -X POST http://localhost:8202/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "refund policy", "top_k": 3}'

# Full RAG chat
curl -X POST http://localhost:8202/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How long do refunds take?", "top_k": 4}'
```
