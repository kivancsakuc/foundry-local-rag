"""Core RAG logic: chunking, the SQLite vector store, retrieval, and generation.

The retrieval functions `cosine_similarity` and `find_relevant` are carried over
from Path B unchanged. That is the point of this path: the retrieval algorithm and
the storage layer are separable concerns. Only where the vectors come from changes.
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import config

# --------------------------------------------------------------------------
# Chunking
# --------------------------------------------------------------------------

FRONT_MATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", re.DOTALL)


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split optional YAML-ish front matter from the document body."""
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text

    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta, match.group(2)


def chunk_text(
    text: str,
    max_tokens: int = config.CHUNK_SIZE,
    overlap_tokens: int = config.CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks of roughly `max_tokens` words.

    Paragraph boundaries are respected first, because the author already grouped
    related ideas together. A paragraph longer than `max_tokens` is then split by
    word count with overlap, so a sentence straddling a boundary still retrieves.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks: list[str] = []
    buffer: list[str] = []
    buffer_len = 0

    def flush() -> None:
        nonlocal buffer, buffer_len
        if buffer:
            chunks.append("\n\n".join(buffer))
            buffer, buffer_len = [], 0

    for para in paragraphs:
        words = para.split()

        if len(words) > max_tokens:
            # Paragraph is too big on its own: flush what we have, then window it.
            flush()
            start = 0
            while start < len(words):
                end = min(start + max_tokens, len(words))
                chunks.append(" ".join(words[start:end]))
                if end >= len(words):
                    break
                start = end - overlap_tokens
            continue

        if buffer_len + len(words) > max_tokens:
            flush()

        buffer.append(para)
        buffer_len += len(words)

    flush()
    return chunks


# --------------------------------------------------------------------------
# Retrieval - identical to Path B
# --------------------------------------------------------------------------


def cosine_similarity(a, b):
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def find_relevant(query_embedding, doc_embeddings, top_k=config.TOP_K):
    """Return the indices and scores of the top-k most similar documents."""
    scores = []
    for i, doc_emb in enumerate(doc_embeddings):
        score = cosine_similarity(query_embedding, doc_emb)
        scores.append((i, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]


# --------------------------------------------------------------------------
# SQLite vector store
# --------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id        INTEGER PRIMARY KEY,
    source    TEXT NOT NULL,
    title     TEXT NOT NULL,
    content   TEXT NOT NULL,
    embedding TEXT NOT NULL
);
"""


@dataclass
class Chunk:
    """One retrievable passage, with the metadata needed to cite it."""

    source: str
    title: str
    content: str
    embedding: list[float]


def connect(db_path: Path = config.DB_PATH) -> sqlite3.Connection:
    """Open the database, creating the file and schema if needed."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def clear(conn: sqlite3.Connection) -> None:
    """Drop all indexed chunks. Ingestion starts from a clean slate each run."""
    conn.execute("DELETE FROM documents")
    conn.commit()


def insert_chunks(conn: sqlite3.Connection, chunks: list[Chunk]) -> None:
    """Persist chunks. SQLite has no vector type, so the vector is JSON text."""
    conn.executemany(
        "INSERT INTO documents (source, title, content, embedding) VALUES (?, ?, ?, ?)",
        [(c.source, c.title, c.content, json.dumps(c.embedding)) for c in chunks],
    )
    conn.commit()


def load_chunks(conn: sqlite3.Connection) -> list[Chunk]:
    """Read every chunk and vector into memory.

    Brute-force scoring over all vectors is linear, which is imperceptible at this
    scale. An approximate-nearest-neighbour index only pays off far beyond it.
    """
    rows = conn.execute(
        "SELECT source, title, content, embedding FROM documents ORDER BY id"
    ).fetchall()
    return [Chunk(r[0], r[1], r[2], json.loads(r[3])) for r in rows]


def count_chunks(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]


# --------------------------------------------------------------------------
# Prompt assembly
# --------------------------------------------------------------------------


def build_messages(query: str, retrieved: list[Chunk]) -> list[dict[str, str]]:
    """Put the retrieved chunks in the system message and the question in the user message."""
    context = "\n\n".join(f"[{c.title}]\n{c.content}" for c in retrieved)
    return [
        {"role": "system", "content": config.SYSTEM_PROMPT.format(context=context)},
        {"role": "user", "content": query},
    ]
