# One-Month Project Plan: Local RAG AI Assistant with Microsoft Foundry Local

> Revised plan. This supersedes `Summer School Foundry Local Plan.docx`. See
> [Corrections To The Original Plan](#corrections-to-the-original-plan) for what changed
> and why. Every command, package name, and model alias below was verified on a real
> machine (Windows 11, Foundry Local 0.10.3 / Core 1.2.4) rather than taken from a draft.
> Timings and retrieval accuracy come from actual runs, recorded in
> [`RESULTS.md`](RESULTS.md).

## Goal

Guide beginner computer science students through a full-time, one-month summer program
in which they build a local question-answering assistant using Microsoft Foundry Local
for offline model inference and the RAG (Retrieval-Augmented Generation) pattern.

By the end, each team has a working offline assistant that answers questions about a
small document collection by retrieving passages locally and feeding them to an
on-device language model. No cloud account. No network call at inference time.

---

## The Central Structural Decision

The two Microsoft sources this program draws on describe **two different
architectures**. Conflating them is the single biggest source of confusion, and it was
the main defect in the original plan.

| | Source | Language | Retrieval | Storage | Interface |
|---|---|---|---|---|---|
| **Path A** | [Tech Community blog](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/building-your-first-local-rag-application-with-foundry-local/4501968) · [repo](https://github.com/leestott/local-rag) | Node.js + Express | **TF-IDF + cosine** — no embedding model | SQLite | HTML page, SSE streaming |
| **Path B** | [Microsoft Learn tutorial](https://learn.microsoft.com/en-us/azure/foundry-local/tutorials/tutorial-build-rag-app) | Python | **Neural embeddings** (`qwen3-embedding-0.6b`) | none — a Python list | CLI |
| **Path C** | This program's own extension | Python | Neural embeddings | SQLite | Streamlit |

**The blog does not use embeddings at all.** Any material about embedding models,
vector similarity, or `find_relevant()` comes from the Learn tutorial, not the blog.

This program teaches all three, in order, because each one exposes the limitation that
motivates the next:

- Path A shows the *shape* of RAG end to end, on day one, with the shortest possible setup.
- Path A retrieved the right document for only **2 of 6** test questions, against 6 of 6
  for embeddings — **that failure motivates Path B.** Worse, it scored a question it
  could not answer *higher* than every question it could, so it cannot decline on
  evidence. Both numbers are reproducible with the two `retrieval_check` scripts.
- Path B re-embeds everything on every start and persists nothing — **that motivates Path C.**

Working implementations of all three live in this repository under `path-a-tfidf/`,
`path-b-embeddings/`, and `path-c-sqlite/`, sharing one corpus in `knowledge-base/`.

---

## Prerequisites And Environment

### Hardware

- 8 GB RAM minimum; 16 GB comfortable.
- Roughly 10 GB free disk for the runtime and model weights.
- **Windows only:** the `-winml` SDK package requires a real DirectX 12 GPU.
  **Virtual machines without GPU passthrough are not supported.** If the teaching lab
  runs on VMs, confirm this before the program starts, or plan to use the
  cross-platform package instead. This is a go/no-go check, not a footnote.

### Software

```bash
winget install Microsoft.FoundryLocal     # the runtime
winget install Python.Python.3.12         # see the Python version note below
```

Node.js 20 or later is also required for Path A.

Verify, and note that these are two different version numbers for the same product:

```bash
foundry --version        # CLI version, e.g. 0.10.3
foundry status           # includes "Foundry Local Core", e.g. 1.2.4
```

The **Core** version is the one that must line up with the Python SDK version. A CLI at
0.x alongside an SDK at 1.x is normal and is not a mismatch.

### Python version

Use **Python 3.12**. The SDK's metadata says `>=3.11`, but its published classifiers
cover 3.11, 3.12, and 3.13 only. Newer releases are untested territory, and in a
program with twenty students a tested version is worth the five minutes it costs.

### Start the service before anything else

A fresh install leaves the service stopped, and the first CLI command against a stopped
service can appear to hang for a long time rather than failing:

```bash
foundry server start
foundry model list        # confirm the aliases you plan to teach actually exist
```

---

## Models

Verified present in the catalog as of August 2026:

| Alias | Type | Size | Use |
|---|---|---|---|
| `qwen2.5-0.5b` | Chat | 528 MB | **Default chat model.** Start here. |
| `qwen3-embedding-0.6b` | Embedding | 478 MB | Paths B and C |
| `phi-3.5-mini` | Chat | 2.1 GB | Path A's default, from the blog |
| `phi-4-mini` | Chat | 2.2 GB | Optional upgrade in week 5 |

**Start at 0.5B, not 3-5B.** Measured on the reference machine: `qwen2.5-0.5b` answers in
**4.2-7.1 s** end to end; `phi-3.5-mini`, at 2.1 GB with a 1024-token budget, takes
**~60 s**.

In a program where students change a prompt and re-run constantly, that difference
decides how much they learn: an hour of tuning at 60 s per iteration is 60 attempts, at
5 s it is 700. Swapping the alias later is a one-line change, so have students make the
upgrade themselves in the final week and measure the trade-off. That comparison teaches
more than starting large would.

**Always verify aliases with `foundry model list` before teaching them.** Aliases change
between catalog releases, and a nonexistent alias fails confusingly at download time
rather than with a clear error.

---

## Phase 1 (Weeks 1-2): Foundations By Building

The original plan spent two weeks on concepts before students built anything. This
version front-loads a working system: students see RAG end to end in week 1 and then
learn each component by replacing it.

### Week 1 — RAG End To End With TF-IDF (Path A)

**Objective:** understand the shape of a RAG pipeline by running one and then adapting it.

**Topics**
- What RAG is: retrieve, augment, generate. What problem it solves.
- Foundry Local: what it is, how it downloads and runs models on-device.
- TF-IDF and cosine similarity as a retrieval method.
- Chunking: size, overlap, and why both matter.
- System prompts: grounding, and permitting the model to admit ignorance.

**Exercises**
1. Install Foundry Local, start the service, list the catalog, run one completion.
2. Clone and run the reference application **unchanged**. See it answer questions about
   its own sample corpus. This is the baseline: if it works, the environment is sound.
3. Replace the corpus with the team's own markdown documents. Rewrite `src/prompts.js`.
   Tune `chunkSize`, `chunkOverlap`, and `topK` in `src/config.js`.
4. Ask a question using words that do not appear in the documents. **Record the failure.**
   This is the motivating evidence for week 2.

**Watch for**
- `better-sqlite3` is a native module. On a Node release newer than its prebuilt
  binaries, npm compiles from source and needs a C++ toolchain. If it fails, upgrade the
  package to a major version that ships a matching binary.
- The default TF-IDF tokeniser strips everything outside ASCII letters and digits. **A
  corpus in any other alphabet will retrieve badly and silently.** Widen the regex to a
  Unicode letter class first.

**Milestone:** a working offline assistant answering questions about the team's own
documents, plus a written record of one question TF-IDF got wrong.

### Week 2 — Embeddings And Semantic Search (Path B)

**Objective:** understand why keyword matching is not enough, and implement the
alternative.

**Topics**
- Text embeddings: vectors that encode meaning rather than vocabulary.
- Cosine similarity, implemented by hand rather than imported.
- Brute-force top-k search, and when an approximate index would be needed instead.
- The rule that indexing and querying must use the same embedding model.

**Exercises**
1. Set up a Python 3.12 virtual environment and install the SDK
   (see [Installing The SDK](#installing-the-sdk)).
2. Work through the Learn tutorial. Type `cosine_similarity` and `find_relevant` out
   rather than pasting them.
3. Re-run week 1's failing question against the embedding version. Compare.
4. Print the similarity scores for every document against one query. Discuss why the
   ranking came out as it did.

**Milestone:** a CLI assistant using genuine semantic retrieval, and a side-by-side
comparison with week 1's TF-IDF result.

---

## Phase 2 (Weeks 3-4): Building The Real Application (Path C)

### Week 3 — Persistence And A Real Ingestion Pipeline

**Objective:** turn the tutorial into an application: read real files, chunk them
properly, and persist the vectors.

**Topics**
- Reading a document collection from disk; parsing optional front matter.
- Paragraph-aware chunking with overlap.
- SQLite as a local store: serverless, single file, in Python's standard library.
- Serialising a vector into a text column, because SQLite has no vector type.

**Schema**

```sql
CREATE TABLE IF NOT EXISTS documents (
    id        INTEGER PRIMARY KEY,
    source    TEXT NOT NULL,
    title     TEXT NOT NULL,
    content   TEXT NOT NULL,
    embedding TEXT NOT NULL   -- JSON-serialised list of floats
);
```

`source` and `title` are what make source citation possible later. Do not omit them.

**Exercises**
1. Write `ingest.py`: read, chunk, embed in one batch call, insert.
2. Verify with SQL, not with trust:
   `sqlite3 data/rag.db "SELECT count(*) FROM documents;"`
3. Load the vectors at startup and pass them to **week 2's `find_relevant()`, unchanged.**

**The architectural point of this week:** the retrieval algorithm and the storage layer
are separable. Only the data source changed. If a student had to modify
`find_relevant()`, the layering is wrong.

**Milestone:** an assistant that indexes once and starts instantly thereafter.

### Week 4 — Interface, Grounding, And Citation

**Objective:** make it usable and make its behaviour inspectable.

**Topics**
- A chat interface with Streamlit (`st.chat_input`, `st.chat_message`, `st.write_stream`).
- Streaming responses, and why they change perceived latency.
- Displaying retrieved chunks in the interface.
- Prompt engineering for grounded answers and source citation.

**Exercises**
1. Replace the CLI loop with a Streamlit app.
2. **Show the retrieved chunks and their similarity scores next to every answer.** When
   an answer is wrong, the first question is always whether the right passage was
   retrieved at all; hiding that makes the system impossible to debug.
3. Make `topK` adjustable in the interface and observe the effect on both answer quality
   and response time.
4. Add source citation: pass the source filename with each chunk and instruct the model
   to name it.

**Milestone:** a demonstrable application that shows its own retrieval.

---

## Phase 3 (Week 5): Evaluation, Documentation, Presentation

### Testing

Diagnose **retrieval** and **generation** separately. They have different fixes, and
changing a prompt cannot repair a passage that was never retrieved.

Write at least ten test questions before tuning anything:
- Six the documents clearly answer.
- Two that require combining two documents.
- **Two the documents definitely do not answer.**

The last two are the most informative. An assistant that answers them confidently is
hallucinating, and that is a correctness bug, not a matter of style. **A system that
cannot admit ignorance has not passed.**

### Measurement

Record, for each of the three paths: response time, whether retrieval found the right
passage, and whether the answer was correct. This table is the evidence base for the
final report and makes tuning decisions defensible rather than anecdotal.

### The demo

The demo must include **switching off the network** and asking a question. That is the
entire claim of the project, and it takes ten seconds to prove.

### Documentation

A README covering purpose, architecture, setup, usage, and known limitations. Teams
should be able to state which of the three architectures they shipped and why.

**Milestone:** documented, tested projects and a rehearsed demo.

---

## Installing The SDK

Windows:

```bash
pip install foundry-local-sdk-winml openai
```

macOS and Linux:

```bash
pip install foundry-local-sdk openai
```

The `openai` package is required on both, because the SDK's chat and embedding clients
build on it. On Windows, prefer the `-winml` variant: it exposes the same API with a
wider range of hardware acceleration through the Windows ML runtime.

The current SDK surface (Core 1.2.4):

```python
from foundry_local_sdk import Configuration, FoundryLocalManager

FoundryLocalManager.initialize(Configuration(app_name="my_app"))
manager = FoundryLocalManager.instance

model = manager.catalog.get_model("qwen3-embedding-0.6b")
model.download(lambda pct: ...)
model.load()
client = model.get_embedding_client()
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `Request to local service failed` | The service is not running: `foundry server restart` |
| A CLI command produces no output for many minutes | The service was never started. Stop it, run `foundry server start`, retry. |
| Model alias not found | The alias is not in this catalog release. Check `foundry model list`. |
| `better-sqlite3` fails to build | No prebuilt binary for your Node version. Install a C++ toolchain or upgrade the package. |
| Retrieval returns irrelevant chunks | Inspect the chunks before blaming the model. Check chunk size, and check the tokeniser is not stripping your alphabet. |
| Answers ignore the context | Confirm the context is really in the system message and that the instruction to use only that context is present. |
| Windows ML errors on a VM | No DirectX 12 GPU passthrough. Use the cross-platform SDK package. |
| `npm start` prints "Discovering available models" and never continues | `foundry-local-sdk` 0.9.x hangs silently against Core 1.2.x. Upgrade to `^1.2.4`. |
| `IndexError` right after an answer finishes printing | The final streaming chunk has an empty `choices` list. Guard with `if not chunk.choices: continue`. The Learn tutorial's own code omits this. |
| Download progress shows numbers above 100% | The SDK reports 0-100, not 0-1. Do not multiply by 100. |
| A model downloads again although `foundry cache list` shows it | The SDK picks its own hardware variant, separate from the CLI's. Budget for two downloads. |

---

## Corrections To The Original Plan

| The original plan said | Correct |
|---|---|
| `pip install foundry-local-sdk` | On Windows, `foundry-local-sdk-winml`. The `openai` package is required as well, on every platform. |
| Load the model `phi-1.5-mini` | **No such alias exists.** Use `qwen2.5-0.5b`, `phi-4-mini`, or `phi-3.5-mini`, all verified in the catalog. |
| Use a chat model of "3-5B parameters" | Start at 0.5B. A 3B model on CPU costs 10+ seconds per answer and destroys the iteration loop that the program depends on. Upgrade in week 5 as a deliberate exercise. |
| Week 2's embedding material comes from the blog | **The blog uses TF-IDF and never touches embeddings.** That material is from the Learn tutorial. The two sources describe different architectures. |
| Weeks 1-2 are concepts, building starts week 3 | Students build a working RAG system in week 1. Concepts are taught by replacing components of something that already runs. |
| Response times of "~1-3 seconds" assumed | Measure on the actual lab hardware and record it. Do not assume. |

### Also added

- The DirectX 12 / virtual machine constraint, promoted to a go/no-go prerequisite check.
- `foundry server start` as an explicit step, because a stopped service hangs rather than fails.
- The CLI-version versus Core-version distinction, which otherwise reads as a mismatch.
- The TF-IDF tokeniser's non-ASCII behaviour, which silently breaks non-English corpora.
- A named third architecture (Path C) instead of an unscoped "extend it with SQLite".
- The requirement to test questions the corpus cannot answer.
- Four defects found while building the reference implementations: the silent SDK hang,
  the `IndexError` in the official tutorial's streaming loop, the changed progress units,
  and the SDK/CLI cache mismatch. All four are in the troubleshooting table above and
  detailed in [`RESULTS.md`](RESULTS.md).
- Measured latency and retrieval accuracy in place of assumed figures.

---

## Reference Material

- Blog: [Building Your First Local RAG Application with Foundry Local](https://techcommunity.microsoft.com/blog/azuredevcommunityblog/building-your-first-local-rag-application-with-foundry-local/4501968)
- Repo (Path A): <https://github.com/leestott/local-rag>
- Tutorial (Path B): [Build a RAG application](https://learn.microsoft.com/en-us/azure/foundry-local/tutorials/tutorial-build-rag-app)
- Contrast, no retrieval at all: <https://github.com/leestott/local-cag>
- [Getting Started with Foundry Local: A Student Guide](https://techcommunity.microsoft.com/t5/educator-developer-blog/getting-started-with-foundry-local-a-student-guide-to-the/ba-p/4503604)
