"""Headless end-to-end runner: retrieve, augment, generate, and report timing.

The Streamlit app is the intended interface; this exists so the full pipeline can be
exercised without a browser — in a terminal, in CI, or when measuring latency.

    python ask.py                      # run the built-in test set
    python ask.py "your question"      # ask one question
"""

from __future__ import annotations

import sys
import time

import config
import models
import rag

# The last entry is deliberately unanswerable from the corpus. A system that answers
# it confidently has failed, however well it handles the others.
TEST_QUESTIONS = [
    "What is retrieval-augmented generation?",
    "Which chat model should students start with, and why not a bigger one?",
    "Why does the TF-IDF path not need an embedding model?",
    "How many students fit in the lab and what is the tuition fee?",
]


def main(argv: list[str]) -> int:
    questions = [" ".join(argv[1:])] if len(argv) > 1 else TEST_QUESTIONS

    conn = rag.connect()
    chunks = rag.load_chunks(conn)
    conn.close()

    if not chunks:
        print("No chunks indexed. Run `python ingest.py` first.", file=sys.stderr)
        return 1

    print(f"Loaded {len(chunks)} chunks from {config.DB_PATH.name}. Loading models...")
    embedding_model = models.load_embedding_model(on_progress=lambda pct: None)
    chat_model = models.load_chat_model(on_progress=lambda pct: None)
    embedding_client = embedding_model.get_embedding_client()
    chat_client = chat_model.get_chat_client()
    doc_embeddings = [c.embedding for c in chunks]
    print("Ready.\n")

    for question in questions:
        print("=" * 78)
        print(f"Q: {question}\n")

        started = time.perf_counter()
        query_embedding = embedding_client.generate_embedding(question).data[0].embedding
        results = rag.find_relevant(query_embedding, doc_embeddings, top_k=config.TOP_K)
        retrieved = [chunks[i] for i, _ in results]
        retrieval_time = time.perf_counter() - started

        print("Retrieved:")
        for rank, (i, score) in enumerate(results, 1):
            print(f"  {rank}. {score:.3f}  {chunks[i].source}")
        print()

        print("A: ", end="", flush=True)
        generation_started = time.perf_counter()
        for chunk in chat_client.complete_streaming_chat(
            rag.build_messages(question, retrieved)
        ):
            # The final chunk carries usage data and an empty choices list.
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                print(content, end="", flush=True)
        generation_time = time.perf_counter() - generation_started

        print(
            f"\n\n[retrieval {retrieval_time * 1000:.0f} ms | "
            f"generation {generation_time:.1f} s | "
            f"total {retrieval_time + generation_time:.1f} s]\n"
        )

    embedding_model.unload()
    chat_model.unload()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
