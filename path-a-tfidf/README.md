[![JavaScript](https://img.shields.io/badge/JavaScript-ES2022-F7DF1E?logo=javascript&logoColor=000)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Node.js](https://img.shields.io/badge/Node.js-%E2%89%A5%2020-339933?logo=node.js&logoColor=fff)](https://nodejs.org/)
[![Foundry Local](https://img.shields.io/badge/Foundry%20Local-On--Device%20AI-0078D4?logo=microsoft&logoColor=fff)](https://foundrylocal.ai)
[![Phi-3.5 Mini](https://img.shields.io/badge/Model-Phi--3.5%20Mini%20Instruct-6B21A8)](https://huggingface.co/microsoft/Phi-3.5-mini-instruct)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Offline](https://img.shields.io/badge/Connectivity-100%25%20Offline-brightgreen)]()

# Path A — TF-IDF Retrieval

The first of the three architectures in this repository. A complete offline RAG
assistant that **uses no embedding model at all**: retrieval is TF-IDF scoring with
cosine similarity, computed in plain JavaScript over vectors kept in SQLite.

Its purpose in the project is to get a full RAG pipeline running in minutes, with a
retrieval step you can read as ordinary numbers — and then to fail in a specific,
measurable way that motivates Path B. See [`../RESULTS.md`](../RESULTS.md) for those
measurements and [`../README.md`](../README.md) for how the three paths compare.

> **Adapted from [`leestott/local-rag`](https://github.com/leestott/local-rag)**, the
> sample accompanying Microsoft's [Tech Community blog post](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/building-your-first-local-rag-application-with-foundry-local/4501968).
> The upstream sample is a gas field support agent over its own 20 documents. This copy
> retargets it at the shared corpus, rewrites the system prompts, and upgrades the SDK.
> See [What changed from upstream](#what-changed-from-upstream). Its MIT license is kept
> verbatim in [`LICENSE`](LICENSE).

## Quick Start

Foundry Local must be installed and its service running (`foundry server start`) —
see the [root README](../README.md#prerequisites).

```bash
cd path-a-tfidf
npm install
npm run ingest              # index ../knowledge-base into data/rag.db
npm start                   # http://127.0.0.1:3000
```

Two things worth running before the server, because neither loads the chat model and
both finish in milliseconds:

```bash
node retrieval_check.js     # retrieval quality against a fixed question set
npm test                    # 51 unit tests, Node's built-in runner
```

`retrieval_check.js` shares its question set with `path-c-sqlite/retrieval_check.py` on
purpose. Running both and reading the outputs side by side is the most useful thing in
this repository for seeing why retrieval strategy matters.

### What happens at startup

1. `npm run ingest` reads every `.md` file in [`../knowledge-base/`](../knowledge-base/),
   parses optional YAML front matter, splits each document into overlapping chunks,
   computes TF-IDF vectors, and writes all of it to `data/rag.db`. **27 chunks from 14
   documents**, effectively instantly — there is no embedding model to run.
2. `npm start` loads `phi-3.5-mini` through the Foundry Local SDK, opens the vector
   store, and starts Express on `127.0.0.1:3000`. The server listens immediately and
   streams model-loading status to the UI over SSE, so the page is usable while the
   model is still downloading on first run.

## Architecture

```
browser (public/index.html)
   │  POST /api/chat/stream
   ▼
Express (src/server.js)
   │
   ├─► VectorStore (src/vectorStore.js) ──► data/rag.db   TF-IDF + cosine, top-K
   │
   └─► ChatEngine (src/chatEngine.js) ────► Foundry Local ──► phi-3.5-mini
                                                                │
   ◄──────────────────── SSE token stream ──────────────────────┘
```

A query flows: the browser posts the question → the server vectorises it with the same
TF-IDF routine used at ingest → the vector store cosine-ranks every stored chunk and
returns the top-K → those chunks are injected into the prompt as context → Foundry Local
generates a grounded answer → tokens stream back over SSE.

Everything is on one machine. No cloud, no API keys, no outbound calls at inference time.

## The Pipeline

### 1. Ingestion — [`src/ingest.js`](src/ingest.js)

Reads the shared corpus, strips YAML front matter (`title`, `category`, `id`) into
metadata, chunks the body, and stores each chunk with its TF-IDF vector in SQLite.

### 2. Vector store — [`src/vectorStore.js`](src/vectorStore.js)

SQLite via `better-sqlite3`. Chunks are stored alongside their TF-IDF vectors; at query
time it cosine-ranks them against the query vector and returns the top-K. An in-memory
inverted index filters candidates first, and parsed vectors are cached after first
access, so repeated queries do not re-parse JSON.

### 3. Chat engine — [`src/chatEngine.js`](src/chatEngine.js)

Orchestrates the RAG flow: vectorise the question, retrieve the top-K chunks, assemble
system prompt + retrieved context + question, call the model through the SDK's native
chat client, and stream the response back chunk by chunk.

### 4. Prompts — [`src/prompts.js`](src/prompts.js)

Two variants, both written for this project (they are not the upstream prompts):

- **Full** (~300 tokens) — a teaching assistant for the summer school, instructed to
  name its source document, to keep the TF-IDF and embedding paths distinct, and to
  answer `"This information is not available in the local knowledge base."` when the
  retrieved context does not cover the question.
- **Compact** (~80 tokens) — the same rules, minimised for constrained devices.

That refusal instruction carries unusual weight here. Path A's retrieval **cannot** tell
an answerable question from an unanswerable one — it scored an out-of-scope question
0.520 against a best in-scope score of 0.300 — so the system prompt is doing that work
unaided. [`../RESULTS.md`](../RESULTS.md) covers this; it is the strongest argument in
the curriculum for moving to embeddings.

## Chunking Strategy

Chunking directly affects retrieval accuracy, answer quality, and performance. This path
uses a **fixed-size sliding window with overlap**, deliberately.

### How it works

Chunks of **~200 whitespace-delimited tokens** with **25 tokens of overlap**, configured
in [`src/config.js`](src/config.js) and implemented in [`src/chunker.js`](src/chunker.js):

1. YAML front matter is stripped and stored as metadata.
2. The body is tokenised on whitespace.
3. A sliding window walks the tokens, emitting one chunk per step.
4. Each window starts 25 tokens before the previous one ended, creating the overlap.
5. Documents shorter than one window stay as a single chunk.

### Why fixed-size

| Constraint | How fixed-size chunking helps |
|---|---|
| **Small local model** | 200-token chunks keep context compact, leaving room for the system prompt and the generated answer |
| **CPU/NPU execution** | Chunking is string operations only — no tokeniser library, no embedding runtime. The whole compute budget stays with the LLM |
| **Zero dependencies** | No vector database, no second model |
| **Predictable memory** | Uniform chunk sizes make retrieval cost and context usage consistent |

### Why not the alternatives

| Alternative | Trade-off |
|---|---|
| **Sentence-based** | Chunk sizes vary unpredictably |
| **Section-aware** (split on `##`) | Section lengths vary widely across the corpus: some too small to be worth a retrieval slot, others too large for the context window |
| **Recursive** (LangChain-style) | Better boundaries, but adds complexity and dependencies for marginal gain on short documents |
| **Semantic** (embedding-based) | Best retrieval quality — and it needs an embedding model, which is exactly what Path A exists to do without. That is [Path C](../path-c-sqlite/) |

### What it buys

Retrieval runs in **under 1–3 ms** (measured, see [`../RESULTS.md`](../RESULTS.md))
against 600–770 ms for the embedding paths, and ingestion is instant because nothing has
to be encoded. Only one model sits in memory.

None of that turns out to matter much. Generation dominates: ~60 s per answer with
`phi-3.5-mini` at a 1024-token budget on the measurement hardware, against 4.2–7.1 s for
`qwen2.5-0.5b` in Path C. **Model choice, not retrieval strategy, sets the response
time.** Retrieval strategy sets whether the answer is right.

### When to switch

- **Hundreds of long documents** → recursive or section-aware chunking.
- **Embedding-based retrieval** → semantic chunking becomes worthwhile.
- **Mixed content** (tables, code, prose) → format-aware chunking, to keep logical units intact.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Non-streaming chat completion |
| `POST` | `/api/chat/stream` | Streaming chat via SSE |
| `POST` | `/api/upload` | Add a document to the knowledge base |
| `GET` | `/api/docs` | List indexed documents |
| `GET` | `/api/status` | Model initialisation status (SSE) |
| `GET` | `/api/health` | Health check |

> **`/api/upload` writes into the shared corpus.** `config.docsDir` points at
> `../knowledge-base/`, so a file uploaded through this UI lands in the corpus that
> Paths B and C also index, and that the numbers in `../RESULTS.md` were measured
> against. Convenient for a demo, but re-run the other paths' ingestion afterwards, and
> do not upload during a measurement run. The handler resolves the path and rejects
> anything escaping `docsDir`, so traversal is guarded.

## Compact Mode

Toggle it in the UI header.

| Setting | Full | Compact |
|---|---|---|
| System prompt | ~300 tokens | ~80 tokens |
| Max output tokens | 1024 | 512 |
| Retrieved chunks | 3 | 3 |

Retrieved chunks are the same in both modes: `chatEngine.js` computes
`Math.min(config.topK, 3)` and `config.topK` is already 3. Raise `topK` in
[`src/config.js`](src/config.js) if you want compact mode to actually narrow retrieval.

## Configuration

All of it in [`src/config.js`](src/config.js):

| Key | Value | Note |
|---|---|---|
| `model` | `phi-3.5-mini` | Must exist in the Foundry Local catalog — check with `foundry model list` |
| `docsDir` | `../knowledge-base` | Shared with Paths B and C |
| `chunkSize` | `200` | Tokens per chunk |
| `chunkOverlap` | `25` | Tokens shared between neighbours |
| `topK` | `3` | Chunks retrieved per query |
| `port` / `host` | `3000` / `127.0.0.1` | Loopback only |

## Key Concepts

### Foundry Local

Microsoft's on-device AI runtime. It runs small language models directly on your machine
with no GPU required and no cloud dependency; the SDK handles model discovery,
downloading, loading, and inference.

```js
import { FoundryLocalManager } from "foundry-local-sdk";

const manager = FoundryLocalManager.create();
const model = manager.catalog.getModel("phi-3.5-mini");
await model.load();

const chatClient = model.createChatClient();
const response = await chatClient.completeChat([
  { role: "user", content: "How do I install Foundry Local?" },
]);
console.log(response.choices[0].message.content);
```

### TF-IDF

Term Frequency–Inverse Document Frequency. Each chunk becomes a numeric vector weighting
each word by how characteristic it is of that chunk relative to all chunks. The question
is vectorised the same way and compared by cosine similarity.

It matches **words, not meaning**. Ask "How do I store vectors in a database?" and it
does well; ask "The assistant keeps making things up, what do I do?" and the target
document does not even reach the top 3. That gap — 2 of 6 questions against 6 of 6 for
embeddings — is the entire reason Path B exists.

### SQLite for vectors

For hundreds to low thousands of chunks, brute-force cosine similarity over SQLite rows
is fast enough and adds no infrastructure: one `.db` file, no Pinecone, no Qdrant, no
Chroma.

## Scripts

| Script | Command | Description |
|---|---|---|
| Ingest | `npm run ingest` | Chunk and index the corpus into SQLite |
| Start | `npm start` | Start the server |
| Dev | `npm run dev` | Start with auto-restart on file changes |
| Test | `npm test` | 51 unit tests — chunker, vector store, config, server |

## What Changed From Upstream

| Upstream (`leestott/local-rag`) | This copy |
|---|---|
| 20 gas engineering documents in `docs/` | The shared 14-document corpus in `../knowledge-base/`, 27 chunks |
| Gas field safety system prompts | Summer-school teaching prompts, rewritten in `src/prompts.js` |
| `foundry-local-sdk@^0.9.0` | `^1.2.4` — 0.9.0 hangs indefinitely inside `catalog.getModel()` against runtime Core 1.2.4. No error, no timeout, no output |
| Download progress multiplied by 100 | Fixed: SDK 1.2.4 already reports 0–100, so the old code printed `Downloading… 3425%` |
| — | `retrieval_check.js`, sharing a question set with Path C for direct comparison |

Both SDK issues are written up in [`../RESULTS.md`](../RESULTS.md) with the two other
defects found while building this project.

## License

MIT. See [`LICENSE`](LICENSE) — the upstream notice, kept verbatim.
