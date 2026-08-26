---
title: TF-IDF Retrieval Without An Embedding Model
category: Retrieval
id: DOC-RT-001
---

# TF-IDF Retrieval Without An Embedding Model

## Summary
TF-IDF scores a passage by how often the query's words appear in it, weighted down
for words that appear everywhere. Combined with cosine similarity it is a complete
retrieval method that needs no embedding model at all.

## How It Works
1. Term frequency: count how many times each word appears in a chunk.
2. Inverse document frequency: words that appear in almost every document carry
   little information, so their weight is reduced.
3. Cosine similarity: represent both the query and each chunk as vectors of weighted
   term counts, then measure the angle between them. A smaller angle means a better
   match.

## Why Choose It For A Teaching Project
- No embedding model to download, so setup is shorter.
- Vectorisation is instant, so the ingest step finishes in under a second.
- For a focused collection of roughly twenty domain documents, results are good.
- The vocabulary and weights are plain numbers a student can print and inspect.
  Neural embeddings are opaque by comparison.

## Where It Falls Short
TF-IDF matches words, not meaning. A question asking about a car will not match a
passage about an automobile. This is precisely the limitation that motivates
embeddings, which is why this program teaches TF-IDF first and embeddings second.

## Tokenisation Warning
A common TF-IDF implementation lowercases the text and strips everything outside the
ASCII letter and digit range. That silently destroys accented and non-Latin
characters. If the knowledge base is not in English, the tokeniser regex must be
widened to a Unicode letter class before retrieval will work at all.
