---
title: Comparing The Three Architectures
category: Program
id: DOC-PG-002
---

# Comparing The Three Architectures

## Why Build Three
Each architecture exists to expose the limitation that motivates the next one. Built
in order, the progression is self-explaining.

## Path A: TF-IDF, Node.js, SQLite
Retrieval by weighted keyword overlap. No embedding model is downloaded or run. Chunks
and term-frequency vectors are persisted in SQLite. The interface is a single HTML page
served by Express with streaming responses.

Strength: fastest possible setup, fully inspectable retrieval.
Limitation: matches words, not meaning.

## Path B: Embeddings, Python, In Memory
Retrieval by cosine similarity over neural embeddings from a real embedding model.
Documents live in a Python list and are re-embedded on every start. The interface is a
command line loop.

Strength: genuine semantic search; a question phrased differently from the source text
still retrieves correctly.
Limitation: nothing is persisted, so startup cost grows with the collection.

## Path C: Embeddings, Python, SQLite
The retrieval of path B with a persistent store, file-based document loading, real
chunking, and a Streamlit interface.

Strength: the only version that is actually a usable application.
Limitation: brute-force search over all vectors; would need an index at much larger
scale.

## What Stays The Same Across B And C
The cosine_similarity and find_relevant functions are identical. Path C changes where
the vectors come from, not how they are compared. Recognising that the retrieval
algorithm and the storage layer are separable concerns is the central architectural
lesson.

## What Changes Across A And B
Everything about retrieval. It is worth stating plainly that these come from two
different sources with two different designs, because material written for one does
not describe the other.
