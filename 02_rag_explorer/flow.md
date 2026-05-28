# RAG Explorer Flow

This file explains the Rag Explorer pipeline in a simple way using a Mermaid diagram.

## Mermaid Diagram

```mermaid
flowchart LR
    A[User enters a question] --> B[Search page or Chat page]
    B --> C[Embed the question\n(using Ollama / nomic-embed-text)]
    C --> D[Search vector store\nfor similar chunks]
    D --> E[Retrieve top matching chunks]
    E --> F[Build answer using retrieved context]
    F --> G[Show result to the user]

    H[Ingest page] --> I[Load PDF / TXT / MD files]
    I --> J[Split into chunks]
    J --> K[Generate embeddings]
    K --> L[Store chunks + embeddings\nin vector store]
    L --> D
```

## Simple Explanation

1. User asks a question.
2. The question is converted into embeddings (numbers that represent meaning).
3. The app searches the stored chunks for the most similar ones.
4. The best matching chunks are collected.
5. These chunks are used to build a grounded answer.
6. The answer is shown to the user.

## How data gets into the system

- First, documents are uploaded or seeded from the Ingest page.
- The files are split into smaller chunks.
- Each chunk gets an embedding.
- The chunks and embeddings are saved in the vector store.

## Why this is useful

- The answer is based on the stored documents, not on random guessing.
- You can inspect the retrieved chunks and understand why the answer was generated.
- This makes the RAG flow easy to test and evaluate.
