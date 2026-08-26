"""Retrieval-only smoke test: no chat model, just the search step.

When a RAG answer is wrong, the first question is always whether the right passage
was retrieved at all. This script answers that question on its own, and it runs in
seconds because no chat model is loaded.

Run:  python retrieval_check.py
"""

from __future__ import annotations

import sys
import time

import models
import rag

# (question, filename fragment that SHOULD be the top hit)
CASES = [
    # Plainly worded - any retriever should get these.
    ("How do I install Foundry Local?", "01-what-is-foundry-local"),
    ("How large should a chunk be?", "05-chunking-strategy"),
    ("How do I store vectors in a database?", "06-sqlite-vector-storage"),
    # Worded differently from the source text - these are the ones that separate
    # semantic search from keyword matching.
    ("The assistant keeps making things up. What do I do?", "07-prompt-engineering"),
    ("Which model is fast enough for students to iterate with?", "08-model-selection"),
    ("Nothing happens when I run the CLI, it just sits there", "12-troubleshooting"),
]

# Deliberately outside the corpus - retrieval will still return its best guess, so
# the scores are what matter here, not the ranking.
OUT_OF_SCOPE = "How many students fit in the lab, and what is the tuition fee?"


def main() -> int:
    conn = rag.connect()
    chunks = rag.load_chunks(conn)
    conn.close()

    if not chunks:
        print("No chunks indexed. Run `python ingest.py` first.", file=sys.stderr)
        return 1

    print(f"Loaded {len(chunks)} chunks. Loading embedding model...\n")
    embedding_model = models.load_embedding_model(on_progress=lambda pct: None)
    client = embedding_model.get_embedding_client()

    doc_embeddings = [c.embedding for c in chunks]
    passed = 0

    for question, expected in CASES:
        started = time.perf_counter()
        query_embedding = client.generate_embedding(question).data[0].embedding
        results = rag.find_relevant(query_embedding, doc_embeddings, top_k=3)
        elapsed = time.perf_counter() - started

        top_source = chunks[results[0][0]].source
        hit_rank = next(
            (r + 1 for r, (i, _) in enumerate(results) if expected in chunks[i].source),
            None,
        )
        ok = hit_rank == 1
        passed += ok

        print(f"{'PASS' if ok else 'MISS'}  {question}")
        print(f"      expected {expected}, top hit {top_source}")
        if hit_rank and not ok:
            print(f"      (expected document was ranked {hit_rank} of 3)")
        for rank, (i, score) in enumerate(results, 1):
            print(f"        {rank}. {score:.3f}  {chunks[i].source}")
        print(f"      retrieved in {elapsed * 1000:.0f} ms\n")

    # Out-of-scope query: report the top score so the grounding threshold is visible.
    query_embedding = client.generate_embedding(OUT_OF_SCOPE).data[0].embedding
    results = rag.find_relevant(query_embedding, doc_embeddings, top_k=3)
    print(f"OUT OF SCOPE  {OUT_OF_SCOPE}")
    print(f"      best score {results[0][1]:.3f} ({chunks[results[0][0]].source})")
    print("      A low score here is what the system prompt has to turn into "
          "an admission of ignorance.\n")

    embedding_model.unload()

    print(f"{passed}/{len(CASES)} questions retrieved the expected document at rank 1.")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
