# Test Cases Logic — DeepEval Framework

All 20 test files follow the same core loop:
**Question in → Target app answers → Judge LLM scores → Metric passes or fails.**

---

## 1. Big Picture — How Every Test Runs

```mermaid
flowchart TD
    PY["pytest"]

    PY --> T0["test_00  Smoke"]
    PY --> TC["Chatbot Tests\ntest_01 to test_07\ntest_18"]
    PY --> TR["RAG Tests\ntest_08 to test_16\ntest_19"]
    PY --> TI["Independent Tests\ntest_17  Summarization"]

    T0 --> HLT["Health checks\nChatbot alive?\nRAG alive?\nJudge alive?"]

    TC --> CB["Chatbot\nlocalhost:8201"]
    TR --> RG["RAG Explorer\nlocalhost:8202"]
    TI --> GR["Groq LLM\nor static fallback"]

    CB --> JG["Judge LLM\nGroq / OpenAI / Ollama"]
    RG --> JG
    GR --> JG

    JG --> SC["Score 0.0 to 1.0"]
    SC --> PF{"Pass or Fail?"}
    PF -->|pass| RPT["HTML Report"]
    PF -->|fail| RPT
```

---

## 2. Input Sources — Where the Questions Come From

```mermaid
flowchart LR
    subgraph SRC ["Input Sources"]
        CG["Chatbot Goldens\n8 real customer questions\npolicy, product, shipping"]
        RG["RAG Goldens\n8 real customer questions\nrefund, shipping, product"]
        SP["Safety Prompts\n5 adversarial questions\nbias and toxicity traps"]
        PP["PII Probes\n4 prompt-injection attempts\ntrying to extract system prompt"]
        CV["Conversations\n2 multi-turn chats\n3 turns each"]
        ST["Summary Source\n1 fixed refund-policy text"]
    end

    CG --> T01["test_01 test_02 test_03\ntest_06"]
    SP --> T04["test_04 test_05\ntest_16"]
    PP --> T07["test_07"]
    RG --> T08["test_08 to test_15\ntest_19"]
    CV --> T18["test_18"]
    ST --> T17["test_17"]
```

---

## 3. Chatbot Tests — test_01 to test_07, test_18

```mermaid
flowchart LR
    Q["Golden Question\nor adversarial prompt"]

    Q --> CB["Chatbot\n:8201\nPOST /chat"]
    CB --> ANS["Answer text"]

    ANS --> M1["test_01\nAnswer Relevancy\nthreshold 0.7\nIs reply on-topic?"]
    ANS --> M2["test_02\nFaithfulness\nthreshold 0.7\nEvery claim backed\nby context?"]
    ANS --> M3["test_03\nHallucination\nthreshold 0.4 max\nAny contradictions?"]
    ANS --> M4["test_04\nBias\nthreshold 0.4 max\nBiased statements?"]
    ANS --> M5["test_05\nToxicity\nthreshold 0.3 max\nHarmful language?"]
    ANS --> M6["test_06\nG-Eval Completeness\nthreshold 0.6\nAll key facts present?"]
    ANS --> M7["test_07\nG-Eval No Prompt Leak\nthreshold 0.7\nRefuses to reveal\nsystem prompt?"]
    ANS --> M8["test_18\nConversation Completeness\nthreshold 0.5\nUser intent met\nacross turns?"]

    M1 --> PF["Pass or Fail"]
    M2 --> PF
    M3 --> PF
    M4 --> PF
    M5 --> PF
    M6 --> PF
    M7 --> PF
    M8 --> PF
```

---

## 4. RAG Tests — test_08 to test_16, test_19

```mermaid
flowchart LR
    Q["RAG Golden Question"]

    Q --> RG["RAG Explorer\n:8202\nPOST /chat"]
    RG --> ANS["Answer text\nplus retrieved chunks\nplus source filenames"]

    ANS --> M8["test_08\nContextual Precision\nthreshold 0.6\nRelevant chunks\nranked higher?"]
    ANS --> M9["test_09\nContextual Recall\nthreshold 0.6\nAll needed facts\nretrieved?"]
    ANS --> M10["test_10\nContextual Relevancy\nthreshold 0.6\nChunks on-topic?"]
    ANS --> M11["test_11\nFaithfulness\nthreshold 0.7\nEvery claim in\nretrieved chunks?"]
    ANS --> M12["test_12\nAnswer Relevancy\nthreshold 0.7\nReply on-topic?"]
    ANS --> M13["test_13\nHallucination\nthreshold 0.4 max\nContradicts\nground truth?"]
    ANS --> M14["test_14\nG-Eval Correctness\nthreshold 0.6\nFacts match\nexpected output?"]
    ANS --> M15["test_15\nG-Eval Citation Quality\nthreshold 0.5\nSource filename\ncited correctly?"]
    ANS --> M16["test_16\nBias and Toxicity\n0.4 max / 0.3 max\nSafe replies\nto adversarial?"]
    ANS --> M19["test_19\nG-Eval Helpfulness\nthreshold 0.6\nSpecific and\nactionable reply?"]

    M8 --> PF["Pass or Fail"]
    M9 --> PF
    M10 --> PF
    M11 --> PF
    M12 --> PF
    M13 --> PF
    M14 --> PF
    M15 --> PF
    M16 --> PF
    M19 --> PF
```

---

## 5. Independent Tests — test_00 and test_17

```mermaid
flowchart TD
    subgraph Smoke ["test_00 — Smoke Tests"]
        S1["Is Judge LLM responding?"]
        S2["Is Chatbot :8201 alive?"]
        S3["Is RAG :8202 alive?"]
        S4["Does RAG have chunks loaded?"]
        S1 --> OK1["assert response received"]
        S2 --> OK2["assert status == ok"]
        S3 --> OK3["assert status == ok"]
        S4 --> OK4["assert chunks > 0"]
    end

    subgraph Summary ["test_17 — Summarization"]
        SRC["Fixed refund policy text\n115 words"]
        SRC --> GR["Groq LLM\ngenerates summary"]
        GR --> SM["SummarizationMetric\nthreshold 0.5\nKey facts preserved?"]
        SM --> PF["Pass or Fail"]
    end
```

---

## 6. How the Score Becomes Pass or Fail

```mermaid
flowchart LR
    SC["Score from Judge LLM\n0.0 to 1.0"]

    SC --> HB{"higher is better?"}

    HB -->|yes - quality metrics| CMP1["score >= threshold\nex: 0.82 >= 0.70\nPASS"]
    HB -->|no - safety metrics| CMP2["score <= threshold\nex: 0.15 <= 0.40\nPASS"]

    CMP1 --> RPT["HTML Report\nreports/report.html"]
    CMP2 --> RPT
```

---

## 7. All 20 Tests at a Glance

| # | File | Target | Input | Metric | Threshold | Direction |
|---|------|--------|-------|--------|-----------|-----------|
| 00 | test_00 | both | — | Smoke / health | — | — |
| 01 | test_01 | Chatbot | Golden Q&A | Answer Relevancy | 0.70 | higher |
| 02 | test_02 | Chatbot | Golden Q&A | Faithfulness | 0.70 | higher |
| 03 | test_03 | Chatbot | Golden Q&A | Hallucination | 0.40 | lower |
| 04 | test_04 | Chatbot | Safety prompts | Bias | 0.40 | lower |
| 05 | test_05 | Chatbot | Safety prompts | Toxicity | 0.30 | lower |
| 06 | test_06 | Chatbot | Golden Q&A | G-Eval Completeness | 0.60 | higher |
| 07 | test_07 | Chatbot | PII probes | G-Eval No Prompt Leak | 0.70 | higher |
| 08 | test_08 | RAG | Golden Q&A | Contextual Precision | 0.60 | higher |
| 09 | test_09 | RAG | Golden Q&A | Contextual Recall | 0.60 | higher |
| 10 | test_10 | RAG | Golden Q&A | Contextual Relevancy | 0.60 | higher |
| 11 | test_11 | RAG | Golden Q&A | Faithfulness | 0.70 | higher |
| 12 | test_12 | RAG | Golden Q&A | Answer Relevancy | 0.70 | higher |
| 13 | test_13 | RAG | Golden Q&A | Hallucination | 0.40 | lower |
| 14 | test_14 | RAG | Golden Q&A | G-Eval Correctness | 0.60 | higher |
| 15 | test_15 | RAG | Golden Q&A | G-Eval Citation Quality | 0.50 | higher |
| 16 | test_16 | RAG | Safety prompts | Bias + Toxicity | 0.40 / 0.30 | lower |
| 17 | test_17 | Synthetic | Summary text | Summarization | 0.50 | higher |
| 18 | test_18 | Chatbot | Conversations | Conversation Completeness | 0.50 | higher |
| 19 | test_19 | RAG | Golden Q&A | G-Eval Helpfulness | 0.60 | higher |
