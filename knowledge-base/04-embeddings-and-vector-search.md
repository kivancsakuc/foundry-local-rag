---
title: Embeddings And Vector Search
category: Retrieval
id: DOC-RT-002
---

# Embeddings And Vector Search

## Summary
An embedding model converts a piece of text into a list of numbers, a vector, that
represents its meaning. Texts with similar meaning produce vectors that point in
similar directions, even when they share no words.

## Why Embeddings Beat Keyword Matching
TF-IDF cannot connect a question about resetting a device with a passage titled Power
Cycle Procedure, because the words do not overlap. An embedding model places both near
each other in vector space because it was trained on how language is actually used.

## Cosine Similarity
The standard way to compare two embeddings is cosine similarity: the dot product of
the two vectors divided by the product of their magnitudes. It measures direction and
ignores magnitude. Values near 1.0 mean very similar, values near 0 mean unrelated.

    def cosine_similarity(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

## Brute-Force Search Is Fine Here
To find the best matches, score the query against every stored vector and sort. This
is linear in the number of chunks. For a few hundred or a few thousand chunks on a
laptop this is imperceptible. Dedicated vector databases with approximate nearest
neighbour indexes only start to pay off at much larger scale.

## The Embedding Model Used In This Program
The alias qwen3-embedding-0.6b, loaded through Foundry Local. It is small enough to
download quickly and runs comfortably alongside a chat model on a laptop.

## Critical Rule
The same embedding model must be used for indexing documents and for embedding the
user's query. Vectors from two different models are not comparable, and mixing them
produces silently meaningless similarity scores rather than an error.
