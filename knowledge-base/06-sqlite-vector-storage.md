---
title: Storing Embeddings In SQLite
category: Pipeline
id: DOC-PP-002
---

# Storing Embeddings In SQLite

## Summary
SQLite is a serverless database contained in a single file. It is the natural place to
persist document chunks and their embedding vectors for a local RAG application.

## Why SQLite
- No server process to install, configure, or start.
- The entire database is one file that can be copied, backed up, or deleted.
- Bundled with Python as the built-in sqlite3 module, so there is no new dependency.
- Cross-platform and extremely widely deployed.

## The Problem It Solves Here
The Microsoft Learn tutorial holds embeddings in a Python list. That works, but every
restart re-embeds every document. With a persistent store, indexing happens once and
startup is instant afterwards.

## Schema

    CREATE TABLE IF NOT EXISTS documents (
        id        INTEGER PRIMARY KEY,
        source    TEXT NOT NULL,
        content   TEXT NOT NULL,
        embedding TEXT NOT NULL
    );

The source column records which file the chunk came from, which is what makes source
citation in the answer possible. The content column is the chunk text. The embedding
column is the vector.

## Storing A Vector In A Text Column
SQLite has no native vector type. Serialise the list of floats to JSON on the way in
and parse it on the way out:

    cur.execute(
        "INSERT INTO documents (source, content, embedding) VALUES (?, ?, ?)",
        (source, chunk, json.dumps(vector)),
    )

A BLOB of packed floats is more compact, but JSON is human-readable, which matters
when students are debugging their own pipeline.

## Search Strategy
Load all vectors into memory at startup and run the same brute-force cosine similarity
search used by the in-memory version. SQLite cannot compute cosine similarity in SQL
without an extension, and at this scale it does not need to. The retrieval function
itself does not change, only where the vectors came from.
