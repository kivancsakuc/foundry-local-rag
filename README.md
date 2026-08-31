# Local RAG with Foundry Local — Three Architectures

An offline Retrieval-Augmented Generation assistant, built three ways, over one shared
document corpus. Nothing leaves the machine: model inference, retrieval, and storage are
all local.

This repository is both an internship project and the working reference for a one-month
summer school curriculum. The curriculum itself is [`CURRICULUM.md`](CURRICULUM.md).

## Why three implementations

Each one exists to expose the limitation that motivates the next.

| | Retrieval | Storage | Language | Interface |
|---|---|---|---|---|
| [`path-a-tfidf/`](path-a-tfidf/) | TF-IDF + cosine, **no embedding model** | SQLite | Node.js + Express | HTML page, SSE streaming |
| [`path-b-embeddings/`](path-b-embeddings/) | Neural embeddings | none — a Python list | Python | CLI |
| [`path-c-sqlite/`](path-c-sqlite/) | Neural embeddings | SQLite | Python | Streamlit |

- **Path A** gets a complete RAG pipeline running in minutes, with retrieval you can
  read as plain numbers. It matches words, not meaning.
- **Path B** replaces keyword scoring with real semantic search, so a question phrased
  differently from the source text still retrieves. It persists nothing and re-embeds
  every document on every start.
- **Path C** keeps Path B's retrieval — `cosine_similarity` and `find_relevant` are
  carried over unchanged — and adds file loading, paragraph-aware chunking, a SQLite
  vector store, and a chat interface. Only where the vectors come from changes.

Path A is adapted from [leestott/local-rag](https://github.com/leestott/local-rag).
Path B is the [Microsoft Learn tutorial](https://learn.microsoft.com/en-us/azure/foundry-local/tutorials/tutorial-build-rag-app).
Path C is this project's own work.

## The shared corpus

All three index [`knowledge-base/`](knowledge-base/) — 14 markdown documents about the
curriculum, the tools, and the architectures themselves. The assistant answers questions
about its own course, which makes the demo self-contained and keeps the three paths
directly comparable.

Documents carry optional front matter (`title`, `category`, `id`). To use your own
corpus, replace the files; no code change is needed.

## Prerequisites

```bash
winget install Microsoft.FoundryLocal
winget install Python.Python.3.12
foundry server start
```

Node.js 20+ for Path A. On Windows the SDK needs a real DirectX 12 GPU; VMs without GPU
passthrough are not supported.

Confirm the model aliases exist before running anything:

```bash
foundry model list
```

## Running

### Path A — TF-IDF

```bash
cd path-a-tfidf
npm install
npm run ingest
npm start                  # http://127.0.0.1:3000
node retrieval_check.js    # retrieval only, no model load, milliseconds
npm test
```

### Path B — in-memory embeddings

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python path-b-embeddings/main.py
```

`requirements.txt` selects the right SDK package per platform, so the same command
works everywhere. On macOS and Linux activate with `source .venv/bin/activate`.

### Path C — embeddings + SQLite + Streamlit

```bash
cd path-c-sqlite
python ingest.py                  # index the corpus into data/rag.db (run once)
streamlit run app.py              # the interface
python ask.py                     # headless: full pipeline with timings
python retrieval_check.py         # retrieval only, no chat model, ~5 s
python -m unittest test_rag -v
```

Verify the index directly rather than trusting it:

```bash
sqlite3 path-c-sqlite/data/rag.db "SELECT count(*) FROM documents;"
```

## Models

| Alias | Type | Size | Used by |
|---|---|---|---|
| `qwen2.5-0.5b` | Chat | 528 MB | Paths B, C |
| `qwen3-embedding-0.6b` | Embedding | 478 MB | Paths B, C |
| `phi-3.5-mini` | Chat | 2.1 GB | Path A |

Chat and embedding aliases for Path C live in `path-c-sqlite/config.py`; Path A's live in
`path-a-tfidf/src/config.js`.

## Measured results

Full numbers and method in [`RESULTS.md`](RESULTS.md). The headline, same corpus and
same six questions on both paths:

| | Path A (TF-IDF) | Path C (embeddings) |
|---|---|---|
| Retrieval accuracy | 2 / 6 | **6 / 6** |
| Retrieval latency | < 1–3 ms | 600–770 ms |
| Answer latency | ~60 s (`phi-3.5-mini`) | 4.2–7.1 s (`qwen2.5-0.5b`) |

The sharper finding is score calibration. On a question the corpus cannot answer, TF-IDF
scored **0.520 — higher than any question it could answer** (best 0.300), so there is no
threshold at which it could decline. Embedding similarity scored the same question 0.271
against 0.447–0.781 in scope, cleanly separated.

Run `node retrieval_check.js` and `python retrieval_check.py` and read the two outputs
side by side. They share a question set on purpose.

## Testing it honestly

Two checks matter more than any others:

1. **Ask something the corpus cannot answer.** If the assistant answers confidently
   instead of admitting ignorance, the system prompt is not doing its job — regardless of
   how well it handles answerable questions.
2. **Turn off the network and ask a question.** That is the whole claim of the project.

Path C shows the retrieved chunks and their similarity scores next to every answer, on
purpose. When an answer is wrong, the first question is always whether the right passage
was retrieved at all.

## What is in this repository

| Path | What it is |
|---|---|
| `knowledge-base/` | The shared corpus. All three paths index it |
| `path-a-tfidf/`, `path-b-embeddings/`, `path-c-sqlite/` | The three implementations |
| `CURRICULUM.md` | The revised one-month curriculum — the source of record |
| `Summer_School_Foundry_Local_Plan_REVISED.docx` | The same curriculum as Word, for reviewers who work in Word. **Generated, not edited by hand** |
| `tools/md_to_docx.py` | Generates that .docx: `python tools/md_to_docx.py CURRICULUM.md -o Summer_School_Foundry_Local_Plan_REVISED.docx`. Re-run it after editing `CURRICULUM.md`, or the two drift apart |
| `RESULTS.md` | Every measured number, and how to reproduce it |

## Known limitations

- Retrieval is brute-force over every stored vector. Linear cost is imperceptible at this
  scale and would need an approximate index far beyond it.
- Path A's TF-IDF tokeniser strips characters outside ASCII letters and digits, so a
  corpus in another alphabet will retrieve badly and silently. Widen the regex in
  `path-a-tfidf/src/chunker.js` before using one.
- Path C stores vectors as JSON text. Packed binary would be more compact, but JSON is
  readable while debugging, which matters more here.
- Streamlit pings a usage-statistics endpoint by default and binds to every interface,
  both of which contradict the offline claim. `path-c-sqlite/.streamlit/config.toml`
  turns the telemetry off and binds to `127.0.0.1`. Keep that file if you copy the app
  elsewhere.
