# Measured Results

Everything below was measured on one machine, not estimated. It is the evidence base
for the claims in [`CURRICULUM.md`](CURRICULUM.md), and the numbers students should be
asked to reproduce rather than take on trust.

**Hardware:** Intel i7-10750H (12 logical cores), NVIDIA RTX 3060 Laptop (5.9 GB),
15.8 GB RAM, Windows 11.
**Software:** Foundry Local CLI 0.10.3, Core 1.2.4, ORT 1.26.0, ORT GenAI 0.14.1,
Node.js 24.11.1, Python 3.12.10.
**Corpus:** the 14 markdown files in `knowledge-base/`, roughly 4,100 words, identical
across all three paths.

---

## Headline

| | Path A (TF-IDF) | Path C (embeddings + SQLite) |
|---|---|---|
| Retrieval accuracy | **2 / 6** | **6 / 6** |
| Retrieval latency | **< 1–3 ms** | **600–770 ms** |
| Answer latency | **~60 s** (`phi-3.5-mini`) | **4.2–7.1 s** (`qwen2.5-0.5b`) |
| Chunks indexed | 27 | 27 |
| Index build time | instant | 35.6 s (one time, then reused) |
| Embedding dimensions | n/a | 1024 |

Both paths index the same 27 chunks from the same 14 documents.

---

## Retrieval accuracy

Six questions, each with one document that should be the top hit. Reproduce with
`node retrieval_check.js` in `path-a-tfidf/` and `python retrieval_check.py` in
`path-c-sqlite/` — the two scripts use the same question set on purpose.

| Question | Path A rank | Path C rank |
|---|---|---|
| How do I install Foundry Local? | **1** ✓ | **1** ✓ |
| How large should a chunk be? | **1** ✓ | **1** ✓ |
| How do I store vectors in a database? | 3 | **1** ✓ |
| The assistant keeps making things up. What do I do? | not in top 3 | **1** ✓ |
| Which model is fast enough for students to iterate with? | 2 | **1** ✓ |
| Nothing happens when I run the CLI, it just sits there | not in top 3 | **1** ✓ |

The split is not random. The first two questions reuse the vocabulary of the documents
they target, and TF-IDF handles them. The last four are worded the way a person actually
asks, and TF-IDF fails all four — including one where the target document never appears
in the top 3 at all.

This is the concrete failure that motivates week 2 of the curriculum. It is worth
running in front of students rather than describing.

---

## Score calibration — the more important finding

An out-of-scope question, answerable by nothing in the corpus:

> "How many students fit in the lab, and what is the tuition fee?"

| | Best in-scope score | Out-of-scope score | Separated? |
|---|---|---|---|
| Path A (TF-IDF) | 0.300 | **0.520** | **No — inverted** |
| Path C (embeddings) | 0.781 | **0.271** | Yes, cleanly |

TF-IDF scored a question it cannot answer **higher than every question it can**. Its
scores are not comparable across queries, so **you cannot threshold on them** — there is
no cutoff that would let the application decline to answer.

Embedding similarity separated cleanly: 0.271 out of scope against 0.447–0.781 in scope.
A threshold around 0.35 would work here.

For Path A this means refusal has to come entirely from the system prompt, because the
retrieval layer cannot tell the difference. That is a genuine architectural limitation,
not a tuning problem, and it is the strongest single argument in the curriculum for
moving to embeddings.

---

## Latency

| Stage | Path A | Path C |
|---|---|---|
| Retrieval | < 1–3 ms | 598–768 ms |
| Generation | ~60 s (`phi-3.5-mini`, maxTokens 1024) | 3.5–6.5 s (`qwen2.5-0.5b`) |
| Total per answer | ~60 s | 4.2–7.1 s |

Retrieval is three orders of magnitude slower with embeddings, and it does not matter:
600 ms against a multi-second generation step is invisible. **The model choice dominates
everything else.**

The ~60 s figure for Path A is the measured cost of a 2.1 GB model with a 1024-token
budget on this hardware. It is the number that justifies the curriculum's insistence on
starting at 0.5B: an hour of tuning at 60 s per iteration is 60 attempts; at 5 s it is
700. Nothing else in the program changes the learning rate that much.

Path C's index build (35.6 s for 27 chunks) happens once. Path B re-embeds its whole
corpus on every start, which is the limitation that motivates persisting the vectors.

---

## Answer quality at 0.5B

The models are small and it shows. Two observed examples:

- Path B, asked the tutorial's own sample question, answered "Python, C#, and
  JavaScript". The source document says "Python, C#, JavaScript, and Rust". **It dropped
  a list item that was directly in front of it.**
- Path C, asked what RAG is, produced a partly garbled definition on one run ("a small
  locally trained model... bypasses the need for extensive training") and a correct
  three-step answer on the next — **same question, same retrieved chunks, same topK of
  3.** The variation is the model's own sampling, not a configuration difference.

Both are worth showing to students. Grounded retrieval reduces hallucination; it does not
eliminate it, and a 0.5B model will still garble a summary it has the text for — and will
not necessarily garble it the same way twice. Any evaluation that runs each question once
is measuring noise as much as quality.

### The refusal test

Asked the out-of-scope question, Path C correctly reported that the information was not
in the context rather than inventing a number. This is the test that matters most: an
assistant that cannot decline is not usable regardless of how well it answers.

Note the split responsibility. Path C's retrieval scored the question at 0.271 and its
system prompt turned that into a refusal. Path A's retrieval scored it 0.520 — its
highest score of the run — so its system prompt is doing that work unaided.

---

## Defects found while building this

Four things that will bite students, none of them documented upstream.

### 1. The official tutorial code crashes at the end of every answer

The Learn tutorial's streaming loop:

```python
for chunk in chat_client.complete_streaming_chat(messages):
    content = chunk.choices[0].delta.content
```

The final chunk carries usage data and an **empty** `choices` list, so `choices[0]`
raises `IndexError` after the answer has printed. Guard it:

```python
if not chunk.choices:
    continue
```

Fixed in `path-b-embeddings/main.py`, `path-c-sqlite/ask.py`, and `path-c-sqlite/app.py`.

### 2. The JavaScript SDK pinned by the blog repo hangs

`leestott/local-rag` pins `foundry-local-sdk@^0.9.0`. Against runtime Core 1.2.4 that
version hangs indefinitely inside `catalog.getModel()` — no error, no timeout, no output.
Upgrading to `foundry-local-sdk@^1.2.4` fixes it.

A silent hang is the worst possible failure mode for a beginner. Pin the SDK to match the
runtime before the program starts.

### 3. The download progress callback changed units

SDK 1.2.4 reports progress as **0–100**, not 0–1. The repo's `chatEngine.js` multiplies by
100 and prints "Downloading… 3425%". Fixed in `path-a-tfidf/src/chatEngine.js`.

### 4. `model.isCached` does not see CLI-cached models

Models downloaded with `foundry model download` are reported as not cached by both SDKs,
which then download them again. The SDKs select their own hardware variant — the CLI
fetched `qwen2.5-0.5b-instruct-trtrtx-gpu`, the SDK wanted a different one. Budget for
each model being downloaded twice, or download once through the SDK path students will
actually use.

---

## Reproducing

```bash
# Path A - TF-IDF retrieval only, no model load, runs in milliseconds
cd path-a-tfidf && npm run ingest && node retrieval_check.js

# Path C - embedding retrieval only, no chat model
cd path-c-sqlite && python ingest.py && python retrieval_check.py

# Path C - full pipeline with timings, including the refusal test
cd path-c-sqlite && python ask.py

# Unit tests
cd path-a-tfidf && npm test              # 51 tests
cd path-c-sqlite && python -m unittest test_rag -v   # 21 tests
```

The two `retrieval_check` scripts deliberately share a question set. Run both and read
the outputs side by side — that comparison is the single most useful artifact in this
repository for teaching why retrieval strategy matters.
