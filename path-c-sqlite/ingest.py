"""Index the shared knowledge base into SQLite.

Reads every markdown file in the knowledge-base folder, splits it into overlapping
chunks, embeds each chunk with the embedding model, and stores chunk plus vector.

This is the step that Path B lacks: after running it once, startup no longer
re-embeds anything.

Run:  python ingest.py
"""

from __future__ import annotations

import sys
import time

import config
import models
import rag


def main() -> int:
    print("=== Summer School RAG - Ingestion (embeddings + SQLite) ===\n")

    if not config.DOCS_DIR.exists():
        print(f"Knowledge base not found: {config.DOCS_DIR}", file=sys.stderr)
        return 1

    files = sorted(config.DOCS_DIR.glob("*.md"))
    if not files:
        print(f"No markdown files found in {config.DOCS_DIR}", file=sys.stderr)
        return 1

    print(f"Found {len(files)} documents.\n")

    # Read and chunk first, so a chunking mistake surfaces before the model loads.
    pending: list[tuple[str, str, str]] = []  # (source, title, content)
    for path in files:
        meta, body = rag.parse_front_matter(path.read_text(encoding="utf-8"))
        title = meta.get("title", path.stem)
        chunks = rag.chunk_text(body)
        for chunk in chunks:
            pending.append((path.name, title, chunk))
        print(f"  {path.name} -> {len(chunks)} chunk(s)")

    print(f"\nChunked into {len(pending)} passages. Loading embedding model...")
    embedding_model = models.load_embedding_model()
    print()
    embedding_client = embedding_model.get_embedding_client()

    started = time.perf_counter()
    response = embedding_client.generate_embeddings([c[2] for c in pending])
    vectors = [item.embedding for item in response.data]
    elapsed = time.perf_counter() - started

    if len(vectors) != len(pending):
        print(
            f"Embedding count mismatch: {len(vectors)} vectors for {len(pending)} chunks",
            file=sys.stderr,
        )
        return 1

    chunks = [
        rag.Chunk(source=src, title=title, content=content, embedding=vec)
        for (src, title, content), vec in zip(pending, vectors)
    ]

    conn = rag.connect()
    rag.clear(conn)
    rag.insert_chunks(conn, chunks)
    total = rag.count_chunks(conn)
    conn.close()

    embedding_model.unload()

    print(f"\nEmbedded {len(vectors)} chunks in {elapsed:.1f}s "
          f"({len(vectors[0])} dimensions each).")
    print(f"Ingestion complete: {total} chunks from {len(files)} documents.")
    print(f"Database: {config.DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
