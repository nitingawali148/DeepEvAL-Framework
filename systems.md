# What Did We Build? — Plain English Guide

Think of this project as a **science fair experiment for AI**.
We built two AI customer-support assistants for an imaginary online shop,
then built a grading machine that gives both assistants report cards.

---

## The Big Picture (3 Systems)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│   System A            System B              System C             │
│  (Chatbot)         (Smart Search)           (Grader)             │
│                                                                   │
│  Answers from       Looks up docs         Scores both            │
│  memory only    →   then answers     →    on 22 tests            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## System A — The Chatbot  `01_chatbot/`

### What is it?
A customer-support chat window for an online shop called **ShopSphere**.
You type a question, it types back an answer.

### How does it work?
Think of a new employee who memorised the entire company manual before starting work.
They know the return policy, shipping policy, refund rules — all from memory.
If you ask something not in the manual, they might **make up an answer** (this is called *hallucination*).

```
You type:  "How do I return a broken item?"
     ↓
The chatbot reads its memory (built-in manual)
     ↓
Calls a cloud AI model (Groq / Ollama) to write a nice reply
     ↓
You see:   "You can return broken items within 30 days..."
```

### Where does it run?
- Chat window (the website): `http://localhost:5173`
- Behind-the-scenes engine: `http://localhost:8201`

### Key files
| File | What it does |
|------|-------------|
| [01_chatbot/backend/app.py](01_chatbot/backend/app.py) | The engine that receives questions and sends answers |
| [01_chatbot/frontend/src/App.jsx](01_chatbot/frontend/src/App.jsx) | The chat window you see in the browser |

---

## System B — The RAG Explorer  `02_rag_explorer/`

### What is it?
Another customer-support assistant — but smarter.
Instead of relying on memory, it **searches documents first**, then answers.

### What does RAG mean?
**R**etrieve → **A**ugment → **G**enerate

- **Retrieve** = search the document library for relevant pieces
- **Augment** = hand those pieces to the AI as reading material
- **Generate** = the AI writes an answer based only on what it just read

### A simple analogy
Instead of a new employee memorising the manual, imagine a librarian.
When you ask a question, the librarian:
1. Walks to the shelf and finds the 3–4 most relevant paragraphs
2. Reads those paragraphs
3. Then answers your question based on what they just read

This makes the answer much more accurate and traceable — you can see exactly which document it came from.

### How the documents are prepared (one-time setup)
```
5 document files (.md)
    ↓  Cut into small pieces (~500 characters each)
21 chunks (small text pieces)
    ↓  Each chunk is turned into a list of 768 numbers
       (this is called an "embedding" — a mathematical fingerprint)
21 fingerprints stored in a database (ChromaDB)
```

### How a question is answered
```
You type:  "What is the refund policy?"
     ↓
Your question is also turned into a fingerprint (768 numbers)
     ↓
The database finds the 4 most similar fingerprints
     ↓
Those 4 chunks of text are handed to the AI as reading material
     ↓
The AI writes an answer based only on those 4 chunks
     ↓
You see the answer + which document each piece came from
```

### Where does it run?
- Full app with 4 pages: `http://localhost:8202`

### The 5 documents in the library
| Document | What it covers |
|----------|---------------|
| faq.md | Common customer questions |
| product_catalog.md | Products sold in the shop |
| refund_policy.md | How refunds work |
| return_policy.md | How returns work |
| shipping_policy.md | Delivery times and costs |

### Key files
| File | What it does |
|------|-------------|
| [02_rag_explorer/app.py](02_rag_explorer/app.py) | The main server — handles all web pages and API calls |
| [02_rag_explorer/rag/ingest.py](02_rag_explorer/rag/ingest.py) | Reads documents and cuts them into chunks |
| [02_rag_explorer/rag/embed.py](02_rag_explorer/rag/embed.py) | Converts text into number fingerprints |
| [02_rag_explorer/rag/store.py](02_rag_explorer/rag/store.py) | Saves and searches the fingerprint database |
| [02_rag_explorer/rag/chat.py](02_rag_explorer/rag/chat.py) | Puts it all together: search → read → answer |

---

## System C — The Grader (DeepEval Framework)  `03_deepeval_framework/`

### What is it?
An automated testing machine that runs both chatbots through **22 different tests**
and gives each answer a score between 0 and 1.

### Why do we need it?
You can not just read every AI answer manually — it would take hours.
This system uses a **third AI (the judge)** to check the answers of the first two AIs.
The judge scores each answer on things like: Was it honest? Was it helpful? Was it safe?

### A simple analogy
Imagine a teacher (the judge) checking homework (the chatbot answers).
The teacher reads each answer and gives it marks:
- Did the student answer the actual question? *(Answer Relevancy)*
- Did the student make up facts? *(Hallucination)*
- Was the answer rude or biased? *(Toxicity / Bias)*
- Did the student correctly cite their sources? *(Faithfulness)*

### The 22 tests at a glance

**For the Chatbot (System A) — 10 tests:**
| Test | What it checks |
|------|---------------|
| Answer Relevancy | Did it actually answer the question? |
| Faithfulness | Did it stick to known facts? |
| Hallucination | Did it make things up? |
| Bias | Did it treat all customers fairly? |
| Toxicity | Was the language rude or harmful? |
| PII Leakage | Did it accidentally share private data? |
| Prompt Leak | Did it reveal its hidden instructions? |
| Completeness | Did it cover everything needed? |
| Conversation Completeness | Did it handle the whole conversation well? |
| Knowledge Retention | Did it remember earlier parts of the chat? |

**For the RAG Explorer (System B) — 11 tests:**
| Test | What it checks |
|------|---------------|
| Contextual Precision | Did it retrieve the right documents? |
| Contextual Recall | Did it retrieve all the needed documents? |
| Contextual Relevancy | Were the retrieved pieces actually useful? |
| Answer Relevancy | Did it actually answer the question? |
| Faithfulness | Did it base the answer on the retrieved text? |
| Hallucination | Did it add information not in the documents? |
| Correctness | Was the answer factually right? |
| Citation Quality | Did it correctly credit its sources? |
| Helpfulness | Was the answer genuinely useful? |
| Bias | Did it treat all topics fairly? |
| Toxicity | Was the language safe and respectful? |

**Bonus (1 test):**
| Test | What it checks |
|------|---------------|
| Summarization | Can it summarise a document accurately? |

### How one test run works
```
The Grader picks a test question  (e.g., "What is the return policy?")
     ↓
Sends the question to System A or B
     ↓
Gets back the answer
     ↓
Gives the answer + the question to the judge AI
     ↓
Judge AI reads and scores it (0.0 to 1.0)
     ↓
Score appears on the dashboard  (green = pass, red = fail)
```

### Two ways to run tests
**Option 1 — Dashboard (click buttons)**
Open `http://localhost:8203` → click any metric card → see the score live

**Option 2 — Batch (run all at once)**
Run `python run_all.py` → wait → get a full HTML report with every test result

### Where does it run?
- Live dashboard: `http://localhost:8203`
- Batch report: `reports/report.html` (generated after running)

### Key files
| File | What it does |
|------|-------------|
| [03_deepeval_framework/dashboard/app.py](03_deepeval_framework/dashboard/app.py) | The dashboard website |
| [03_deepeval_framework/dashboard/registry.py](03_deepeval_framework/dashboard/registry.py) | The list of all 22 tests and their settings |
| [03_deepeval_framework/dashboard/runner.py](03_deepeval_framework/dashboard/runner.py) | Runs one test end-to-end |
| [03_deepeval_framework/datasets/chatbot_goldens.py](03_deepeval_framework/datasets/chatbot_goldens.py) | The 8 example questions for the chatbot |
| [03_deepeval_framework/datasets/rag_goldens.py](03_deepeval_framework/datasets/rag_goldens.py) | The 8 example questions for the RAG explorer |
| [03_deepeval_framework/llm_providers/factory.py](03_deepeval_framework/llm_providers/factory.py) | Picks which AI to use as the judge |

---

## How All Three Systems Talk to Each Other

```
                 ┌─────────────────┐
                 │   You (User)    │
                 └────────┬────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
  ┌──────────────┐ ┌─────────────┐ ┌───────────────┐
  │  System A    │ │  System B   │ │   System C    │
  │  Chatbot     │ │  RAG Search │ │   Grader      │
  │  :8201/:5173 │ │  :8202      │ │   :8203       │
  └──────┬───────┘ └──────┬──────┘ └───────┬───────┘
         │                │                │
         │                │     calls      │
         │                └────────────────┤
         └─────────────────────────────────┤
                                           │
                                           ▼
                                   ┌──────────────┐
                                   │  Judge AI    │
                                   │ (Groq/Ollama)│
                                   │  Scores 0–1  │
                                   └──────────────┘
```

The Grader (System C) is the glue — it calls System A and System B,
collects their answers, and sends them to the judge for scoring.

---

## Quick Reference — Ports & URLs

| System | What it is | URL |
|--------|-----------|-----|
| System A — Chat UI | Browser chat window | http://localhost:5173 |
| System A — API | Engine behind the chat | http://localhost:8201 |
| System B — RAG App | Full RAG explorer | http://localhost:8202 |
| System C — Dashboard | Eval score dashboard | http://localhost:8203 |

---

## The Simplest Possible Summary

> We built **two AI assistants** (one works from memory, one searches documents)
> and a **grading machine** that automatically checks both assistants across
> 22 quality, safety, and accuracy tests — and shows the results on a dashboard.
